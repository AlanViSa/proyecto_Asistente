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

# Verify that the .env.production file exists
if [ ! -f ".env.production" ]; then
    print_message "Error: .env.production not found. Please run generate_env.sh first." "$RED"
    exit 1
fi

print_message "Configuring system security..." "$YELLOW"

# 1. Configure firewall
print_message "\nConfiguring firewall rules..." "$YELLOW"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5432/tcp  # Allow PostgreSQL
sudo ufw allow 6379/tcp  # Allow Redis
sudo ufw enable

# 2. Configure resource limits
print_message "\nConfiguring resource limits..." "$YELLOW"
cat > /etc/security/limits.d/salon-assistant.conf << EOL
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOL

# 3. Configure kernel parameters
print_message "\nConfiguring kernel parameters..." "$YELLOW"
cat > /etc/sysctl.d/99-salon-assistant.conf << EOL
net.ipv4.tcp_max_syn_backlog = 65535
net.core.somaxconn = 65535
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.ip_local_port_range = 1024 65535
EOL

# 4. Configure SSL/TLS
print_message "\nConfiguring SSL/TLS..." "$YELLOW"
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/private.key -out certs/certificate.crt \
    -subj "/C=ES/ST=Madrid/L=Madrid/O=Salon Assistant/CN=localhost"

# 5. Configurar permisos de archivos
print_message "\nConfiguring file permissions..." "$YELLOW"
chmod 600 .env.production  # Restrict access to environment file
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

# 7. Restart services
print_message "\nRestarting services..." "$YELLOW"
sudo sysctl -p /etc/sysctl.d/99-salon-assistant.conf
sudo systemctl restart docker
sudo systemctl restart ufw

print_message "\nSecurity configuration completed!" "$GREEN"
print_message "IMPORTANT: Make sure to store the credentials and certificates in a safe place." "$RED"
print_message "Additional recommendations:" "$YELLOW"
print_message "1. Set up automatic backups" "$YELLOW"
print_message "2. Implement a security monitoring system" "$YELLOW"
print_message "3. Perform periodic security audits" "$YELLOW"
print_message "4. Keep the system and dependencies updated" "$YELLOW"