# Salon Assistant Standardization Plan

This document outlines the plan to standardize all codebase components to English, removing Spanish-named files.

## File Mappings

### Models

| Spanish File | English Replacement | Status |
|--------------|---------------------|--------|
| app/models/cliente.py | app/models/client.py | ✅ English exists |
| app/models/cita.py | app/models/appointment.py | ✅ English exists |

### Services

| Spanish File | English Replacement | Status |
|--------------|---------------------|--------|
| app/services/cita.py | app/services/appointment_service.py | ✅ English exists, alias created |
| app/services/cliente.py | app/services/client_service.py | ✅ English exists, alias created |
| app/services/horario_bloqueado.py | app/services/blocked_schedule_service.py | ✅ English exists, alias created |
| app/services/preferencias_notificacion.py | app/services/notification_preference_service.py | ✅ English exists, alias created |
| app/services/recordatorio.py | app/services/reminder_service.py | ✅ English exists, alias created |
| app/services/notification.py | app/services/notification_service.py | ✅ English exists, alias created |
| N/A | app/services/service_service.py | ✅ English created |

### API Endpoints

| Spanish File | English Replacement | Status |
|--------------|---------------------|--------|
| app/api/endpoints/citas.py | app/api/v1/endpoints/appointments.py | ✅ English exists |
| app/api/endpoints/clientes.py | app/api/v1/endpoints/clients.py | ✅ English exists |

## Implementation Plan

1. ✅ Create missing English files
2. ✅ Update all imports across the codebase
3. 🔄 Create compatibility alias files for Spanish services
4. ⏳ Test the application thoroughly 

## Summary of Changes Made

1. Created standardized English versions of all service files:
   - `app/services/client_service.py`
   - `app/services/appointment_service.py`
   - `app/services/reminder_service.py`
   - `app/services/notification_preference_service.py`
   - `app/services/blocked_schedule_service.py`
   - `app/services/notification_service.py`
   - `app/services/service_service.py`

2. Created compatibility alias files for all Spanish service files:
   - `app/services/cliente.py` → Alias to `ClientService`
   - `app/services/cita.py` → Alias to `AppointmentService`
   - `app/services/recordatorio.py` → Alias to `ReminderService`
   - `app/services/preferencias_notificacion.py` → Alias to `NotificationPreferenceService`
   - `app/services/horario_bloqueado.py` → Alias to `BlockedScheduleService`
   - `app/services/notification.py` → Alias to `NotificationService`

3. Added standardized import support in package __init__ files:
   - `app/models/__init__.py` - Added model aliases
   - `app/services/__init__.py` - Added service aliases

4. Updated API endpoints to use English service names:
   - `app/api/deps.py` - Updated dependencies to use English models and services
   - `app/api/v1/endpoints/clients.py` - Updated to use `ClientService`

5. Created documentation:
   - `STANDARDIZATION.md` - Guidelines and best practices for standardization 