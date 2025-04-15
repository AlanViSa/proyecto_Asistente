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

# Update the system
print_message "Updating the system..." "$YELLOW"
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
print_message "Installing Docker..." "$YELLOW"
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# Verify Docker installation
if ! command -v docker &> /dev/null; then
    print_message "Error: Docker was not installed correctly." "$RED"
    exit 1
fi

# Install Docker Compose
print_message "Installing Docker Compose..." "$YELLOW"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify Docker Compose installation
if ! command -v docker-compose &> /dev/null; then
    print_message "Error: Docker Compose was not installed correctly." "$RED"
    exit 1
fi

# Configure the firewall
print_message "Configuring the firewall..." "$YELLOW"
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Install Nginx
print_message "Installing Nginx..." "$YELLOW"
sudo apt-get install -y nginx

# Verify Nginx installation
if ! command -v nginx &> /dev/null; then
    print_message "Error: Nginx was not installed correctly." "$RED"
    exit 1
fi

# Restart Nginx
sudo systemctl restart nginx

print_message "Server configuration completed!" "$GREEN"