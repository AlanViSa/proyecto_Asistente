#!/bin/bash

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para imprimir mensajes
print_message() {
    echo -e "${2}${1}${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_message "Error: No se encontró docker-compose.yml. Por favor, ejecuta este script desde el directorio raíz del proyecto." "$RED"
    exit 1
fi

print_message "Configurando sistema de copias de seguridad..." "$YELLOW"

# 1. Crear directorio para copias de seguridad
BACKUP_DIR="/var/backups/salon-assistant"
sudo mkdir -p $BACKUP_DIR
sudo chown -R $USER:$USER $BACKUP_DIR

# 2. Crear script de backup
cat > $BACKUP_DIR/backup.sh << 'EOL'
#!/bin/bash

# Configuración
BACKUP_DIR="/var/backups/salon-assistant"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="salon_assistant_$TIMESTAMP"
RETENTION_DAYS=7

# Crear directorio para este backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup de la base de datos
print_message "Realizando backup de la base de datos..." "$YELLOW"
docker-compose exec -T db pg_dump -U postgres salon_assistant > "$BACKUP_DIR/$BACKUP_NAME/database.sql"

# Backup de archivos de configuración
print_message "Realizando backup de archivos de configuración..." "$YELLOW"
cp .env.production "$BACKUP_DIR/$BACKUP_NAME/"
cp .env.credentials "$BACKUP_DIR/$BACKUP_NAME/"
cp -r certs "$BACKUP_DIR/$BACKUP_NAME/"

# Comprimir backup
print_message "Comprimiendo backup..." "$YELLOW"
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$BACKUP_DIR/$BACKUP_NAME"

# Eliminar backups antiguos
print_message "Limpiando backups antiguos..." "$YELLOW"
find $BACKUP_DIR -name "salon_assistant_*.tar.gz" -mtime +$RETENTION_DAYS -delete

print_message "Backup completado: $BACKUP_NAME.tar.gz" "$GREEN"
EOL

# 3. Crear script de restauración
cat > $BACKUP_DIR/restore.sh << 'EOL'
#!/bin/bash

# Verificar argumentos
if [ "$#" -ne 1 ]; then
    print_message "Uso: $0 <archivo_backup.tar.gz>" "$RED"
    exit 1
fi

BACKUP_FILE=$1
BACKUP_DIR="/var/backups/salon-assistant"
TEMP_DIR=$(mktemp -d)

# Verificar que el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    print_message "Error: El archivo $BACKUP_FILE no existe" "$RED"
    exit 1
fi

# Extraer backup
print_message "Extrayendo backup..." "$YELLOW"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restaurar base de datos
print_message "Restaurando base de datos..." "$YELLOW"
docker-compose exec -T db psql -U postgres salon_assistant < "$TEMP_DIR/database.sql"

# Restaurar archivos de configuración
print_message "Restaurando archivos de configuración..." "$YELLOW"
cp "$TEMP_DIR/.env.production" .
cp "$TEMP_DIR/.env.credentials" .
cp -r "$TEMP_DIR/certs" .

# Limpiar
rm -rf "$TEMP_DIR"

print_message "Restauración completada" "$GREEN"
EOL

# 4. Configurar tarea cron para backups diarios
print_message "Configurando tarea cron para backups diarios..." "$YELLOW"
(crontab -l 2>/dev/null | grep -v "backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_DIR/backup.sh >> $BACKUP_DIR/backup.log 2>&1") | crontab -

# 5. Establecer permisos
chmod +x $BACKUP_DIR/backup.sh
chmod +x $BACKUP_DIR/restore.sh

print_message "\n¡Sistema de copias de seguridad configurado!" "$GREEN"
print_message "Los backups se realizarán automáticamente a las 2:00 AM todos los días" "$YELLOW"
print_message "Ubicación de los backups: $BACKUP_DIR" "$YELLOW"
print_message "Retención de backups: 7 días" "$YELLOW"
print_message "\nPara realizar un backup manual:" "$YELLOW"
print_message "  $BACKUP_DIR/backup.sh" "$YELLOW"
print_message "\nPara restaurar un backup:" "$YELLOW"
print_message "  $BACKUP_DIR/restore.sh <archivo_backup.tar.gz>" "$YELLOW"
EOL 