# Sistema de Recordatorios Automáticos

Este sistema se encarga de enviar recordatorios automáticos a los clientes sobre sus citas programadas.

## Configuración

### Windows

1. Abrir PowerShell como administrador
2. Navegar al directorio del proyecto
3. Ejecutar el script de configuración:
   ```powershell
   .\scripts\setup_task.ps1
   ```

### Linux/Mac

1. Abrir terminal
2. Navegar al directorio del proyecto
3. Hacer el script ejecutable:
   ```bash
   chmod +x scripts/setup_cron.sh
   ```
4. Ejecutar el script de configuración:
   ```bash
   ./scripts/setup_cron.sh
   ```

## Monitoreo

Los logs se guardan en el directorio `logs/recordatorios.log`.

### Windows
Para ver los logs en tiempo real:
```powershell
Get-Content logs/recordatorios.log -Wait
```

### Linux/Mac
Para ver los logs en tiempo real:
```bash
tail -f logs/recordatorios.log
```

## Configuración de Recordatorios

Los recordatorios están configurados para enviarse:
- 24 horas antes de la cita
- 2 horas antes de la cita

Para modificar estos tiempos, editar la constante `RECORDATORIOS` en `app/services/recordatorio.py`.

## Canales de Notificación

Los recordatorios se envían a través de:
- Email
- SMS (requiere configuración de Twilio)
- WhatsApp (requiere configuración de WhatsApp Business API)

## Solución de Problemas

1. Si los recordatorios no se están enviando:
   - Verificar que la tarea programada está activa
   - Revisar los logs en busca de errores
   - Comprobar la configuración de los servicios de notificación

2. Si hay errores de conexión:
   - Verificar la configuración de la base de datos
   - Comprobar las credenciales de los servicios de notificación

3. Si los recordatorios se envían en momentos incorrectos:
   - Verificar la zona horaria del sistema
   - Comprobar la configuración de la tarea programada

### Preferencias de Notificación

Cada cliente puede personalizar sus preferencias de notificación:

1. **Canales de Notificación**
   - Email (habilitado por defecto)
   - SMS (opcional)
   - WhatsApp (opcional)

2. **Tipos de Recordatorio**
   - Recordatorio 24 horas antes (habilitado por defecto)
   - Recordatorio 2 horas antes (habilitado por defecto)

3. **Zona Horaria**
   - Por defecto: America/Mexico_City
   - Personalizable para cada cliente

### Gestión de Preferencias

Las preferencias se pueden gestionar a través de la API:

1. **Obtener Preferencias**
   ```http
   GET /api/v1/preferencias-notificacion/{cliente_id}
   ```

2. **Crear/Actualizar Preferencias**
   ```http
   POST /api/v1/preferencias-notificacion
   PUT /api/v1/preferencias-notificacion/{cliente_id}
   ```

3. **Crear Preferencias por Defecto**
   ```http
   POST /api/v1/preferencias-notificacion/{cliente_id}/default
   ```

## Canales de Notificación

### Email
- Configurado y funcional
- Requiere dirección de email válida del cliente
- Usa plantillas HTML personalizadas

### SMS (Próximamente)
- En desarrollo
- Requerirá configuración adicional del proveedor de SMS
- Necesita número de teléfono válido del cliente

### WhatsApp (Próximamente)
- En desarrollo
- Requerirá configuración de la API de WhatsApp Business
- Necesita número de teléfono válido del cliente

## Solución de Problemas

1. Si los recordatorios no se están enviando:
   - Verificar que el servicio está ejecutándose:
     - Windows: Task Scheduler
     - Linux/Mac: `crontab -l`
   - Revisar los logs en busca de errores
   - Verificar que los clientes tienen preferencias configuradas
   - Comprobar que hay citas programadas en el rango de tiempo

2. Si hay errores de conexión:
   - Verificar la configuración de la base de datos
   - Comprobar las credenciales de los servicios de notificación

3. Si los recordatorios se envían en momentos incorrectos:
   - Verificar la zona horaria del sistema
   - Comprobar la configuración de la tarea programada

### Comandos Útiles

1. **Verificar estado de la tarea programada**
   - Windows:
     ```powershell
     Get-ScheduledTask -TaskName "EnviarRecordatoriosCitas" | Get-ScheduledTaskInfo
     ```
   - Linux/Mac:
     ```bash
     crontab -l | grep enviar_recordatorios
     ```

2. **Ejecutar manualmente**
   ```bash
   python app/scripts/enviar_recordatorios.py
   ```

3. **Limpiar logs antiguos**
   - Windows:
     ```powershell
     Get-ChildItem .\logs\recordatorios.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
     ```
   - Linux/Mac:
     ```bash
     find logs -name "recordatorios.log" -mtime +30 -delete
     ``` 