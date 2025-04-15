"""
Alias for BlockedScheduleService for backwards compatibility
"""
from app.services.blocked_schedule_service import BlockedScheduleService

# Create Spanish alias for the service
HorarioBloqueadoService = BlockedScheduleService

# Alias for the main method with Spanish naming
is_horario_bloqueado = BlockedScheduleService.is_time_blocked