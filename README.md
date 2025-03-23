# Salon Assistant

Sistema de gestión para salones de belleza que permite administrar citas, clientes, servicios y notificaciones.

## Requisitos del Sistema

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/salon-assistant.git
cd salon-assistant
```

2. Copiar el archivo de variables de entorno de ejemplo:
```bash
cp .env.production.example .env.production
```

3. Editar el archivo `.env.production` con tus credenciales y configuraciones.

4. Dar permisos de ejecución a los scripts:
```bash
chmod +x scripts/*.sh
```

## Despliegue

1. Generar variables de entorno seguras:
```bash
./scripts/generate_env.sh
```

2. Configurar la seguridad del sistema:
```bash
./scripts/security_setup.sh
```

3. Configurar el sistema de copias de seguridad:
```bash
./scripts/backup_setup.sh
```

4. Iniciar los servicios:
```bash
docker-compose up -d
```

5. Inicializar la base de datos:
```bash
./scripts/init_db.sh
```

6. Verificar el estado del sistema:
```bash
./scripts/health_check.sh
```

## Acceso a los Servicios

- API: https://tu-dominio.com/api/v1
- Documentación API: https://tu-dominio.com/docs
- Prometheus: https://tu-dominio.com:9090
- Grafana: https://tu-dominio.com:3000

### Credenciales de Prueba

- Administrador:
  - Email: admin@example.com
  - Contraseña: admin123

- Cliente:
  - Email: cliente@example.com
  - Contraseña: cliente123

## Monitoreo

El sistema incluye las siguientes herramientas de monitoreo:

### Prometheus
- Métricas de la aplicación FastAPI
- Métricas del sistema (CPU, memoria, disco)
- Métricas de la base de datos
- Métricas de Redis

### Grafana
- Dashboard principal con métricas clave
- Dashboard de rendimiento de la API
- Dashboard de uso de recursos
- Dashboard de errores y excepciones

### Logs
- Logs estructurados en formato JSON
- Rotación automática de logs
- Niveles de log configurables

### Alertas
- Alertas configuradas para:
  - Uso alto de CPU (>80%)
  - Uso alto de memoria (>80%)
  - Uso alto de disco (>80%)
  - Errores de la API (>5%)
  - Latencia alta (>1s)
  - Servicios caídos

## Mantenimiento

### Actualización
```bash
git pull
docker-compose pull
docker-compose up -d
```

### Copias de Seguridad
- Se realizan automáticamente a las 2:00 AM
- Se mantienen durante 7 días
- Incluyen:
  - Base de datos
  - Archivos de configuración
  - Certificados SSL

Para realizar un backup manual:
```bash
/var/backups/salon-assistant/backup.sh
```

Para restaurar un backup:
```bash
/var/backups/salon-assistant/restore.sh <archivo_backup.tar.gz>
```

### Logs
Los logs se encuentran en:
- Aplicación: `logs/app.log`
- Nginx: `logs/nginx.log`
- Base de datos: `logs/db.log`
- Redis: `logs/redis.log`

## Solución de Problemas

1. Verificar el estado de los servicios:
```bash
docker-compose ps
```

2. Revisar logs:
```bash
docker-compose logs -f [servicio]
```

3. Verificar conectividad:
```bash
./scripts/health_check.sh
```

4. Reiniciar servicios:
```bash
docker-compose restart [servicio]
```

## Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 