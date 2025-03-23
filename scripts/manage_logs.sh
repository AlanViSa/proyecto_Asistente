#!/bin/bash

# Configuración
LOG_DIR="/app/logs"
MAX_LOG_SIZE="100M"
MAX_LOG_FILES=5
LOG_ROTATE_CONF="/etc/logrotate.d/salon-assistant"
LOG_FILE="/var/log/log_manager.log"
LOG_ANALYSIS_DIR="/app/log_analysis"
MAX_ANALYSIS_FILES=10
DATE_FORMAT="%Y-%m-%d %H:%M:%S"

# Función para logging con manejo de errores
log() {
    local message="$1"
    local timestamp=$(date +"$DATE_FORMAT")
    echo "$timestamp - $message" | tee -a "$LOG_FILE" || {
        echo "Error: No se pudo escribir en el archivo de log" >&2
        return 1
    }
    return 0
}

# Función para verificar permisos
check_permissions() {
    local dir="$1"
    local required_perm="$2"
    
    if [ ! -d "$dir" ]; then
        log "Error: El directorio $dir no existe"
        return 1
    fi
    
    if [ ! -w "$dir" ]; then
        log "Error: No hay permisos de escritura en $dir"
        return 1
    fi
    
    if [ ! -r "$dir" ]; then
        log "Error: No hay permisos de lectura en $dir"
        return 1
    fi
    
    return 0
}

# Función para verificar directorio de logs
check_log_dir() {
    if [ ! -d "$LOG_DIR" ]; then
        log "Creando directorio de logs..."
        mkdir -p "$LOG_DIR" || {
            log "Error: No se pudo crear el directorio de logs"
            return 1
        }
        chmod 755 "$LOG_DIR"
    fi
    
    if ! check_permissions "$LOG_DIR" "755"; then
        return 1
    fi
    
    return 0
}

# Función para verificar directorio de análisis
check_analysis_dir() {
    if [ ! -d "$LOG_ANALYSIS_DIR" ]; then
        log "Creando directorio de análisis..."
        mkdir -p "$LOG_ANALYSIS_DIR" || {
            log "Error: No se pudo crear el directorio de análisis"
            return 1
        }
        chmod 755 "$LOG_ANALYSIS_DIR"
    fi
    
    if ! check_permissions "$LOG_ANALYSIS_DIR" "755"; then
        return 1
    fi
    
    return 0
}

