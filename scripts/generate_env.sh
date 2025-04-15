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

# Function to generate a secure random string
generate_secure_string() {
    openssl rand -base64 32
}

# Check that we are in the correct directory
if [ ! -f ".env.production" ]; then
    print_message "Error: .env.production not found. Please create the file first." "$RED"
    exit 1
fi

# Generate secure environment variables
print_message "Generating secure environment variables..." "$YELLOW"

# Generate SECRET_KEY
SECRET_KEY=$(generate_secure_string)
sed -i "s/\${SECRET_KEY}/$SECRET_KEY/" .env.production

# Generate DB_PASSWORD
DB_PASSWORD=$(generate_secure_string)
sed -i "s/\${DB_PASSWORD}/$DB_PASSWORD/" .env.production

# Generar GRAFANA_ADMIN_PASSWORD
GRAFANA_ADMIN_PASSWORD=$(generate_secure_string)
sed -i "s/\${GRAFANA_ADMIN_PASSWORD}/$GRAFANA_ADMIN_PASSWORD/" .env.production

# Request credentials for external services
print_message "\nPlease enter the following credentials:" "$YELLOW"

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

# Save credentials in a secure file
print_message "\nSaving credentials in a secure file..." "$YELLOW"
cat > .env.credentials << EOL
# Credentials generated on $(date)
SECRET_KEY=$SECRET_KEY
DB_PASSWORD=$DB_PASSWORD
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Credenciales de servicios externos
TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER
OPENAI_API_KEY=$OPENAI_API_KEY
EOL

# Set secure permissions
chmod 600 .env.credentials

print_message "\nEnvironment variables generated successfully!" "$GREEN"
print_message "Credentials have been saved to .env.credentials" "$YELLOW"
print_message "IMPORTANT: Save this file in a safe place and do not share it." "$RED"