"""
Script para enviar recordatorios de citas
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.db.database import async_session_maker
from app.services.recordatorio import RecordatorioService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/recordatorios.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Función principal para enviar recordatorios"""
    inicio = datetime.now()
    logger.info("Iniciando envío de recordatorios")
    
    try:
        async with async_session_maker() as db:
            # Enviar recordatorios
            resultados = await RecordatorioService.enviar_recordatorios(db)
            
            # Obtener estadísticas de las últimas 24 horas
            fin = datetime.now()
            stats = await RecordatorioService.get_estadisticas_recordatorios(
                db,
                fecha_inicio=fin - timedelta(hours=24),
                fecha_fin=fin
            )
            
            # Calcular duración
            duracion = (fin - inicio).total_seconds()
            
            # Preparar resumen
            resumen = {
                "inicio": inicio.strftime("%Y-%m-%d %H:%M:%S"),
                "fin": fin.strftime("%Y-%m-%d %H:%M:%S"),
                "duracion_segundos": duracion,
                "recordatorios_enviados": resultados,
                "estadisticas_24h": stats
            }
            
            # Mostrar resumen
            logger.info("Resumen de envío de recordatorios:")
            logger.info(json.dumps(resumen, indent=2))
            
            # Verificar si hay pocos recordatorios
            total_enviados = sum(resultados.values())
            if total_enviados == 0:
                logger.warning(
                    "No se enviaron recordatorios. "
                    "Verifica que haya citas programadas y que los clientes tengan preferencias configuradas."
                )
            elif total_enviados < 5:  # Umbral arbitrario
                logger.warning(
                    f"Se enviaron pocos recordatorios ({total_enviados}). "
                    "Verifica que las preferencias de notificación estén configuradas correctamente."
                )
                
    except Exception as e:
        logger.error(f"Error al enviar recordatorios: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")
        raise 