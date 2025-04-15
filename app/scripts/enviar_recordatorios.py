"""
Script to send appointment reminders
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from app.core.config import settings
from app.db.database import async_session_maker
from app.services.reminder_service import ReminderService

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

async def send_reminders():
    """Main function to send reminders"""
    start_time = datetime.now()
    logger.info("Starting reminder sending process")
    
    try:
        async with async_session_maker() as db:
            # Send reminders
            results = await ReminderService.send_reminders(db)
            
            # Get statistics for the last 24 hours
            end_time = datetime.now()
            stats = await ReminderService.get_reminder_statistics(
                db,
                start_date=end_time - timedelta(hours=24),
                end_date=end_time
            )
            
            # Calculate duration
            duration = (end_time - start_time).total_seconds()
            
            # Prepare summary
            summary = {
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration,
                "reminders_sent": results,
                "statistics_24h": stats
            }
            
            # Show summary
            logger.info("Reminder sending summary:")
            logger.info(json.dumps(summary, indent=2))
            
            # Check if there were few reminders
            total_sent = sum(results.values())
            if total_sent == 0:
                logger.warning(
                    "No reminders were sent. "
                    "Check that there are scheduled appointments and that clients have notification preferences configured."
                )
            elif total_sent < 5:  # Arbitrary threshold
                logger.warning(
                    f"Few reminders were sent ({total_sent}). "
                    "Check that notification preferences are configured correctly."
                )
                
    except Exception as e:
        logger.error(f"Error al enviar recordatorios: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(send_reminders())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise 