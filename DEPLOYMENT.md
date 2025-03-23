# Guía de Despliegue - Salon Assistant

## Requisitos del Sistema

- Python 3.8+
- PostgreSQL 13+
- Docker 20.10+
- Docker Compose 2.0+
- Nginx (opcional, para proxy inverso)

## Preparación del Entorno

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd salon-assistant
```

2. Crear y activar entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

1. Copiar el archivo de ejemplo de variables de entorno:
```bash
cp .env.example .env.production
```

2. Configurar las variables de entorno en `.env.production`:
- `DATABASE_URL`: URL de conexión a la base de datos
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo para JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración del token
- `SMTP_HOST`: Servidor SMTP para correos
- `SMTP_PORT`: Puerto SMTP
- `SMTP_USER`: Usuario SMTP
- `SMTP_PASSWORD`: Contraseña SMTP
- `FRONTEND_URL`: URL del frontend

## Base de Datos

1. Crear la base de datos:
```bash
createdb salon_assistant
```

2. Ejecutar migraciones:
```bash
alembic upgrade head
```

3. Crear usuario administrador inicial:
```bash
python scripts/create_admin.py
```

## Despliegue con Docker

1. Construir las imágenes:
```bash
docker-compose -f docker-compose.prod.yml build
```

2. Iniciar los servicios:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Configuración de Nginx (Opcional)

1. Instalar Nginx:
```bash
sudo apt-get update
sudo apt-get install nginx
```

2. Configurar Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Habilitar la configuración:
```bash
sudo ln -s /etc/nginx/sites-available/salon-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/HTTPS (Recomendado)

1. Instalar Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtener certificado SSL:
```bash
sudo certbot --nginx -d your-domain.com
```

## Monitoreo y Mantenimiento

1. Verificar logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

2. Backup de base de datos:
```bash
pg_dump -U postgres salon_assistant > backup.sql
```

3. Restaurar backup:
```bash
psql -U postgres salon_assistant < backup.sql
```

## Actualización

1. Detener servicios:
```bash
docker-compose -f docker-compose.prod.yml down
```

2. Actualizar código:
```bash
git pull origin main
```

3. Reconstruir y reiniciar:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Solución de Problemas

1. Verificar estado de servicios:
```bash
docker-compose -f docker-compose.prod.yml ps
```

2. Revisar logs específicos:
```bash
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml logs db
```

3. Reiniciar servicios:
```bash
docker-compose -f docker-compose.prod.yml restart
```

## Seguridad

1. Configurar firewall:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. Actualizar regularmente:
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Contacto

Para soporte técnico o preguntas sobre el despliegue, contactar al equipo de desarrollo. 