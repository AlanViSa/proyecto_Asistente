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
| app/services/cita.py | app/services/appointment_service.py | ✅ English exists |
| app/services/cliente.py | app/services/client_service.py | ❌ Create English version |
| app/services/horario_bloqueado.py | app/services/blocked_schedule_service.py | ✅ English exists |
| app/services/preferencias_notificacion.py | app/services/notification_preference_service.py | ❌ Create English version |
| app/services/recordatorio.py | app/services/reminder_service.py | ✅ English exists |

### API Endpoints

| Spanish File | English Replacement | Status |
|--------------|---------------------|--------|
| app/api/endpoints/citas.py | app/api/v1/endpoints/appointments.py | ✅ English exists |
| app/api/endpoints/clientes.py | app/api/v1/endpoints/clients.py | ✅ English exists |

## Implementation Plan

1. Create missing English files
2. Update all imports across the codebase
3. Delete all Spanish files
4. Test the application thoroughly 