#!/bin/bash

# Verificar que estamos en producción
if [ "$ENVIRONMENT" != "production" ]; then
    echo "Este script solo debe ejecutarse en producción"
    exit 1
fi

# Verificar variables de entorno críticas
required_vars=(
    "DATABASE_URL"
    "OPENAI_API_KEY"
    "TWILIO_ACCOUNT_SID"
    "TWILIO_AUTH_TOKEN"
    "SECRET_KEY"
    "SERVER_HOST"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: La variable de entorno $var no está configurada"
        exit 1
    fi
done

# Crear directorio de logs si no existe
mkdir -p /var/log/salon

# Aplicar migraciones de base de datos
echo "Aplicando migraciones de base de datos..."
alembic upgrade head

# Iniciar la aplicación con Gunicorn
echo "Iniciando la aplicación..."
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --log-file /var/log/salon/gunicorn.log \
    --access-logfile /var/log/salon/access.log \
    --error-logfile /var/log/salon/error.log \
    --capture-output \
    --enable-stdio-inheritance 