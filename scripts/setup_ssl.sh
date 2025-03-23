#!/bin/bash

# Verificar si se proporcionó el dominio
if [ -z "$1" ]; then
    echo "Uso: $0 <dominio>"
    echo "Ejemplo: $0 ejemplo.com"
    exit 1
fi

DOMAIN=$1
EMAIL="tu-email@ejemplo.com"  # Cambiar por tu email

# Crear directorio para certificados
mkdir -p /etc/nginx/ssl/live/$DOMAIN

# Instalar certbot si no está instalado
if ! command -v certbot &> /dev/null; then
    echo "Instalando certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Obtener certificado
echo "Obteniendo certificado SSL para $DOMAIN..."
certbot certonly --nginx \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domain $DOMAIN \
    --redirect

# Verificar la renovación automática
echo "Configurando renovación automática..."
certbot renew --dry-run

echo "Configuración SSL completada para $DOMAIN"
echo "Asegúrate de actualizar la configuración de Nginx con las rutas correctas de los certificados" 