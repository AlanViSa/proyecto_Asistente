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

# Función para generar una cadena aleatoria segura
generate_secure_string() {
    openssl rand -base64 32
}

# Verificar que estamos en el directorio correcto
if [ ! -f ".env.production" ]; then
    print_message "Error: No se encontró .env.production. Por favor, crea el archivo primero." "$RED"
    exit 1
fi

# Generar variables de entorno seguras
print_message "Generando variables de entorno seguras..." "$YELLOW"

# Generar SECRET_KEY
SECRET_KEY=$(generate_secure_string)
sed -i "s/\${SECRET_KEY}/$SECRET_KEY/" .env.production

# Generar DB_PASSWORD
DB_PASSWORD=$(generate_secure_string)
sed -i "s/\${DB_PASSWORD}/$DB_PASSWORD/" .env.production

# Generar GRAFANA_ADMIN_PASSWORD
GRAFANA_ADMIN_PASSWORD=$(generate_secure_string)
sed -i "s/\${GRAFANA_ADMIN_PASSWORD}/$GRAFANA_ADMIN_PASSWORD/" .env.production

# Solicitar credenciales de servicios externos
print_message "\nPor favor, ingresa las siguientes credenciales:" "$YELLOW"

# Twilio
read -p "Twilio Account SID: " TWILIO_ACCOUNT_SID
read -p "Twilio Auth Token: " TWILIO_AUTH_TOKEN
read -p "Twilio Phone Number: " TWILIO_PHONE_NUMBER

# OpenAI
read -p "OpenAI API Key: " OPENAI_API_KEY

# Actualizar archivo con las credenciales
sed -i "s/\${TWILIO_ACCOUNT_SID}/$TWILIO_ACCOUNT_SID/" .env.production
sed -i "s/\${TWILIO_AUTH_TOKEN}/$TWILIO_AUTH_TOKEN/" .env.production
sed -i "s/\${TWILIO_PHONE_NUMBER}/$TWILIO_PHONE_NUMBER/" .env.production
sed -i "s/\${OPENAI_API_KEY}/$OPENAI_API_KEY/" .env.production

# Guardar credenciales en un archivo seguro
print_message "\nGuardando credenciales en un archivo seguro..." "$YELLOW"
cat > .env.credentials << EOL
# Credenciales generadas el $(date)
SECRET_KEY=$SECRET_KEY
DB_PASSWORD=$DB_PASSWORD
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Credenciales de servicios externos
TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER
OPENAI_API_KEY=$OPENAI_API_KEY
EOL

# Establecer permisos seguros
chmod 600 .env.credentials

print_message "\n¡Variables de entorno generadas exitosamente!" "$GREEN"
print_message "Las credenciales se han guardado en .env.credentials" "$YELLOW"
print_message "IMPORTANTE: Guarda este archivo en un lugar seguro y no lo compartas." "$RED" 