# Función para configurar logrotate
setup_logrotate() {
    log "Configurando logrotate..."
    
    # Verificar permisos de sudo
    if ! sudo -v; then
        log "Error: Se requieren permisos de sudo para configurar logrotate"
        return 1
    fi
    
    # Crear configuración temporal
    local temp_conf="/tmp/salon-assistant-logrotate"
    cat > "$temp_conf" << EOF
$LOG_DIR/*.log {
    daily
    rotate $MAX_LOG_FILES
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    size $MAX_LOG_SIZE
    dateext
    dateformat -%Y%m%d
}
EOF
    
    # Mover configuración con sudo
    if sudo mv "$temp_conf" "$LOG_ROTATE_CONF"; then
        sudo chmod 644 "$LOG_ROTATE_CONF"
        log "Configuración de logrotate completada"
        return 0
    else
        log "Error: No se pudo mover la configuración de logrotate"
        rm -f "$temp_conf"
        return 1
    fi
}

# Función para limpiar logs antiguos
cleanup_old_logs() {
    log "Limpiando logs antiguos..."
    
    # Verificar espacio disponible
    local available_space=$(df -m "$LOG_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 100 ]; then
        log "Advertencia: Espacio disponible bajo ($available_space MB)"
    fi
    
    # Eliminar logs comprimidos más antiguos que MAX_LOG_FILES
    find "$LOG_DIR" -name "*.log.*.gz" -type f -mtime +$MAX_LOG_FILES -delete 2>/dev/null || {
        log "Error: No se pudieron eliminar algunos logs antiguos"
        return 1
    }
    
    # Eliminar logs vacíos
    find "$LOG_DIR" -name "*.log" -type f -empty -delete 2>/dev/null || {
        log "Error: No se pudieron eliminar algunos logs vacíos"
        return 1
    }
    
    # Limpiar archivos de análisis antiguos
    if [ -d "$LOG_ANALYSIS_DIR" ]; then
        find "$LOG_ANALYSIS_DIR" -name "analysis_*.txt" -type f -mtime +$MAX_ANALYSIS_FILES -delete 2>/dev/null || {
            log "Error: No se pudieron eliminar algunos archivos de análisis antiguos"
            return 1
        }
    fi
    
    log "Limpieza completada"
    return 0
}

# Función para validar nombre de archivo
validate_log_file() {
    local file=$1
    if [[ ! "$file" =~ ^[a-zA-Z0-9_.-]+\.log$ ]]; then
        log "Error: Nombre de archivo inválido"
        return 1
    fi
    return 0
}

# Función para validar formato de fecha
validate_date_format() {
    local date_str=$1
    if ! date -d "$date_str" >/dev/null 2>&1; then
        log "Error: Formato de fecha inválido"
        return 1
    fi
    return 0
}

# Función para analizar logs
analyze_logs() {
    local log_file=$1
    local analysis_file="$LOG_ANALYSIS_DIR/analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    if [ ! -f "$log_file" ]; then
        log "Error: Archivo de log no encontrado"
        return 1
    fi
    
    if [ ! -r "$log_file" ]; then
        log "Error: No hay permisos de lectura en el archivo de log"
        return 1
    fi
    
    log "Iniciando análisis de $log_file..."
    
    {
        echo "Análisis de $log_file"
        echo "Fecha: $(date)"
        echo "----------------------------------------"
        
        # Contar errores
        echo "Errores encontrados:"
        grep -i "error" "$log_file" | wc -l || true
        
        # Contar warnings
        echo "Warnings encontrados:"
        grep -i "warning" "$log_file" | wc -l || true
        
        # Top 10 IPs
        echo "Top 10 IPs:"
        grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" "$log_file" | sort | uniq -c | sort -nr | head -n 10 || true
        
        # Top 10 endpoints
        echo "Top 10 endpoints:"
        grep -oE "/api/v1/[a-zA-Z0-9/]+" "$log_file" | sort | uniq -c | sort -nr | head -n 10 || true
        
        # Análisis de tiempos de respuesta
        echo "Análisis de tiempos de respuesta:"
        grep -oE "response_time=[0-9.]+" "$log_file" | cut -d= -f2 | sort -n | awk '
            NR==1 {min=$1}
            NR==NR {max=$1}
            {sum+=$1}
            END {printf "Min: %.3f\nMax: %.3f\nPromedio: %.3f\n", min, max, sum/NR}'
        
        # Análisis de códigos de estado HTTP
        echo "Códigos de estado HTTP:"
        grep -oE "status_code=[0-9]+" "$log_file" | cut -d= -f2 | sort | uniq -c | sort -nr || true
        
    } > "$analysis_file"
    
    if [ $? -eq 0 ]; then
        log "Análisis guardado en $analysis_file"
        cat "$analysis_file"
        return 0
    else
        log "Error: No se pudo completar el análisis"
        rm -f "$analysis_file"
        return 1
    fi
}

# Función para monitorear logs en tiempo real
monitor_logs() {
    local log_file=$1
    local filter=$2
    
    if [ ! -f "$log_file" ]; then
        log "Error: Archivo de log no encontrado"
        return 1
    fi
    
    if [ ! -r "$log_file" ]; then
        log "Error: No hay permisos de lectura en el archivo de log"
        return 1
    fi
    
    echo "Monitoreando $log_file (Ctrl+C para detener)..."
    if [ -n "$filter" ]; then
        tail -f "$log_file" | grep "$filter"
    else
        tail -f "$log_file"
    fi
}

# Función para buscar en logs
search_logs() {
    local log_file=$1
    local pattern=$2
    
    if [ ! -f "$log_file" ]; then
        log "Error: Archivo de log no encontrado"
        return 1
    fi
    
    if [ ! -r "$log_file" ]; then
        log "Error: No hay permisos de lectura en el archivo de log"
        return 1
    fi
    
    echo "Buscando '$pattern' en $log_file..."
    grep -i "$pattern" "$log_file" || true
}

# Verificar requisitos iniciales
if ! check_log_dir; then
    echo "Error: No se pudo verificar/crear el directorio de logs"
    exit 1
fi

if ! check_analysis_dir; then
    echo "Error: No se pudo verificar/crear el directorio de análisis"
    exit 1
fi

# Menú principal
while true; do
    echo
    echo "Gestión de Logs"
    echo "1. Configurar logrotate"
    echo "2. Limpiar logs antiguos"
    echo "3. Analizar logs"
    echo "4. Monitorear logs en tiempo real"
    echo "5. Buscar en logs"
    echo "6. Salir"
    read -p "Seleccione una opción: " option

    case $option in
        1)
            setup_logrotate
            ;;
        2)
            cleanup_old_logs
            ;;
        3)
            echo "Logs disponibles:"
            ls -lh "$LOG_DIR"/*.log 2>/dev/null || true
            read -p "Ingrese el nombre del archivo de log a analizar: " log_file
            if validate_log_file "$log_file"; then
                analyze_logs "$LOG_DIR/$log_file"
            fi
            ;;
        4)
            echo "Logs disponibles:"
            ls -lh "$LOG_DIR"/*.log 2>/dev/null || true
            read -p "Ingrese el nombre del archivo de log a monitorear: " log_file
            if validate_log_file "$log_file"; then
                read -p "Ingrese un filtro (opcional): " filter
                monitor_logs "$LOG_DIR/$log_file" "$filter"
            fi
            ;;
        5)
            echo "Logs disponibles:"
            ls -lh "$LOG_DIR"/*.log 2>/dev/null || true
            read -p "Ingrese el nombre del archivo de log a buscar: " log_file
            if validate_log_file "$log_file"; then
                read -p "Ingrese el patrón a buscar: " pattern
                search_logs "$LOG_DIR/$log_file" "$pattern"
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