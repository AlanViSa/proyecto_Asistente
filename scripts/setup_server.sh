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

# Actualizar el sistema
print_message "Actualizando el sistema..." "$YELLOW"
sudo apt-get update && sudo apt-get upgrade -y

# Instalar Docker
print_message "Instalando Docker..." "$YELLOW"
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# Verificar instalación de Docker
if ! command -v docker &> /dev/null; then
    print_message "Error: Docker no se instaló correctamente." "$RED"
    exit 1
fi

# Instalar Docker Compose
print_message "Instalando Docker Compose..." "$YELLOW"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación de Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_message "Error: Docker Compose no se instaló correctamente." "$RED"
    exit 1
fi

# Configurar el firewall
print_message "Configurando el firewall..." "$YELLOW"
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Instalar Nginx
print_message "Instalando Nginx..." "$YELLOW"
sudo apt-get install -y nginx

# Verificar instalación de Nginx
if ! command -v nginx &> /dev/null; then
    print_message "Error: Nginx no se instaló correctamente." "$RED"
    exit 1
fi

# Reiniciar Nginx
sudo systemctl restart nginx

print_message "¡Configuración del servidor completada!" "$GREEN" 