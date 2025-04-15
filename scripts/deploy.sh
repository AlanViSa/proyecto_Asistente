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
    print_message "Error: docker-compose.yml not found. Make sure you are in the project's root directory." "$RED"
    exit 1
fi

# Verify environment variables
if [ ! -f ".env.production" ]; then
    print_message "Error: .env.production not found. Please create the file with the necessary variables." "$RED"
    exit 1
fi

# Stop existing containers
print_message "Stopping existing containers..." "$YELLOW"
docker-compose down

# Build images
print_message "Building Docker images..." "$YELLOW"
docker-compose build

# Start services
print_message "Starting services..." "$YELLOW"
docker-compose up -d

# Wait for services to be ready
print_message "Waiting for services to be ready..." "$YELLOW"
sleep 10

# Verify service status
print_message "Verifying service status..." "$YELLOW"
docker-compose ps

# Execute database migrations
print_message "Executing database migrations..." "$YELLOW"
docker-compose exec app alembic upgrade head

# Verify system health
print_message "Verifying system health..." "$YELLOW"
curl -s http://localhost:8000/health || {
    print_message "Error: The service is not responding correctly." "$RED"
    exit 1
}

print_message "¡Despliegue completado exitosamente!" "$GREEN" 