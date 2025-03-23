#!/bin/bash

# Configuración
BACKUP_DIR="/app/backups"
RETENTION_DAYS=7
LOG_FILE="/var/log/backup.log"
MIN_SPACE_MB=1000  # Espacio mínimo requerido en MB
MAX_BACKUP_SIZE_MB=5000  # Tamaño máximo de backup en MB
BACKUP_PREFIX="backup"
BACKUP_SUFFIX=".sql.gz"
TEMP_DIR="/tmp/backup_temp"

# Función para logging con manejo de errores
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $message" | tee -a "$LOG_FILE" || {
        echo "Error: No se pudo escribir en el archivo de log" >&2
        return 1
    }
    return 0
}

# Función para verificar variables de entorno
check_env_vars() {
    local required_vars=("POSTGRES_HOST" "POSTGRES_USER" "POSTGRES_DB" "POSTGRES_PASSWORD")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "Error: Variables de entorno faltantes: ${missing_vars[*]}"
        return 1
    fi
    
    return 0
}

# Función para verificar versión de PostgreSQL
check_postgres_version() {
    local version=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW server_version;")
    if [ $? -ne 0 ]; then
        log "Error: No se pudo obtener la versión de PostgreSQL"
        return 1
    fi
    
    log "Versión de PostgreSQL: $version"
    return 0
}

# Función para verificar espacio disponible
check_disk_space() {
    local required_space=$1
    local available_space=$(df -m "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    
    if [ "$available_space" -lt "$required_space" ]; then
        log "Error: Espacio insuficiente. Disponible: ${available_space}MB, Requerido: ${required_space}MB"
        return 1
    fi
    
    return 0
}

# Función para verificar directorio de backups
check_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creando directorio de backups..."
        mkdir -p "$BACKUP_DIR" || {
            log "Error: No se pudo crear el directorio de backups"
            return 1
        }
        chmod 755 "$BACKUP_DIR"
    fi
    
    if [ ! -w "$BACKUP_DIR" ]; then
        log "Error: No hay permisos de escritura en $BACKUP_DIR"
        return 1
    fi
    
    return 0
}

# Función para validar nombre de archivo
validate_backup_file() {
    local file=$1
    if [[ ! "$file" =~ ^${BACKUP_PREFIX}_[0-9]{8}_[0-9]{6}${BACKUP_SUFFIX}$ ]]; then
        log "Error: Nombre de archivo inválido"
        return 1
    fi
    return 0
}

# Función para verificar integridad del backup
verify_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log "Error: Archivo de backup no encontrado"
        return 1
    fi
    
    # Verificar que el archivo no esté corrupto
    if ! gzip -t "$backup_file"; then
        log "Error: El archivo de backup está corrupto"
        return 1
    fi
    
    # Verificar tamaño del backup
    local backup_size=$(stat -f%z "$backup_file")
    if [ "$backup_size" -gt $((MAX_BACKUP_SIZE_MB * 1024 * 1024)) ]; then
        log "Error: El backup excede el tamaño máximo permitido"
        return 1
    fi
    
    return 0
}

# Función para crear backup
create_backup() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_$timestamp${BACKUP_SUFFIX}"
    local temp_file="$TEMP_DIR/backup_$timestamp.sql"
    
    # Verificar requisitos
    if ! check_env_vars; then
        return 1
    fi
    
    if ! check_postgres_version; then
        return 1
    fi
    
    if ! check_disk_space "$MIN_SPACE_MB"; then
        return 1
    fi
    
    # Crear directorio temporal si no existe
    mkdir -p "$TEMP_DIR" || {
        log "Error: No se pudo crear el directorio temporal"
        return 1
    }
    
    log "Iniciando backup..."
    
    # Crear backup de la base de datos
    if ! PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$temp_file"; then
        log "Error al crear backup"
        rm -f "$temp_file"
        return 1
    fi
    
    # Comprimir backup
    if ! gzip -c "$temp_file" > "$backup_file"; then
        log "Error al comprimir backup"
        rm -f "$temp_file" "$backup_file"
        return 1
    fi
    
    # Verificar integridad del backup
    if ! verify_backup "$backup_file"; then
        rm -f "$backup_file"
        return 1
    fi
    
    # Limpiar archivo temporal
    rm -f "$temp_file"
    
    log "Backup creado exitosamente: $backup_file"
    return 0
}

