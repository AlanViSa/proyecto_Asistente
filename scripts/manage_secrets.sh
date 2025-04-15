#!/bin/bash

# Configuration
SECRETS_DIR="secrets"
LOG_FILE="/var/log/secrets_manager.log"
MIN_PASSWORD_LENGTH=12
MAX_FILE_NAME_LENGTH=64
MAX_SECRET_LENGTH=4096
TEMP_DIR="/tmp/secrets_temp"
ROTATION_INTERVAL_DAYS=90  # Days before a secret is considered for rotation

# Function for logging with error handling
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $message" | tee -a "$LOG_FILE" || {
        echo "Error: Could not write to log file" >&2
        return 1
    }
    return 0
}

# Function to check the secrets directory
check_secrets_dir() {
    if [ ! -d "$SECRETS_DIR" ]; then
        log "Creating secrets directory..."
        mkdir -p "$SECRETS_DIR" || {
            log "Error: No se pudo crear el directorio de secretos"
            return 1
        }
        chmod 700 "$SECRETS_DIR"
    fi
    
    if [ ! -w "$SECRETS_DIR" ]; then
        log "Error: No write permissions in $SECRETS_DIR"
        return 1
    fi
    
    if [ ! -r "$SECRETS_DIR" ]; then
        log "Error: No hay permisos de lectura en $SECRETS_DIR"
        return 1
    fi
    
    return 0
}

