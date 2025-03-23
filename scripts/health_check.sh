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

# Función para verificar un endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local response=$(curl -s -w "\n%{http_code}" $url)
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "200" ]; then
        print_message "✓ $name está funcionando correctamente" "$GREEN"
        return 0
    else
        print_message "✗ $name no está respondiendo correctamente (Código: $status_code)" "$RED"
        return 1
    fi
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_message "Error: No se encontró docker-compose.yml. Asegúrate de estar en el directorio raíz del proyecto." "$RED"
    exit 1
fi

print_message "Iniciando verificación de salud del sistema..." "$YELLOW"

# Verificar que los contenedores están corriendo
print_message "\nVerificando contenedores..." "$YELLOW"
if docker-compose ps | grep -q "Up"; then
    print_message "✓ Todos los contenedores están corriendo" "$GREEN"
else
    print_message "✗ Algunos contenedores no están corriendo" "$RED"
    exit 1
fi

# Verificar endpoints de la API
print_message "\nVerificando endpoints de la API..." "$YELLOW"
check_endpoint "http://localhost:8000/health" "Endpoint de salud"
check_endpoint "http://localhost:8000/health/db" "Endpoint de salud de la base de datos"

# Verificar Prometheus
print_message "\nVerificando Prometheus..." "$YELLOW"
check_endpoint "http://localhost:9090/-/healthy" "Prometheus"

# Verificar Grafana
print_message "\nVerificando Grafana..." "$YELLOW"
check_endpoint "http://localhost:3000/api/health" "Grafana"

# Verificar conexión a la base de datos
print_message "\nVerificando conexión a la base de datos..." "$YELLOW"
if docker-compose exec db pg_isready -U postgres > /dev/null 2>&1; then
    print_message "✓ Conexión a la base de datos exitosa" "$GREEN"
else
    print_message "✗ No se pudo conectar a la base de datos" "$RED"
    exit 1
fi

# Verificar Redis
print_message "\nVerificando Redis..." "$YELLOW"
if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
    print_message "✓ Redis está funcionando correctamente" "$GREEN"
else
    print_message "✗ Redis no está respondiendo" "$RED"
    exit 1
fi

# Verificar métricas
print_message "\nVerificando métricas..." "$YELLOW"
if curl -s http://localhost:8000/metrics | grep -q "http_requests_total"; then
    print_message "✓ Las métricas están siendo recopiladas" "$GREEN"
else
    print_message "✗ No se encontraron métricas" "$RED"
    exit 1
fi

print_message "\nVerificación de salud completada." "$GREEN" 