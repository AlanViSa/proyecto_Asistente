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

# Verificar que los servicios están corriendo
if ! docker-compose ps | grep -q "Up"; then
    print_message "Error: Los servicios no están corriendo. Por favor, ejecuta primero deploy.sh" "$RED"
    exit 1
fi

# Crear usuario administrador
print_message "Creando usuario administrador..." "$YELLOW"
docker-compose exec app python -c "
from app.core.security import get_password_hash
from app.models.admin import Admin
from app.db.session import SessionLocal

db = SessionLocal()
admin = Admin(
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    nombre='Administrador',
    activo=True
)
db.add(admin)
db.commit()
db.close()
"

# Crear servicios de ejemplo
print_message "Creando servicios de ejemplo..." "$YELLOW"
docker-compose exec app python -c "
from app.models.servicio import Servicio
from app.db.session import SessionLocal

db = SessionLocal()
servicios = [
    Servicio(
        nombre='Corte de Cabello',
        descripcion='Corte de cabello profesional',
        duracion=30,
        precio=25.00,
        activo=True
    ),
    Servicio(
        nombre='Coloración',
        descripcion='Coloración profesional',
        duracion=120,
        precio=80.00,
        activo=True
    ),
    Servicio(
        nombre='Manicure',
        descripcion='Manicure básico',
        duracion=45,
        precio=35.00,
        activo=True
    )
]
for servicio in servicios:
    db.add(servicio)
db.commit()
db.close()
"

# Crear cliente de prueba
print_message "Creando cliente de prueba..." "$YELLOW"
docker-compose exec app python -c "
from app.models.cliente import Cliente
from app.db.session import SessionLocal

db = SessionLocal()
cliente = Cliente(
    email='cliente@example.com',
    hashed_password=get_password_hash('cliente123'),
    nombre='Cliente Prueba',
    telefono='+1234567890',
    activo=True
)
db.add(cliente)
db.commit()
db.close()
"

print_message "¡Inicialización de la base de datos completada exitosamente!" "$GREEN"
print_message "Credenciales de prueba:" "$YELLOW"
print_message "Admin: admin@example.com / admin123" "$YELLOW"
print_message "Cliente: cliente@example.com / cliente123" "$YELLOW" 