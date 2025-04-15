#!/bin/bash

# Configuration
BACKUP_DIR="/app/backups"
RETENTION_DAYS=7
LOG_FILE="/var/log/backup.log"
MIN_SPACE_MB=1000  # Minimum required space in MB
MAX_BACKUP_SIZE_MB=5000  # Maximum backup size in MB
BACKUP_PREFIX="backup"
BACKUP_SUFFIX=".sql.gz"
TEMP_DIR="/tmp/backup_temp"

# Function for logging with error handling
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $message" | tee -a "$LOG_FILE" || {
        echo "Error: Could not write to the log file" >&2
        return 1
    }
    return 0
}

# Función para verificar variables de entorno
check_env_vars() {
    local required_vars=("DATABASE_URL")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "Error: Missing environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    return 0
}

# Function to check available disk space
check_disk_space() {
    local required_space=$1
    local available_space=$(df -m "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    
    if [ "$available_space" -lt "$required_space" ]; then
        log "Error: Insufficient space. Available: ${available_space}MB, Required: ${required_space}MB"
        return 1
    fi
    
    return 0
}

# Function to check backup directory
check_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
    fi
    return 0
}

# Función para validar nombre de archivo
validate_backup_file() {
    local file=$1
    if [[ ! "$file" =~ ^${BACKUP_PREFIX}_[0-9]{8}_[0-9]{6}${BACKUP_SUFFIX}$ ]]; then
        log "Error: Invalid file name"
        return 1
    fi
    return 0
}

# Función para verificar integridad del backup
verify_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log "Error: Backup file not found"
        return 1
    fi
    
    # Verify that the file is not corrupt
    if ! gunzip -t "$backup_file"; then
        return 1
    fi
    
    # Verificar tamaño del backup
    local backup_size=$(stat -f%z "$backup_file")
    if [ "$backup_size" -gt $((MAX_BACKUP_SIZE_MB * 1024 * 1024)) ]; then
        log "Error: El backup excede el tamaño máximo permitido"
        # log "Error: Backup exceeds the maximum allowed size"
        return 1
    fi
    
    return 0
}

create_backup() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_$timestamp${BACKUP_SUFFIX}"
    local temp_file="$TEMP_DIR/backup_$timestamp.sql"
    
    # Verificar requisitos
    if ! check_env_vars; then
        return 1
    fi
    
    if ! check_disk_space "$MIN_SPACE_MB"; then
        return 1
    fi
    
    log "Starting backup..."
    
    if ! pg_dump "$DATABASE_URL" > "$temp_file"; then
        log "Error creating backup"
        rm -f "$temp_file"
        return 1
    fi
    
    if ! gzip "$temp_file" > "$backup_file"; then
        log "Error compressing backup"
        rm -f "$temp_file"
        return 1
    fi
    
    if ! verify_backup "$backup_file"; then
        rm -f "$backup_file"
        log "Error: The generated backup is corrupted."
        return 1
    fi
    
    rm -f "$temp_file"
    
    log "Backup created successfully: $backup_file"
    return 0
}

restore_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log "Error: Backup file not found: $backup_file"
        return 1
    fi
    
    if ! validate_backup_file "$(basename "$backup_file")"; then
        return 1
    fi

    log "Starting restoration from $backup_file..."

    local temp_file="$TEMP_DIR/restore_$(date +%Y%m%d_%H%M%S).sql"
    
    if ! gunzip "$backup_file" > "$temp_file"; then
        log "Error decompressing backup"
        rm -f "$temp_file"
        return 1
    fi
    
    if ! psql "$DATABASE_URL" < "$temp_file"; then
        log "Error restoring backup"
        rm -f "$temp_file"
        return 1
    fi
    
    rm -f "$temp_file"
    
    log "Backup restored successfully"
    return 0
}

cleanup_old_backups() {
    log "Limpiando backups antiguos..."
    
    # Verificar espacio disponible antes de limpiar
    if ! check_disk_space "$MIN_SPACE_MB"; then
        log "Advertencia: Espacio disponible bajo, procediendo con limpieza"
    fi
    
    # Eliminar backups antiguos
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*${BACKUP_SUFFIX}" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || {
        log "Error: Could not delete some old backups"
        return 1
    }
    
    log "Cleanup completed"
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
    echo "Error: Environment variables not configured correctly"
    exit 1
fi

if ! check_backup_dir; then
    echo "Error: No se pudo verificar/crear el directorio de backups"
    exit 1
fi

# Menú principal
while true; do
    echo ""
    echo "Backup Management"
    echo "1. Create backup"
    echo "2. Restore backup"
    echo "3. List backups"
    echo "4. Clean old backups"
    echo "5. Verify backup"
    echo "6. Exit"
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
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
done 