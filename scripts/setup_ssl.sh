#!/bin/bash

# Check if the domain was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 example.com"
    exit 1
fi

DOMAIN=$1
EMAIL="your-email@example.com"  # Change to your email

# Create directory for certificates
mkdir -p /etc/nginx/ssl/live/$DOMAIN

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Get certificate
echo "Obtaining SSL certificate for $DOMAIN..."
certbot certonly --nginx \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domain $DOMAIN \
    --redirect

# Verify automatic renewal
echo "Configuring automatic renewal..."
certbot renew --dry-run

echo "SSL configuration completed for $DOMAIN"
echo "Make sure to update the Nginx configuration with the correct certificate paths"