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

# Verificar que el archivo .env.production existe
if [ ! -f ".env.production" ]; then
    print_message "Error: No se encontró .env.production. Por favor, ejecuta primero generate_env.sh" "$RED"
    exit 1
fi

print_message "Configurando seguridad del sistema..." "$YELLOW"

# 1. Configurar firewall
print_message "\nConfigurando reglas de firewall..." "$YELLOW"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp
sudo ufw enable

# 2. Configurar límites de recursos
print_message "\nConfigurando límites de recursos..." "$YELLOW"
cat > /etc/security/limits.d/salon-assistant.conf << EOL
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOL

# 3. Configurar parámetros del kernel
print_message "\nConfigurando parámetros del kernel..." "$YELLOW"
cat > /etc/sysctl.d/99-salon-assistant.conf << EOL
net.ipv4.tcp_max_syn_backlog = 65535
net.core.somaxconn = 65535
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.ip_local_port_range = 1024 65535
EOL

# 4. Configurar SSL/TLS
print_message "\nConfigurando SSL/TLS..." "$YELLOW"
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/private.key -out certs/certificate.crt \
    -subj "/C=ES/ST=Madrid/L=Madrid/O=Salon Assistant/CN=localhost"

# 5. Configurar permisos de archivos
print_message "\nConfigurando permisos de archivos..." "$YELLOW"
chmod 600 .env.production
chmod 600 .env.credentials
chmod 600 certs/private.key
chmod 644 certs/certificate.crt

# 6. Configurar Docker
print_message "\nConfigurando seguridad de Docker..." "$YELLOW"
cat > /etc/docker/daemon.json << EOL
{
  "userns-remap": "default",
  "no-new-privileges": true,
  "icc": false,
  "userland-proxy": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOL

# 7. Reiniciar servicios
print_message "\nReiniciando servicios..." "$YELLOW"
sudo sysctl -p /etc/sysctl.d/99-salon-assistant.conf
sudo systemctl restart docker
sudo systemctl restart ufw

print_message "\n¡Configuración de seguridad completada!" "$GREEN"
print_message "IMPORTANTE: Asegúrate de guardar las credenciales y certificados en un lugar seguro." "$RED"
print_message "Recomendaciones adicionales:" "$YELLOW"
print_message "1. Configura copias de seguridad automáticas" "$YELLOW"
print_message "2. Implementa un sistema de monitoreo de seguridad" "$YELLOW"
print_message "3. Realiza auditorías de seguridad periódicas" "$YELLOW"
print_message "4. Mantén el sistema y las dependencias actualizadas" "$YELLOW" 