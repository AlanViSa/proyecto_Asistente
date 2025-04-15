# Salon Assistant - Documentación Completa

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Visión General del Proyecto](#visión-general-del-proyecto)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Diseño de la Base de Datos](#diseño-de-la-base-de-datos)
5. [Componentes Principales](#componentes-principales)
   - [Sistema de Autenticación](#sistema-de-autenticación)
   - [Gestión de Citas](#gestión-de-citas)
   - [Sistema de Notificaciones](#sistema-de-notificaciones)
   - [Gestión de Servicios](#gestión-de-servicios)
   - [Sistema de Programación](#sistema-de-programación)
6. [Documentación de la API](#documentación-de-la-api)
7. [Flujo de Desarrollo](#flujo-de-desarrollo)
8. [Guía de Despliegue](#guía-de-despliegue)
9. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
10. [Solución de Problemas](#solución-de-problemas)
11. [Mejoras Futuras](#mejoras-futuras)

## Introducción

Salon Assistant es un sistema integral de gestión diseñado para salones de belleza y negocios similares basados en servicios. Proporciona una solución completa para la reserva de citas, gestión de clientes, catálogo de servicios, notificaciones automatizadas y análisis de negocio.

El sistema fue desarrollado para abordar desafíos comunes que enfrentan los negocios de salones:
- Reserva y seguimiento manual ineficiente de citas
- Alta tasa de ausencias y cancelaciones de último minuto
- Dificultad en la gestión de relaciones con clientes y preferencias
- Falta de información basada en datos para la optimización del negocio
- Desafíos en la programación del personal y gestión de recursos

Esta documentación proporciona una visión detallada de la arquitectura, componentes y funcionalidad del sistema para ayudar a los desarrolladores a entender, mantener y extender la aplicación.

## Visión General del Proyecto

### Historia del Desarrollo

Salon Assistant comenzó como una solución para digitalizar las operaciones de salones que anteriormente se gestionaban mediante sistemas basados en papel o hojas de cálculo básicas. El proyecto evolucionó a través de varias fases:

1. **Fase de Investigación y Requisitos**: Entrevistas extensas con propietarios y personal de salones identificaron puntos críticos y requisitos clave.
2. **Desarrollo de MVP**: El desarrollo inicial se centró en la funcionalidad básica de reserva de citas y gestión de clientes.
3. **Integración del Sistema de Notificaciones**: Adición de notificaciones multicanal a través de correo electrónico, SMS y WhatsApp.
4. **Análisis e Informes**: Implementación de funciones de análisis de negocio e informes.
5. **Internacionalización**: Soporte para múltiples idiomas con enfoque inicial en inglés y español.
6. **Optimización de Rendimiento**: Mejoras en tiempos de respuesta y rendimiento general del sistema.

### Características Principales

- **Programación Inteligente de Citas**: Detección inteligente de conflictos y optimización
- **Notificaciones Multicanal**: Recordatorios por correo electrónico, SMS y WhatsApp
- **Portal del Cliente**: Reserva y gestión de citas autoservicio
- **Gestión de Catálogo de Servicios**: Ofertas de servicios flexibles con precios y duración
- **Gestión de Personal**: Optimización de horarios y seguimiento de rendimiento
- **Análisis de Negocio**: Información sobre tendencias de citas, popularidad de servicios e ingresos
- **Gestión de Disponibilidad**: Bloqueo de franjas horarias no disponibles y gestión de horarios comerciales

### Stack Tecnológico

- **Backend**: FastAPI (Python) para endpoints API de alto rendimiento
- **Base de Datos**: PostgreSQL para producción, SQLite para desarrollo/pruebas
- **Caché y Limitación de Tasa**: Redis
- **Procesamiento de Tareas**: APScheduler para recordatorios y tareas programadas
- **Servicios Externos**: Twilio (SMS/WhatsApp), OpenAI (asistencia de chatbot)
- **Monitoreo**: Prometheus y Grafana
- **Contenedorización**: Docker y Docker Compose
- **CI/CD**: GitHub Actions

## Arquitectura del Sistema

Salon Assistant sigue una arquitectura moderna inspirada en microservicios mientras mantiene la simplicidad de un despliegue monolítico. Este enfoque proporciona una buena separación de preocupaciones y desarrollo modular sin la complejidad operacional de un sistema completamente distribuido.

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Dispositivos Cliente                      │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Servidor Web)                     │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Aplicación FastAPI                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Endpoints  │  │   Capa de   │  │     Middlewares     │  │
│  │     API     │  │  Servicios  │  │  (Logging, Auth)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Modelos   │  │  Esquemas   │  │  Configuración Core │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───┬───────────────────┬───────────────────────┬─────────────┘
    ▼                   ▼                       ▼
┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ PostgreSQL  │  │      Redis      │  │ Servicios Externos  │
│ Base de Datos│  │(Caché/Rate Limit)│  │  (Twilio, OpenAI)  │
└─────────────┘  └─────────────────┘  └─────────────────────┘
       ▲                                         ▲
       │                                         │
       └─────────────┐               ┌───────────┘
                     ▼               ▼
               ┌──────────────────────────┐
               │  Programadores de Fondo  │
               │(Procesamiento Recordatorio)│
               └──────────────────────────┘
```

### Interacciones de Componentes

1. **Flujo de Solicitud del Cliente**:
   - Las solicitudes del cliente llegan a través del servidor web Nginx
   - Las solicitudes son procesadas por middleware para logging, autenticación y limitación de tasa
   - Los endpoints API validan la entrada usando esquemas Pydantic
   - La capa de servicio implementa la lógica de negocio
   - Las operaciones de base de datos ocurren a través de modelos ORM SQLAlchemy

2. **Flujo de Notificación**:
   - Las tareas programadas verifican las próximas citas que requieren notificaciones
   - Las preferencias de notificación determinan qué canales usar
   - Se llaman servicios externos para entregar notificaciones
   - El estado de entrega se registra para seguimiento y análisis

3. **Flujo de Datos**:
   - Los datos se almacenan principalmente en PostgreSQL
   - Redis proporciona capacidades de caché y limitación de tasa
   - Copias de seguridad regulares garantizan la seguridad de los datos
   - Las migraciones de base de datos se gestionan a través de Alembic

## Diseño de la Base de Datos

El esquema de la base de datos fue diseñado para representar las relaciones entre clientes, citas, servicios y otras entidades dentro del dominio de negocio del salón.

### Diagrama de Entidad-Relación

```
┌───────────────┐       ┌───────────────────┐       ┌────────────────┐
│    Cliente    │       │       Cita        │       │    Servicio    │
├───────────────┤       ├───────────────────┤       ├────────────────┤
│ id            │◄──┐   │ id                │   ┌──►│ id             │
│ email         │   │   │ fecha_hora        │   │   │ nombre         │
│ nombre_completo│  │   │ estado            │   │   │ descripcion    │
│ telefono      │   └───┤ cliente_id        │   │   │ precio         │
│ password_hash │      │ servicio_id        │───┘   │ duracion_minutos│
│ esta_activo   │       │ notas             │       │ esta_activo    │
│ es_admin      │       └───────────────────┘       └────────────────┘
└───────────────┘               │
        │                       │
        ▼                       │
┌────────────────────────┐      │
│PreferenciaNotificacion │      │
├────────────────────────┤      │
│ id                     │      │
│ cliente_id             │      │
│ email_habilitado       │      │
│ sms_habilitado         │      │
│ whatsapp_habilitado    │      │
│ recordatorio_24h       │      │
│ recordatorio_2h        │      │
│ zona_horaria           │      │
└────────────────────────┘      │
                                ▼
┌─────────────────┐     ┌───────────────────┐
│HorarioBloqueado │     │    Recordatorio   │
├─────────────────┤     ├───────────────────┤
│ id              │     │ id                │
│ hora_inicio     │     │ cita_id           │
│ hora_fin        │     │ hora_programada   │
│ motivo          │     │ enviado           │
└─────────────────┘     │ mensaje           │
                        └───────────────────┘
```

## Componentes Principales

### Sistema de Autenticación

**Propósito**: El sistema de autenticación proporciona control de acceso seguro a la aplicación, diferenciando entre cuentas de cliente y administrador.

**Archivos Clave**:
- `app/core/security.py`: Utilidades centrales de seguridad
- `app/api/v1/endpoints/auth.py`: Endpoints de autenticación
- `app/services/auth.py`: Lógica de negocio de autenticación

**Características**:
- Autenticación basada en JWT
- Hash de contraseñas con bcrypt
- Control de acceso basado en roles
- Funcionalidad de token de actualización
- Limitación de tasa para intentos de inicio de sesión

**Fundamento de Desarrollo**:
El sistema de autenticación fue diseñado con la seguridad como preocupación principal mientras se mantiene una experiencia de usuario fluida. Se eligieron JWTs por su naturaleza sin estado y compatibilidad con aplicaciones frontend modernas. El sistema implementa las mejores prácticas de la industria, incluyendo hash de contraseñas, expiración de tokens y protección contra ataques de fuerza bruta.

### Gestión de Citas

**Propósito**: El sistema de gestión de citas es la funcionalidad central de la aplicación, manejando la creación, modificación y seguimiento de citas de clientes.

**Archivos Clave**:
- `app/models/appointment.py`: Modelos de base de datos para citas
- `app/api/v1/endpoints/appointments.py`: Endpoints API relacionados con citas
- `app/services/appointment_service.py`: Lógica de negocio para citas
- `app/services/cita.py`: Alias en español para compatibilidad hacia atrás

**Características**:
- Creación de citas con detección de conflictos
- Reprogramación y cancelación
- Seguimiento de estado (pendiente, confirmada, completada, cancelada, no asistió)
- Notas de cita personalizables
- Historial de citas del cliente

**Fundamento de Desarrollo**:
El sistema de citas fue desarrollado para proporcionar una solución de programación flexible pero robusta. Los desafíos clave incluyeron manejar diferencias de zona horaria, prevenir reservas duplicadas y garantizar la asignación adecuada de recursos. El diseño permite extensiones futuras como asignación de personal y gestión de recursos.

### Sistema de Notificaciones

**Propósito**: El sistema de notificaciones mantiene a los clientes informados sobre sus citas a través de múltiples canales de comunicación.

**Archivos Clave**:
- `app/services/notification_service.py`: Lógica central de notificaciones
- `app/services/reminder_service.py`: Procesamiento de recordatorios de citas
- `app/services/recordatorio.py`: Alias en español para compatibilidad hacia atrás
- `app/tasks/scheduler.py`: Tareas programadas de recordatorio

**Características**:
- Notificaciones multicanal (Email, SMS, WhatsApp)
- Plantillas de notificación personalizables
- Preferencias de notificación del cliente
- Recordatorios programados (24 horas y 2 horas antes de las citas)
- Seguimiento de entrega de notificaciones

**Fundamento de Desarrollo**:
El sistema de notificaciones fue diseñado para reducir las ausencias a citas, que se identificó como un punto crítico importante para los negocios de salones. La investigación indicó que los recordatorios oportunos aumentan significativamente las tasas de asistencia. El sistema respeta las preferencias del cliente y las zonas horarias locales para garantizar que las notificaciones se reciban en momentos apropiados.

**Soporte de Internacionalización**:
La aplicación incluye versiones en inglés y español de los archivos de servicio para respaldar negocios multilingües. Esto se implementó utilizando patrones de alias para mantener la compatibilidad hacia atrás durante la transición.

### Gestión de Servicios

**Propósito**: El componente de gestión de servicios permite al salón administrar sus ofertas de servicios, incluidos precios, duración y disponibilidad.

**Archivos Clave**:
- `app/models/service.py`: Modelo de catálogo de servicios
- `app/api/v1/endpoints/services.py`: Endpoints de gestión de servicios
- `app/services/service_service.py`: Lógica de negocio para servicios

**Características**:
- Gestión de catálogo de servicios
- Configuración de precios y duración
- Activación/desactivación de servicios
- Categorización de servicios
- Análisis de servicios

**Fundamento de Desarrollo**:
Los servicios son las ofertas centrales de un negocio de salón. Este componente fue diseñado para proporcionar flexibilidad en la gestión de detalles del servicio mientras se mantiene la consistencia de datos para programación e informes. La separación entre servicios activos e inactivos permite ofertas estacionales o temporales sin afectar datos históricos.

### Sistema de Programación

**Propósito**: El sistema de programación gestiona la disponibilidad del salón y optimiza la asignación de citas.

**Archivos Clave**:
- `app/services/blocked_schedule_service.py`: Gestionar períodos de tiempo no disponibles
- `app/services/horario_bloqueado.py`: Alias en español para compatibilidad hacia atrás

**Características**:
- Gestión de horarios comerciales
- Seguimiento de vacaciones y cierres
- Reserva de bloques de tiempo
- Verificación de disponibilidad
- Sugerencias de programación inteligentes

**Fundamento de Desarrollo**:
La programación efectiva es crítica para maximizar los ingresos del salón y la utilización del personal. El sistema de programación considera horarios comerciales, períodos bloqueados, citas existentes y duración del servicio para determinar disponibilidad. Este componente fue diseñado para ser extensible para características futuras como programación específica de personal y asignación de recursos.

## Documentación de la API

La API sigue principios RESTful y está organizada por tipos de recursos. Todos los endpoints tienen el prefijo `/api/v1/`.

### Endpoints de Autenticación

| Endpoint | Método | Descripción | Autorización |
|----------|--------|-------------|--------------|
| `/api/v1/auth/login` | POST | Autenticar un usuario y devolver token de acceso | Público |
| `/api/v1/auth/register` | POST | Registrar un nuevo cliente | Público |
| `/api/v1/auth/refresh` | POST | Actualizar un token de acceso | Requiere token de actualización |

### Endpoints de Cliente

| Endpoint | Método | Descripción | Autorización |
|----------|--------|-------------|--------------|
| `/api/v1/clients` | GET | Listar todos los clientes | Solo admin |
| `/api/v1/clients/{client_id}` | GET | Obtener detalles de cliente | Admin o propio cliente |
| `/api/v1/clients` | POST | Crear un nuevo cliente | Solo admin |
| `/api/v1/clients/{client_id}` | PUT | Actualizar información de cliente | Admin o propio cliente |

### Endpoints de Cita

| Endpoint | Método | Descripción | Autorización |
|----------|--------|-------------|--------------|
| `/api/v1/appointments` | GET | Listar citas con filtros | Solo admin |
| `/api/v1/appointments/{appointment_id}` | GET | Obtener detalles de cita | Admin o cliente de la cita |
| `/api/v1/appointments` | POST | Crear una nueva cita | Autenticado |
| `/api/v1/appointments/{appointment_id}` | PUT | Actualizar cita | Admin o cliente de la cita |
| `/api/v1/appointments/{appointment_id}/cancel` | POST | Cancelar cita | Admin o cliente de la cita |
| `/api/v1/appointments/{appointment_id}/confirm` | POST | Confirmar cita | Solo admin |
| `/api/v1/appointments/{appointment_id}/complete` | POST | Marcar cita como completada | Solo admin |
| `/api/v1/appointments/{appointment_id}/no-show` | POST | Marcar cliente como no asistió | Solo admin |

## Flujo de Desarrollo

### Configuración del Proyecto

1. Clonar el repositorio:
   ```bash
   git clone <repository-url>
   cd salon-assistant
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con valores apropiados
   ```

5. Ejecutar migraciones de base de datos:
   ```bash
   alembic upgrade head
   ```

6. Crear un usuario administrador:
   ```bash
   python create_admin.py
   ```

7. Iniciar el servidor de desarrollo:
   ```bash
   uvicorn app.main:app --reload
   ```

## Guía de Despliegue

La aplicación soporta múltiples métodos de despliegue:

### Despliegue Docker (Recomendado)

1. Configurar entorno:
   ```bash
   cp .env.production.example .env.production
   # Editar .env.production con valores de producción
   ```

2. Construir e iniciar contenedores:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. Ejecutar migraciones:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

4. Crear usuario administrador (si es necesario):
   ```bash
   docker-compose exec web python create_admin.py
   ```

### Despliegue tradicional en VM

Consulte las instrucciones detalladas en [DEPLOYMENT.md](../DEPLOYMENT.md).

## Monitoreo y Mantenimiento

### Comprobaciones de Salud

La aplicación proporciona endpoints de comprobación de salud:
- `/api/health`: Estado básico de la aplicación
- `/api/health/detailed`: Estado detallado de componentes, incluyendo base de datos y servicios externos

### Monitoreo

Prometheus se utiliza para la recopilación de métricas, con las siguientes métricas clave:
- Tasas de solicitud y tiempos de respuesta
- Rendimiento de consultas de base de datos
- Disponibilidad de servicios externos
- Ejecución de tareas en segundo plano

Los paneles de Grafana visualizan estas métricas y proporcionan capacidades de alerta.

### Logging

La aplicación utiliza logging estructurado con niveles configurables:
- ERROR: Problemas críticos que requieren atención inmediata
- WARNING: Problemas potenciales que podrían necesitar investigación
- INFO: Información de operación normal
- DEBUG: Información detallada para depuración

Los logs se escriben en archivos y stdout para entornos de contenedores.

### Estrategia de Respaldo

Las copias de seguridad regulares de la base de datos son esenciales:
1. Copias de seguridad diarias automatizadas
2. Política de retención para gestionar el almacenamiento de copias de seguridad
3. Proceso de verificación de copias de seguridad
4. Procedimientos de prueba de restauración

## Solución de Problemas

### Problemas Comunes

#### Problemas de Autenticación
- Verificar configuración de secreto JWT y algoritmo
- Verificar método de hash de contraseña
- Inspeccionar configuración de expiración de token

#### Problemas de Conexión a Base de Datos
- Verificar configuración de URL de base de datos
- Verificar que el servicio de base de datos esté en ejecución
- Inspeccionar logs de base de datos para errores

#### Fallos de Notificación
- Verificar credenciales de servicio externo (Twilio)
- Verificar información de contacto del cliente
- Inspeccionar logs de servicio de notificación

#### Problemas de Rendimiento
- Verificar indexación de base de datos
- Revisar logs de consultas lentas
- Inspeccionar configuración de caché

### Técnicas de Depuración

1. Habilitar logging de depuración:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Usar endpoints de depuración de API (solo admin):
   - `/api/debug/config`: Ver configuración de aplicación
   - `/api/debug/cache`: Inspeccionar contenidos de caché
   - `/api/debug/tasks`: Ver estado de tareas programadas

3. Inspección de base de datos:
   ```bash
   docker-compose exec db psql -U postgres salon_assistant
   ```

## Mejoras Futuras

### Características Planificadas

1. **Gestión de Personal**:
   - Perfiles de personal y especializaciones
   - Programación específica de personal
   - Análisis de rendimiento

2. **Programa de Fidelización de Clientes**:
   - Sistema de puntos por citas
   - Redención de recompensas
   - Comunicaciones automatizadas de fidelización

3. **Gestión de Inventario**:
   - Seguimiento de productos
   - Uso por servicio
   - Alertas de stock bajo

4. **Aplicación Móvil**:
   - Experiencia móvil nativa
   - Notificaciones push
   - Capacidades offline

5. **Análisis Avanzado**:
   - Patrones predictivos de reserva
   - Previsión de ingresos
   - Análisis de ciclo de vida del cliente

### Mejoras Arquitectónicas

1. **Evolución a Microservicios**:
   - División en servicios específicos de dominio
   - Implementación de gateway API
   - Descubrimiento de servicios

2. **Características en Tiempo Real**:
   - Implementación de WebSocket
   - Actualizaciones de panel en vivo
   - Notificaciones instantáneas

3. **Caché Avanzado**:
   - Capa de caché distribuido
   - Invalidación inteligente de caché
   - Caché en el borde

---

Esta documentación fue creada para proporcionar una comprensión integral del sistema Salon Assistant. Debe mantenerse actualizada a medida que el sistema evoluciona y se agregan nuevas características. 