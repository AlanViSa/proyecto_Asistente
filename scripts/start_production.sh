#!/bin/bash

# Verify that we are in production
if [ "$ENVIRONMENT" != "production" ]; then
    echo "This script should only be executed in production"
    exit 1
fi

# Verify critical environment variables
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
        echo "Error: The environment variable $var is not configured"
        exit 1
    fi
done

# Create logs directory if it doesn't exist
mkdir -p /var/log/salon

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the application with Gunicorn
echo "Starting the application..."
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