# Función para restaurar backup
restore_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log "Error: Archivo de backup no encontrado"
        return 1
    fi
    
    if ! validate_backup_file "$(basename "$backup_file")"; then
        return 1
    fi
    
    if ! verify_backup "$backup_file"; then
        return 1
    fi
    
    log "Iniciando restauración desde $backup_file..."
    
    # Verificar conexión a la base de datos
    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
        log "Error: No se puede conectar a la base de datos"
        return 1
    fi
    
    # Crear directorio temporal si no existe
    mkdir -p "$TEMP_DIR" || {
        log "Error: No se pudo crear el directorio temporal"
        return 1
    }
    
    local temp_file="$TEMP_DIR/restore_$(date +%Y%m%d_%H%M%S).sql"
    
    # Descomprimir backup
    if ! gunzip -c "$backup_file" > "$temp_file"; then
        log "Error al descomprimir backup"
        rm -f "$temp_file"
        return 1
    fi
    
    # Restaurar backup
    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$temp_file"; then
        log "Error al restaurar backup"
        rm -f "$temp_file"
        return 1
    fi
    
    # Limpiar archivo temporal
    rm -f "$temp_file"
    
    log "Backup restaurado exitosamente"
    return 0
}

# Función para limpiar backups antiguos
cleanup_old_backups() {
    log "Limpiando backups antiguos..."
    
    # Verificar espacio disponible antes de limpiar
    if ! check_disk_space "$MIN_SPACE_MB"; then
        log "Advertencia: Espacio disponible bajo, procediendo con limpieza"
    fi
    
    # Eliminar backups antiguos
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*${BACKUP_SUFFIX}" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || {
        log "Error: No se pudieron eliminar algunos backups antiguos"
        return 1
    }
    
    log "Limpieza completada"
    return 0
}

# Función para listar backups
list_backups() {
    echo "Backups disponibles:"
    for backup in "$BACKUP_DIR"/${BACKUP_PREFIX}_*${BACKUP_SUFFIX}; do
        if [ -f "$backup" ]; then
            local size=$(stat -f%z "$backup")
            local date=$(stat -f%Sm "$backup")
            echo "- $(basename "$backup") ($(numfmt --to=iec $size)) - $date"
        fi
    done
}

# Verificar requisitos iniciales
if ! check_env_vars; then
    echo "Error: Variables de entorno no configuradas correctamente"
    exit 1
fi

if ! check_backup_dir; then
    echo "Error: No se pudo verificar/crear el directorio de backups"
    exit 1
fi

# Menú principal
while true; do
    echo
    echo "Gestión de Backups"
    echo "1. Crear backup"
    echo "2. Restaurar backup"
    echo "3. Listar backups"
    echo "4. Limpiar backups antiguos"
    echo "5. Verificar backup"
    echo "6. Salir"
    read -p "Seleccione una opción: " option

    case $option in
        1)
            create_backup
            ;;
        2)
            list_backups
            read -p "Ingrese el nombre del archivo de backup a restaurar: " backup_file
            if validate_backup_file "$backup_file"; then
                restore_backup "$BACKUP_DIR/$backup_file"
            fi
            ;;
        3)
            list_backups
            ;;
        4)
            cleanup_old_backups
            ;;
        5)
            list_backups
            read -p "Ingrese el nombre del archivo de backup a verificar: " backup_file
            if validate_backup_file "$backup_file"; then
                verify_backup "$BACKUP_DIR/$backup_file"
            fi
            ;;
        6)
            echo "Saliendo..."
            exit 0
            ;;
        *)
            echo "Opción inválida"
            ;;
    esac
done 