# Function to check the temporary directory
check_temp_dir() {
    if [ ! -d "$TEMP_DIR" ]; then
        mkdir -p "$TEMP_DIR" || {  # Create temporary directory if it does not exist
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

# Function to validate file name
validate_file_name() {
    local name=$1
    if [[ ! "$name" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
        log "Error: The name can only contain letters, numbers, periods, dashes, and underscores"
        return 1
    fi
    if [ ${#name} -gt $MAX_FILE_NAME_LENGTH ]; then
        log "Error: The name is too long (maximum $MAX_FILE_NAME_LENGTH characters)"
        return 1
    fi
    return 0
}

# Function to validate secret value
validate_secret_value() {
    local value=$1
    if [ ${#value} -gt $MAX_SECRET_LENGTH ]; then
        log "Error: The value is too long (maximum $MAX_SECRET_LENGTH characters)"
        return 1
    fi
    if [[ "$value" =~ [^[:print:]] ]]; then
        log "Error: The value contains non-printable characters"
        return 1
    fi
    return 0
}

# Función para validar contraseña
validate_password() {
    local password=$1
    if [ ${#password} -lt $MIN_PASSWORD_LENGTH ]; then
        log "Error: The password must be at least $MIN_PASSWORD_LENGTH characters long"
        return 1
    fi
    if ! [[ "$password" =~ [A-Z] ]]; then
        log "Error: The password must contain at least one uppercase letter"
        return 1
    fi
    if ! [[ "$password" =~ [a-z] ]]; then
        log "Error: The password must contain at least one lowercase letter"
        return 1
    fi
    if ! [[ "$password" =~ [0-9] ]]; then
        log "Error: The password must contain at least one number"
        return 1
    fi
    if ! [[ "$password" =~ [^A-Za-z0-9] ]]; then
        log "Error: The password must contain at least one special character"
        return 1
    fi
    return 0
}

# Function to generate a secure secret key
generate_secret() {
    if ! openssl rand -base64 32 > "$TEMP_DIR/secret.tmp"; then
        log "Error: Could not generate the secret key"
        return 1
    fi
    # Output the generated secret and then remove the temporary file
    
    cat "$TEMP_DIR/secret.tmp"
    rm -f "$TEMP_DIR/secret.tmp"
    return 0
}

# Función para encriptar un archivo
encrypt_file() {  # Encrypts a file using AES-256-CBC with a password
    local file=$1
    local password=$2
    
    if [ ! -f "$file" ]; then
        log "Error: Archivo no encontrado"
        return 1
    fi
    
    # Encrypt the file and save it with a .enc extension
    if ! openssl enc -aes-256-cbc -salt -pbkdf2 -iter 10000 -in "$file" -out "$file.enc" -k "$password"; then
        log "Error: Could not encrypt the file"
        return 1
    fi
    
    if ! rm "$file"; then  # Remove the original unencrypted file
        log "Error: No se pudo eliminar el archivo original"
        rm -f "$file.enc"
        return 1
    fi
    
    return 0
}

# Function to decrypt a file
decrypt_file() {
    local file=$1
    local password=$2
    
    if [ ! -f "$file" ]; then
        log "Error: Archivo encriptado no encontrado"
        return 1
    fi
    
    # Decrypt the file and remove the .enc extension
    if ! openssl enc -aes-256-cbc -d -pbkdf2 -iter 10000 -in "$file" -out "${file%.enc}" -k "$password"; then
        log "Error: Could not decrypt the file"
        return 1
    fi
    
    return 0  # Decrypted file is named without .enc extension
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
        log "Error: Could not create the secret file"
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
    
    log "Secret '$name' created and encrypted"
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
    # Prompt for password and decrypt the file
    if ! decrypt_file "$secret_file" "$password"; then
        return 1
    fi
    
    cat "${secret_file%.enc}"
    rm -f "${secret_file%.enc}"
    return 0
}

# Función para listar secretos
list_secrets() {  # Lists all available secrets in the secrets directory
    echo "Secretos disponibles:"
    for file in "$SECRETS_DIR"/*.enc; do
        if [ -f "$file" ]; then
            echo "- ${file%.enc}"
        fi
    done
}

# Función para rotar un secreto
rotate_secret() {  # Rotates a secret by decrypting, generating a new value, and re-encrypting
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
    # Decrypt the file with the current password
    if ! decrypt_file "$secret_file" "$current_password"; then
        return 1
    fi  # Decrypt the file with the current password
    
    local temp_file="${secret_file%.enc}"
    local new_value=$(generate_secret)
    
    if [ $? -eq 0 ]; then
        echo "$new_value" > "$temp_file"
        read -s -p "Ingrese la nueva contraseña: " new_password
        echo
        
        if ! validate_password "$new_password"; then  # Validate the new password
            rm -f "$temp_file"
            return 1
        fi
        
        if ! encrypt_file "$temp_file" "$new_password"; then  # Encrypt the file with the new password
            return 1
        fi  # Encrypt the file with the new password
        
        log "Secreto '$name' rotado exitosamente"
        return 0
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Función para verificar secretos que necesitan rotación
check_rotation() {  # Checks which secrets need rotation based on their age
    local current_time=$(date +%s)
    
    for file in "$SECRETS_DIR"/*.enc; do
        if [ -f "$file" ]; then
            local file_time=$(stat -f%m "$file")
            local days_old=$(( (current_time - file_time) / 86400 ))
            
            if [ $days_old -ge $ROTATION_INTERVAL_DAYS ]; then
                log "Warning: Secret '${file%.enc}' needs rotation (${days_old} days old)"
            fi
        fi
    done
}

# Verificar requisitos iniciales
if ! check_secrets_dir; then  # Check if the secrets directory exists and is writable
    echo "Error: Could not verify/create the secrets directory"
    exit 1
fi

if ! check_temp_dir; then  # Check if the temporary directory exists and is writable
    echo "Error: Could not verify/create the temporary directory"
    exit 1
fi  # Check if the temporary directory exists and is writable

# Verificar secretos que necesitan rotación
check_rotation

# Menú principal
while true; do
    echo
    echo "Gestión de Secretos"
    echo "1. Create new secret"
    echo "2. Read secret"
    echo "3. List secrets"
    echo "4. Rotate secret"
    echo "5. Check rotation"
    echo "6. Exit"
    read -p "Select an option: " option
    # Main menu loop

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
            echo "Invalid option"
            ;;
    esac
done 