#!/bin/bash

# Configuración
SECRETS_DIR="secrets"
LOG_FILE="/var/log/secrets_manager.log"
MIN_PASSWORD_LENGTH=12
MAX_FILE_NAME_LENGTH=64
MAX_SECRET_LENGTH=4096
TEMP_DIR="/tmp/secrets_temp"
ROTATION_INTERVAL_DAYS=90

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

# Función para verificar directorio de secretos
check_secrets_dir() {
    if [ ! -d "$SECRETS_DIR" ]; then
        log "Creando directorio de secretos..."
        mkdir -p "$SECRETS_DIR" || {
            log "Error: No se pudo crear el directorio de secretos"
            return 1
        }
        chmod 700 "$SECRETS_DIR"
    fi
    
    if [ ! -w "$SECRETS_DIR" ]; then
        log "Error: No hay permisos de escritura en $SECRETS_DIR"
        return 1
    fi
    
    if [ ! -r "$SECRETS_DIR" ]; then
        log "Error: No hay permisos de lectura en $SECRETS_DIR"
        return 1
    fi
    
    return 0
}

# Función para verificar directorio temporal
check_temp_dir() {
    if [ ! -d "$TEMP_DIR" ]; then
        mkdir -p "$TEMP_DIR" || {
            log "Error: No se pudo crear el directorio temporal"
            return 1
        }
        chmod 700 "$TEMP_DIR"
    fi
    
    if [ ! -w "$TEMP_DIR" ]; then
        log "Error: No hay permisos de escritura en $TEMP_DIR"
        return 1
    fi
    
    return 0
}

