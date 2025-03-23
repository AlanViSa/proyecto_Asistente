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
    print_message "Error: No se encontró docker-compose.yml. Asegúrate de estar en el directorio raíz del proyecto." "$RED"
    exit 1
fi

# Verificar variables de entorno
if [ ! -f ".env.production" ]; then
    print_message "Error: No se encontró .env.production. Por favor, crea el archivo con las variables necesarias." "$RED"
    exit 1
fi

# Detener contenedores existentes
print_message "Deteniendo contenedores existentes..." "$YELLOW"
docker-compose down

# Construir imágenes
print_message "Construyendo imágenes Docker..." "$YELLOW"
docker-compose build

# Iniciar servicios
print_message "Iniciando servicios..." "$YELLOW"
docker-compose up -d

# Esperar a que los servicios estén listos
print_message "Esperando a que los servicios estén listos..." "$YELLOW"
sleep 10

# Verificar estado de los servicios
print_message "Verificando estado de los servicios..." "$YELLOW"
docker-compose ps

# Ejecutar migraciones de base de datos
print_message "Ejecutando migraciones de base de datos..." "$YELLOW"
docker-compose exec app alembic upgrade head

# Verificar salud del sistema
print_message "Verificando salud del sistema..." "$YELLOW"
curl -s http://localhost:8000/health || {
    print_message "Error: El servicio no está respondiendo correctamente." "$RED"
    exit 1
}

print_message "¡Despliegue completado exitosamente!" "$GREEN" 