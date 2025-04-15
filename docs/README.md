# Salon Assistant - Complete Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Database Design](#database-design)
5. [Core Components](#core-components)
   - [Authentication System](#authentication-system)
   - [Appointment Management](#appointment-management)
   - [Notification System](#notification-system)
   - [Service Management](#service-management)
   - [Scheduling System](#scheduling-system)
6. [API Documentation](#api-documentation)
7. [Development Workflow](#development-workflow)
8. [Deployment Guide](#deployment-guide)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)

## Introduction

Salon Assistant is a comprehensive management system designed for beauty salons and similar service-based businesses. It provides an end-to-end solution for appointment booking, client management, service cataloging, automated notifications, and business analytics. 

The system was developed to address common challenges faced by salon businesses:
- Inefficient manual appointment booking and tracking
- High rate of no-shows and last-minute cancellations
- Difficulty in managing client relationships and preferences
- Lack of data-driven insights for business optimization
- Challenges in staff scheduling and resource management

This documentation provides a detailed overview of the system's architecture, components, and functionality to assist developers in understanding, maintaining, and extending the application.

## Project Overview

### Development History

Salon Assistant began as a solution to digitize salon operations that were previously managed through paper-based systems or basic spreadsheets. The project evolved through several phases:

1. **Research & Requirements Phase**: Extensive interviews with salon owners and staff identified key pain points and requirements.
2. **MVP Development**: Initial development focused on core appointment booking and client management functionality.
3. **Notification System Integration**: Addition of multi-channel notifications via email, SMS and WhatsApp.
4. **Analytics & Reporting**: Implementation of business analytics and reporting features.
5. **Internationalization**: Support for multiple languages with initial focus on English and Spanish.
6. **Performance Optimization**: Improvements in response times and overall system performance.

### Key Features

- **Smart Appointment Scheduling**: Intelligent conflict detection and optimization
- **Multi-channel Notifications**: Email, SMS, and WhatsApp reminders
- **Client Portal**: Self-service appointment booking and management
- **Service Catalog Management**: Flexible service offerings with pricing and duration
- **Staff Management**: Schedule optimization and performance tracking
- **Business Analytics**: Insights on appointment trends, service popularity, and revenue
- **Availability Management**: Block out unavailable time slots and manage business hours

### Technology Stack

- **Backend**: FastAPI (Python) for high-performance API endpoints
- **Database**: PostgreSQL for production, SQLite for development/testing
- **Caching & Rate Limiting**: Redis
- **Task Processing**: APScheduler for scheduled reminders and tasks
- **External Services**: Twilio (SMS/WhatsApp), OpenAI (chatbot assistance)
- **Monitoring**: Prometheus and Grafana
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions

## System Architecture

Salon Assistant follows a modern microservices-inspired architecture while maintaining the simplicity of a monolithic deployment. This approach provides good separation of concerns and modular development without the operational complexity of a fully distributed system.

### Architectural Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Devices                        │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       Nginx (Web Server)                     │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │     API     │  │  Services   │  │     Middlewares     │  │
│  │  Endpoints  │  │   Layer     │  │  (Logging, Auth)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Models   │  │   Schemas   │  │     Core Config     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───┬───────────────────┬───────────────────────┬─────────────┘
    ▼                   ▼                       ▼
┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ PostgreSQL  │  │      Redis      │  │  External Services  │
│  Database   │  │(Cache/Rate Limit)│  │  (Twilio, OpenAI)  │
└─────────────┘  └─────────────────┘  └─────────────────────┘
       ▲                                         ▲
       │                                         │
       └─────────────┐               ┌───────────┘
                     ▼               ▼
               ┌──────────────────────────┐
               │  Background Schedulers   │
               │  (Reminder Processing)   │
               └──────────────────────────┘
```

### Component Interactions

1. **Client Request Flow**:
   - Client requests come through the Nginx web server
   - Requests are processed by middleware for logging, authentication, and rate limiting
   - API endpoints validate input using Pydantic schemas
   - Service layer implements business logic
   - Database operations occur through SQLAlchemy ORM models

2. **Notification Flow**:
   - Scheduled tasks check for upcoming appointments requiring notifications
   - Notification preferences determine which channels to use
   - External services are called to deliver notifications
   - Delivery status is recorded for tracking and analytics

3. **Data Flow**:
   - Data is stored primarily in PostgreSQL
   - Redis provides caching and rate limiting capabilities
   - Regular backups ensure data safety
   - Database migrations are managed through Alembic

## Database Design

The database schema was designed to represent the relationships between clients, appointments, services, and other entities within the salon business domain.

### Entity Relationship Diagram

```
┌───────────────┐       ┌───────────────────┐       ┌────────────────┐
│    Client     │       │    Appointment    │       │    Service     │
├───────────────┤       ├───────────────────┤       ├────────────────┤
│ id            │◄──┐   │ id                │   ┌──►│ id             │
│ email         │   │   │ date_time         │   │   │ name           │
│ full_name     │   │   │ status            │   │   │ description    │
│ phone         │   └───┤ client_id         │   │   │ price          │
│ hashed_password│      │ service_id        │───┘   │ duration_minutes│
│ is_active     │       │ notes             │       │ is_active      │
│ is_admin      │       └───────────────────┘       └────────────────┘
└───────────────┘               │
        │                       │
        ▼                       │
┌────────────────────────┐      │
│ NotificationPreference │      │
├────────────────────────┤      │
│ id                     │      │
│ client_id              │      │
│ email_enabled          │      │
│ sms_enabled            │      │
│ whatsapp_enabled       │      │
│ reminder_24h           │      │
│ reminder_2h            │      │
│ timezone               │      │
└────────────────────────┘      │
                                ▼
┌────────────────┐      ┌───────────────────┐
│ BlockedSchedule │      │    Reminder      │
├────────────────┤      ├───────────────────┤
│ id             │      │ id                │
│ start_time     │      │ appointment_id    │
│ end_time       │      │ scheduled_time    │
│ reason         │      │ sent              │
└────────────────┘      │ message           │
                        └───────────────────┘
```

### Database Tables Description

#### Client Table
Stores information about salon clients.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each client |
| email | String | Unique email address | Used for authentication and notifications |
| full_name | String | Client's full name | Used for personalized communication |
| phone | String | Phone number | Used for SMS and WhatsApp notifications |
| hashed_password | String | Secure password hash | Enables client authentication |
| is_active | Boolean | Account status | Controls whether client can use the system |
| is_admin | Boolean | Admin privileges | Determines access to administrative features |
| created_at | DateTime | Creation timestamp | For auditing and analytics |
| updated_at | DateTime | Last update timestamp | For auditing and analytics |

#### Service Table
Catalogues the services offered by the salon.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each service |
| name | String | Service name | Displayed to clients during booking |
| description | String | Detailed description | Provides additional information about the service |
| price | Decimal | Service cost | Used for invoicing and financial reporting |
| duration_minutes | Integer | Time required | Used for scheduling and availability management |
| is_active | Boolean | Service availability | Controls whether service can be booked |

#### Appointment Table
Central table for managing salon bookings.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each appointment |
| client_id | Integer | Foreign key | Links to the client who booked the appointment |
| service_id | Integer | Foreign key | Links to the service being provided |
| date_time | DateTime | Appointment time | When the service is scheduled |
| status | Enum | Current status | Tracks appointment lifecycle (pending, confirmed, completed, cancelled) |
| notes | String | Additional information | Special requests or staff notes |
| created_at | DateTime | Creation timestamp | For auditing and analytics |
| updated_at | DateTime | Last update timestamp | For auditing and analytics |

#### NotificationPreference Table
Stores client communication preferences.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for preferences |
| client_id | Integer | Foreign key | Links to the client |
| email_enabled | Boolean | Email notifications | Whether to send email notifications |
| sms_enabled | Boolean | SMS notifications | Whether to send SMS notifications |
| whatsapp_enabled | Boolean | WhatsApp notifications | Whether to send WhatsApp notifications |
| reminder_24h | Boolean | 24-hour reminders | Whether to send 24-hour advance reminders |
| reminder_2h | Boolean | 2-hour reminders | Whether to send 2-hour advance reminders |
| timezone | String | Client's timezone | For sending notifications at appropriate local times |

#### BlockedSchedule Table
Records times when the salon cannot accept appointments.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each blocked period |
| start_time | DateTime | Start of blocked period | When unavailability begins |
| end_time | DateTime | End of blocked period | When availability resumes |
| reason | String | Explanation | Why the time is blocked (holidays, maintenance, etc.) |

#### Reminder Table
Tracks appointment reminders.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each reminder |
| appointment_id | Integer | Foreign key | Links to the appointment |
| scheduled_time | DateTime | When to send | When the reminder should be sent |
| sent | Boolean | Delivery status | Whether the reminder has been sent |
| message | String | Reminder content | Customized message for the client |

#### SentReminder Table
Records details of reminders that have been sent.

| Field | Type | Description | Motivation |
|-------|------|-------------|------------|
| id | Integer | Primary key | Unique identifier for each sent reminder |
| appointment_id | Integer | Foreign key | Links to the appointment |
| message | Text | Reminder content | What was communicated to the client |
| sent_at | DateTime | Timestamp | When the reminder was sent |
| status | Enum | Delivery status | Tracking of message delivery (sent, delivered, failed, read) |
| channel | String | Communication method | Which channel was used (email, SMS, WhatsApp) |
| recipient | String | Contact info | Where the reminder was sent |
| external_id | String | Provider reference | Reference ID from external service (e.g., Twilio) |

## Core Components

### Authentication System

**Purpose**: The authentication system provides secure access control to the application, differentiating between client and administrator accounts.

**Key Files**:
- `app/core/security.py`: Central security utilities
- `app/api/v1/endpoints/auth.py`: Authentication endpoints
- `app/services/auth.py`: Authentication business logic

**Features**:
- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- Refresh token functionality
- Rate limiting for login attempts

**Development Rationale**:
The authentication system was designed with security as the primary concern while maintaining a smooth user experience. JWTs were chosen for their stateless nature and compatibility with modern frontend applications. The system implements industry best practices including password hashing, token expiration, and protection against brute force attacks.

### Appointment Management

**Purpose**: The appointment management system is the core functionality of the application, handling the creation, modification, and tracking of client appointments.

**Key Files**:
- `app/models/appointment.py`: Database models for appointments
- `app/api/v1/endpoints/appointments.py`: Appointment-related API endpoints
- `app/services/appointment_service.py`: Business logic for appointments
- `app/services/cita.py`: Spanish alias for backwards compatibility

**Features**:
- Appointment creation with conflict detection
- Rescheduling and cancellation
- Status tracking (pending, confirmed, completed, cancelled, no-show)
- Customizable appointment notes
- Client appointment history

**Development Rationale**:
The appointment system was developed to provide a flexible yet robust scheduling solution. Key challenges included handling timezone differences, preventing double-bookings, and ensuring proper resource allocation. The design allows for future extensions such as staff assignment and resource management.

### Notification System

**Purpose**: The notification system keeps clients informed about their appointments through multiple communication channels.

**Key Files**:
- `app/services/notification_service.py`: Core notification logic
- `app/services/reminder_service.py`: Appointment reminder processing
- `app/services/recordatorio.py`: Spanish alias for backwards compatibility
- `app/tasks/scheduler.py`: Scheduled reminder tasks

**Features**:
- Multi-channel notifications (Email, SMS, WhatsApp)
- Customizable notification templates
- Client notification preferences
- Scheduled reminders (24 hours and 2 hours before appointments)
- Notification delivery tracking

**Development Rationale**:
The notification system was designed to reduce appointment no-shows, which was identified as a major pain point for salon businesses. Research indicated that timely reminders significantly increase attendance rates. The system respects client preferences and local time zones to ensure notifications are received at appropriate times.

**Internationalization Support**:
The application includes both English and Spanish versions of the service files to support multilingual businesses. This was implemented using alias patterns to maintain backward compatibility during the transition.

### Service Management

**Purpose**: The service management component allows the salon to manage their service offerings, including pricing, duration, and availability.

**Key Files**:
- `app/models/service.py`: Service catalog model
- `app/api/v1/endpoints/services.py`: Service management endpoints
- `app/services/service_service.py`: Business logic for services

**Features**:
- Service catalog management
- Pricing and duration configuration
- Service activation/deactivation
- Service categorization
- Service analytics

**Development Rationale**:
Services are the core offerings of a salon business. This component was designed to provide flexibility in managing service details while maintaining data consistency for scheduling and reporting. The separation between active and inactive services allows seasonal or temporary offerings without affecting historical data.

### Scheduling System

**Purpose**: The scheduling system manages salon availability and optimizes appointment allocation.

**Key Files**:
- `app/services/blocked_schedule_service.py`: Manage unavailable time periods
- `app/services/horario_bloqueado.py`: Spanish alias for backwards compatibility

**Features**:
- Business hours management
- Holiday and closure tracking
- Time block reservation
- Availability checking
- Intelligent scheduling suggestions

**Development Rationale**:
Effective scheduling is critical for maximizing salon revenue and staff utilization. The scheduling system considers business hours, blocked periods, existing appointments, and service duration to determine availability. This component was designed to be extensible for future features such as staff-specific scheduling and resource allocation.

## API Documentation

The API follows RESTful principles and is organized by resource types. All endpoints are prefixed with `/api/v1/`.

### Authentication Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/auth/login` | POST | Authenticate a user and return access token | Public |
| `/api/v1/auth/register` | POST | Register a new client | Public |
| `/api/v1/auth/refresh` | POST | Refresh an access token | Requires refresh token |

### Client Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/clients` | GET | List all clients | Admin only |
| `/api/v1/clients/{client_id}` | GET | Get client details | Admin or own client |
| `/api/v1/clients` | POST | Create a new client | Admin only |
| `/api/v1/clients/{client_id}` | PUT | Update client information | Admin or own client |

### Appointment Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/appointments` | GET | List appointments with filters | Admin only |
| `/api/v1/appointments/{appointment_id}` | GET | Get appointment details | Admin or client of appointment |
| `/api/v1/appointments` | POST | Create a new appointment | Authenticated |
| `/api/v1/appointments/{appointment_id}` | PUT | Update appointment | Admin or client of appointment |
| `/api/v1/appointments/{appointment_id}/cancel` | POST | Cancel appointment | Admin or client of appointment |
| `/api/v1/appointments/{appointment_id}/confirm` | POST | Confirm appointment | Admin only |
| `/api/v1/appointments/{appointment_id}/complete` | POST | Mark appointment as completed | Admin only |
| `/api/v1/appointments/{appointment_id}/no-show` | POST | Mark client as no-show | Admin only |

### Service Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/services` | GET | List all services | Public |
| `/api/v1/services/{service_id}` | GET | Get service details | Public |
| `/api/v1/services` | POST | Create a new service | Admin only |
| `/api/v1/services/{service_id}` | PUT | Update service | Admin only |
| `/api/v1/services/{service_id}` | DELETE | Delete service | Admin only |

### Availability Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/availability` | GET | Check available time slots | Public |
| `/api/v1/blocked-schedule` | GET | List blocked time periods | Admin only |
| `/api/v1/blocked-schedule` | POST | Create a blocked period | Admin only |
| `/api/v1/blocked-schedule/{id}` | DELETE | Remove a blocked period | Admin only |

### Notification Endpoints

| Endpoint | Method | Description | Authorization |
|----------|--------|-------------|---------------|
| `/api/v1/notification-preferences/{client_id}` | GET | Get client notification preferences | Admin or own client |
| `/api/v1/notification-preferences/{client_id}` | PUT | Update notification preferences | Admin or own client |

## Development Workflow

### Project Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd salon-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with appropriate values
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Create an admin user:
   ```bash
   python create_admin.py
   ```

7. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Development Standards

- **Code Style**: The project follows PEP 8 style guidelines
- **Documentation**: All functions, classes, and modules have docstrings
- **Testing**: Unit tests are required for all new functionality
- **Git Workflow**: Feature branch workflow with pull requests
- **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH)

### Testing Strategy

The application employs multiple testing approaches:

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test interactions between components
3. **API Tests**: Test API endpoints with realistic scenarios
4. **End-to-End Tests**: Test complete workflows

To run tests:
```bash
pytest
```

For test coverage:
```bash
pytest --cov=app
```

## Deployment Guide

The application supports multiple deployment methods:

### Docker Deployment (Recommended)

1. Configure environment:
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with production values
   ```

2. Build and start containers:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. Run migrations:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

4. Create admin user (if needed):
   ```bash
   docker-compose exec web python create_admin.py
   ```

### Traditional VM Deployment

See detailed instructions in [DEPLOYMENT.md](../DEPLOYMENT.md).

## Monitoring and Maintenance

### Health Checks

The application provides health check endpoints:
- `/api/health`: Basic application status
- `/api/health/detailed`: Detailed component status including database and external services

### Monitoring

Prometheus is used for metrics collection, with the following key metrics:
- Request rates and response times
- Database query performance
- External service availability
- Background task execution

Grafana dashboards visualize these metrics and provide alerting capabilities.

### Logging

The application uses structured logging with configurable levels:
- ERROR: Critical issues requiring immediate attention
- WARNING: Potential issues that might need investigation
- INFO: Normal operation information
- DEBUG: Detailed information for debugging

Logs are written to files and stdout for container environments.

### Backup Strategy

Regular database backups are essential:
1. Automated daily backups
2. Retention policy for managing backup storage
3. Backup verification process
4. Restore testing procedures

## Troubleshooting

### Common Issues

#### Authentication Problems
- Check JWT secret and algorithm configuration
- Verify password hashing method
- Inspect token expiration settings

#### Database Connection Issues
- Check database URL configuration
- Verify database service is running
- Inspect database logs for errors

#### Notification Failures
- Check external service credentials (Twilio)
- Verify client contact information
- Inspect notification service logs

#### Performance Problems
- Check database indexing
- Review slow query logs
- Inspect caching configuration

### Debugging Techniques

1. Enable debug logging:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Use API debugging endpoints (admin only):
   - `/api/debug/config`: View application configuration
   - `/api/debug/cache`: Inspect cache contents
   - `/api/debug/tasks`: View scheduled task status

3. Database inspection:
   ```bash
   docker-compose exec db psql -U postgres salon_assistant
   ```

## Future Enhancements

### Planned Features

1. **Staff Management**:
   - Staff profiles and specializations
   - Staff-specific scheduling
   - Performance analytics

2. **Client Loyalty Program**:
   - Points system for appointments
   - Reward redemption
   - Automated loyalty communications

3. **Inventory Management**:
   - Product tracking
   - Usage per service
   - Low stock alerts

4. **Mobile Application**:
   - Native mobile experience
   - Push notifications
   - Offline capabilities

5. **Advanced Analytics**:
   - Predictive booking patterns
   - Revenue forecasting
   - Client lifecycle analysis

### Architectural Improvements

1. **Microservices Evolution**:
   - Split into domain-specific services
   - API gateway implementation
   - Service discovery

2. **Real-time Features**:
   - WebSocket implementation
   - Live dashboard updates
   - Instant notifications

3. **Advanced Caching**:
   - Distributed caching layer
   - Intelligent cache invalidation
   - Edge caching

---

This documentation was created to provide a comprehensive understanding of the Salon Assistant system. It should be kept up-to-date as the system evolves and new features are added. 