# Salon Assistant Application - Naming Standardization

## Overview

This document outlines the naming conventions and standardization approach used in the Salon Assistant application. The project has transitioned from a mix of Spanish and English naming to a consistent English-based naming scheme, while maintaining backward compatibility.

## Naming Conventions

### Models

All models use English names with PascalCase:
- `Client` - Client information (previously also referred to as "Cliente")
- `Appointment` - Appointment scheduling (previously also referred to as "Cita")
- `Service` - Salon services (previously also referred to as "Servicio") 
- `Reminder` - Appointment reminders (previously also referred to as "Recordatorio")
- `BlockedSchedule` - Blocked time periods (previously also referred to as "HorarioBloqueado")
- `NotificationPreference` - Client notification preferences (previously also referred to as "PreferenciaNotificacion")
- `SentReminder` - Record of sent reminders (previously also referred to as "RecordatorioEnviado")
- `HealthCheck` - System health monitoring

### Services

Services use English names with PascalCase and "Service" suffix:
- `ClientService` - Client management operations
- `AppointmentService` - Appointment scheduling and management
- `ReminderService` - Reminder processing and sending
- `ServiceService` - Salon service management
- `AuthService` - Authentication and authorization
- `NotificationService` - Multi-channel notification sending
- `BlockedScheduleService` - Availability management
- `NotificationPreferenceService` - Client preference management
- `HealthService` - System monitoring and reporting

### API Endpoints

API endpoints use REST conventions with resources in plural form:
- `/clients` - Client management
- `/appointments` - Appointment scheduling
- `/services` - Salon service management
- `/reminders` - Reminder management
- `/blocked-schedules` - Availability management
- `/notification-preferences` - Notification preference management
- `/auth` - Authentication endpoints

## Backward Compatibility

To maintain backward compatibility during the transition, the following mechanisms are in place:

1. **Model Aliases**: Spanish-named model aliases are provided in `app/models/__init__.py`
   ```python
   # Example:
   Cliente = Client
   Cita = Appointment
   ```

2. **Service Aliases**: Spanish-named service aliases are provided in `app/services/__init__.py`
   ```python
   # Example:
   ClienteService = ClientService
   CitaService = AppointmentService
   ```

3. **Compatibility Files**: Legacy Spanish-named files now serve as aliases to their English counterparts:
   ```python
   # app/services/cliente.py
   from app.services.client_service import ClientService
   
   # Create Spanish alias for the service
   ClienteService = ClientService
   ```

4. **Enum Aliases**: For enumeration types, Spanish equivalents are provided:
   ```python
   # Example from notification.py
   class CanalNotificacion(str, Enum):
       EMAIL = NotificationChannel.EMAIL.value
       SMS = NotificationChannel.SMS.value
       WHATSAPP = NotificationChannel.WHATSAPP.value
   ```

5. **Import-All Support**: Both `__init__.py` files export all model and service names in their `__all__` lists.

## Migration Guide

When working with the codebase, please follow these guidelines:

1. For new code, always use the English naming conventions.
2. When modifying existing code, update to English naming where practical.
3. Import models and services through the package imports when possible:
   ```python
   # Preferred:
   from app.models import Client, Appointment
   from app.services import ClientService, AppointmentService
   
   # Instead of direct imports:
   from app.models.client import Client
   from app.services.client_service import ClientService
   ```

4. When maintaining compatibility is required, use the standardized aliases:
   ```python
   from app.models import Cliente  # Alias for Client
   from app.services import ClienteService  # Alias for ClientService
   ```

## Implementation Pattern

The standardization follows these implementation patterns:

1. **English Service File**: Contains the full implementation with English naming
   ```python
   # app/services/client_service.py
   class ClientService:
       """Service for client-related operations"""
       # ... implementation ...
   ```

2. **Spanish Alias File**: Contains only import and aliasing
   ```python
   # app/services/cliente.py
   from app.services.client_service import ClientService
   ClienteService = ClientService
   # Additional imports for backward compatibility
   ```

3. **Common Import Pattern**: Use the package imports
   ```python
   # Preferred pattern
   from app.services import ClientService, AppointmentService
   ```

## Documentation

All new docstrings and comments should be written in English to maintain consistency with the naming standards. Existing Spanish docstrings can remain as-is in legacy files, but any updates should transition to English.

## File Organization

With the standardization, files are organized as follows:

1. **English Implementation Files**:
   - Located in their appropriate directories (`app/models/`, `app/services/`, etc.)
   - Contains full implementation with English naming

2. **Spanish Compatibility Files**:
   - Located in the same directories, retaining their original names
   - Serve as thin wrappers that import and alias the English implementations

3. **Central Import Modules**:
   - `app/models/__init__.py` - Exposes all models with both English and Spanish names
   - `app/services/__init__.py` - Exposes all services with both English and Spanish names 