# Función para validar nombre de archivo
validate_file_name() {
    local name=$1
    if [[ ! "$name" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
        log "Error: El nombre solo puede contener letras, números, puntos, guiones y guiones bajos"
        return 1
    fi
    if [ ${#name} -gt $MAX_FILE_NAME_LENGTH ]; then
        log "Error: El nombre es demasiado largo (máximo $MAX_FILE_NAME_LENGTH caracteres)"
        return 1
    fi
    return 0
}

# Función para validar valor del secreto
validate_secret_value() {
    local value=$1
    if [ ${#value} -gt $MAX_SECRET_LENGTH ]; then
        log "Error: El valor es demasiado largo (máximo $MAX_SECRET_LENGTH caracteres)"
        return 1
    fi
    if [[ "$value" =~ [^[:print:]] ]]; then
        log "Error: El valor contiene caracteres no imprimibles"
        return 1
    fi
    return 0
}

# Función para validar contraseña
validate_password() {
    local password=$1
    if [ ${#password} -lt $MIN_PASSWORD_LENGTH ]; then
        log "Error: La contraseña debe tener al menos $MIN_PASSWORD_LENGTH caracteres"
        return 1
    fi
    if ! [[ "$password" =~ [A-Z] ]]; then
        log "Error: La contraseña debe contener al menos una mayúscula"
        return 1
    fi
    if ! [[ "$password" =~ [a-z] ]]; then
        log "Error: La contraseña debe contener al menos una minúscula"
        return 1
    fi
    if ! [[ "$password" =~ [0-9] ]]; then
        log "Error: La contraseña debe contener al menos un número"
        return 1
    fi
    if ! [[ "$password" =~ [^A-Za-z0-9] ]]; then
        log "Error: La contraseña debe contener al menos un carácter especial"
        return 1
    fi
    return 0
}

# Función para generar una clave secreta segura
generate_secret() {
    if ! openssl rand -base64 32 > "$TEMP_DIR/secret.tmp"; then
        log "Error: No se pudo generar la clave secreta"
        return 1
    fi
    
    cat "$TEMP_DIR/secret.tmp"
    rm -f "$TEMP_DIR/secret.tmp"
    return 0
}

# Función para encriptar un archivo
encrypt_file() {
    local file=$1
    local password=$2
    
    if [ ! -f "$file" ]; then
        log "Error: Archivo no encontrado"
        return 1
    fi
    
    if ! openssl enc -aes-256-cbc -salt -pbkdf2 -iter 10000 -in "$file" -out "$file.enc" -k "$password"; then
        log "Error: No se pudo encriptar el archivo"
        return 1
    fi
    
    if ! rm "$file"; then
        log "Error: No se pudo eliminar el archivo original"
        rm -f "$file.enc"
        return 1
    fi
    
    return 0
}

# Función para desencriptar un archivo
decrypt_file() {
    local file=$1
    local password=$2
    
    if [ ! -f "$file" ]; then
        log "Error: Archivo encriptado no encontrado"
        return 1
    fi
    
    if ! openssl enc -aes-256-cbc -d -pbkdf2 -iter 10000 -in "$file" -out "${file%.enc}" -k "$password"; then
        log "Error: No se pudo desencriptar el archivo"
        return 1
    fi
    
    return 0
}

# Función para crear un nuevo secreto
create_secret() {
    local name=$1
    local value=$2
    
    if ! validate_file_name "$name"; then
        return 1
    fi
    
    if ! validate_secret_value "$value"; then
        return 1
    fi
    
    local secret_file="$SECRETS_DIR/$name"
    echo "$value" > "$secret_file" || {
        log "Error: No se pudo crear el archivo del secreto"
        return 1
    }
    
    read -s -p "Ingrese una contraseña para encriptar el secreto: " password
    echo
    
    if ! validate_password "$password"; then
        rm -f "$secret_file"
        return 1
    fi
    
    if ! encrypt_file "$secret_file" "$password"; then
        return 1
    fi
    
    log "Secreto '$name' creado y encriptado"
    return 0
}

# Función para leer un secreto
read_secret() {
    local name=$1
    
    if ! validate_file_name "$name"; then
        return 1
    fi
    
    local secret_file="$SECRETS_DIR/$name.enc"
    if [ ! -f "$secret_file" ]; then
        log "Error: Secreto '$name' no encontrado"
        return 1
    fi
    
    read -s -p "Ingrese la contraseña para desencriptar el secreto: " password
    echo
    
    if ! decrypt_file "$secret_file" "$password"; then
        return 1
    fi
    
    cat "${secret_file%.enc}"
    rm -f "${secret_file%.enc}"
    return 0
}

# Función para listar secretos
list_secrets() {
    echo "Secretos disponibles:"
    for file in "$SECRETS_DIR"/*.enc; do
        if [ -f "$file" ]; then
            echo "- ${file%.enc}"
        fi
    done
}

# Función para rotar un secreto
rotate_secret() {
    local name=$1
    
    if ! validate_file_name "$name"; then
        return 1
    fi
    
    local secret_file="$SECRETS_DIR/$name.enc"
    if [ ! -f "$secret_file" ]; then
        log "Error: Secreto '$name' no encontrado"
        return 1
    fi
    
    read -s -p "Ingrese la contraseña actual: " current_password
    echo
    
    if ! decrypt_file "$secret_file" "$current_password"; then
        return 1
    fi
    
    local temp_file="${secret_file%.enc}"
    local new_value=$(generate_secret)
    
    if [ $? -eq 0 ]; then
        echo "$new_value" > "$temp_file"
        read -s -p "Ingrese la nueva contraseña: " new_password
        echo
        
        if ! validate_password "$new_password"; then
            rm -f "$temp_file"
            return 1
        fi
        
        if ! encrypt_file "$temp_file" "$new_password"; then
            return 1
        fi
        
        log "Secreto '$name' rotado exitosamente"
        return 0
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Función para verificar secretos que necesitan rotación
check_rotation() {
    local current_time=$(date +%s)
    
    for file in "$SECRETS_DIR"/*.enc; do
        if [ -f "$file" ]; then
            local file_time=$(stat -f%m "$file")
            local days_old=$(( (current_time - file_time) / 86400 ))
            
            if [ $days_old -ge $ROTATION_INTERVAL_DAYS ]; then
                log "Advertencia: El secreto '${file%.enc}' necesita rotación (${days_old} días)"
            fi
        fi
    done
}

# Verificar requisitos iniciales
if ! check_secrets_dir; then
    echo "Error: No se pudo verificar/crear el directorio de secretos"
    exit 1
fi

if ! check_temp_dir; then
    echo "Error: No se pudo verificar/crear el directorio temporal"
    exit 1
fi

# Verificar secretos que necesitan rotación
check_rotation

# Menú principal
while true; do
    echo
    echo "Gestión de Secretos"
    echo "1. Crear nuevo secreto"
    echo "2. Leer secreto"
    echo "3. Listar secretos"
    echo "4. Rotar secreto"
    echo "5. Verificar rotación"
    echo "6. Salir"
    read -p "Seleccione una opción: " option

    case $option in
        1)
            read -p "Nombre del secreto: " name
            read -s -p "Valor del secreto: " value
            echo
            create_secret "$name" "$value"
            ;;
        2)
            read -p "Nombre del secreto: " name
            read_secret "$name"
            ;;
        3)
            list_secrets
            ;;
        4)
            read -p "Nombre del secreto a rotar: " name
            rotate_secret "$name"
            ;;
        5)
            check_rotation
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