#!/bin/bash

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Verify that we are in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_message "Error: docker-compose.yml not found. Please run this script from the project root directory." "$RED"
    exit 1
fi

# print_message "Configuring backup system..." "$YELLOW"

# 1. Create directory for backups
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

# Create directory for this backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup de la base de datos
print_message "Realizando backup de la base de datos..." "$YELLOW"
docker-compose exec -T db pg_dump -U postgres salon_assistant > "$BACKUP_DIR/$BACKUP_NAME/database.sql"

# Backup de archivos de configuración
print_message "Realizando backup de archivos de configuración..." "$YELLOW"
cp .env.production "$BACKUP_DIR/$BACKUP_NAME/"
cp .env.credentials "$BACKUP_DIR/$BACKUP_NAME/"
cp -r certs "$BACKUP_DIR/$BACKUP_NAME/"

# Compress backup
print_message "Compressing backup..." "$YELLOW"
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$BACKUP_DIR/$BACKUP_NAME"

# Delete old backups
print_message "Cleaning up old backups..." "$YELLOW"
find $BACKUP_DIR -name "salon_assistant_*.tar.gz" -mtime +$RETENTION_DAYS -delete

print_message "Backup completado: $BACKUP_NAME.tar.gz" "$GREEN"
EOL

# 3. Create restore script
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

# Verify that the file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_message "Error: The file $BACKUP_FILE does not exist" "$RED"
    exit 1
fi

# Extract backup
print_message "Extracting backup..." "$YELLOW"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restore database
print_message "Restoring database..." "$YELLOW"
docker-compose exec -T db psql -U postgres salon_assistant < "$TEMP_DIR/database.sql"

# Restore configuration files
print_message "Restoring configuration files..." "$YELLOW"
cp "$TEMP_DIR/.env.production" .
cp "$TEMP_DIR/.env.credentials" .
cp -r "$TEMP_DIR/certs" .

# Clean up
rm -rf "$TEMP_DIR"

print_message "Restore completed" "$GREEN"
EOL

# 4. Configure cron job for daily backups
print_message "Configuring cron job for daily backups..." "$YELLOW"
(crontab -l 2>/dev/null | grep -v "backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_DIR/backup.sh >> $BACKUP_DIR/backup.log 2>&1") | crontab -

# 5. Set permissions
chmod +x $BACKUP_DIR/backup.sh
chmod +x $BACKUP_DIR/restore.sh

print_message "\n¡Sistema de copias de seguridad configurado!" "$GREEN"
print_message "Los backups se realizarán automáticamente a las 2:00 AM todos los días" "$YELLOW"
print_message "Ubicación de los backups: $BACKUP_DIR" "$YELLOW"
print_message "Retención de backups: 7 días" "$YELLOW"
print_message "\nTo perform a manual backup:" "$YELLOW"
print_message "  $BACKUP_DIR/backup.sh" "$YELLOW"
print_message "\nTo restore a backup:" "$YELLOW"
print_message "  $BACKUP_DIR/restore.sh <archivo_backup.tar.gz>" "$YELLOW"
EOL 