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

# Verify that the services are running
if ! docker-compose ps | grep -q "Up"; then
    print_message "Error: Services are not running. Please execute deploy.sh first." "$RED"
    exit 1
fi

# Create admin user
print_message "Creating admin user..." "$YELLOW"
docker-compose exec app python -c "
from app.core.security import get_password_hash
from app.models.user import User  # Assuming you have a User model
from app.db.database import SessionLocal

db = SessionLocal()
admin_user = User(
    email='admin@example.com',
    password=get_password_hash('admin123'),
    name='Administrator',
    is_active=True,
    role='admin'  # Assuming you have a role field
)
db.add(admin_user)
db.commit()
db.close()
"

# Create example services
print_message "Creating example services..." "$YELLOW"
docker-compose exec app python -c "
from app.models.servicio import Servicio
from app.db.session import SessionLocal

db = SessionLocal()
servicios = [
    Servicio(
        name='Haircut',
        description='Professional haircut',
        duration=30,
        price=25.00,
        is_active=True
    ),
    Servicio(
        name='Coloring',
        description='Professional coloring',
        duration=120,
        price=80.00,
        is_active=True
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

# Create test client
print_message "Creating test client..." "$YELLOW"
docker-compose exec app python -c "
from app.models.user import User  # Assuming you have a User model
from app.db.database import SessionLocal
from app.core.security import get_password_hash

db = SessionLocal()
test_user = User(
    email='test_client@example.com',
    password=get_password_hash('test_client123'),
    name='Test Client',
    phone='+1234567890',
    is_active=True,
    role='client'  # Assuming you have a role field
)
db.add(test_user)
db.commit()
db.close()
"

print_message "Database initialization completed successfully!" "$GREEN"
print_message "Test credentials:" "$YELLOW"
print_message "Admin: admin@example.com / admin123" "$YELLOW"
print_message "Client: test_client@example.com / test_client123" "$YELLOW"