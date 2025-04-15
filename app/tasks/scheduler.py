"""
Scheduler for running recurring tasks like reminder processing.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.reminder_service import ReminderService

logger = logging.getLogger("app.tasks.scheduler")

class TaskScheduler:
    """
    Scheduler for handling periodic tasks like reminder processing.
    """
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.scheduler = None
    
    def start(self):
        """Start the scheduler with the configured jobs."""
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
            
        # Configure the scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        # Create and configure scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        
        # Add reminder processing job (runs every 5 minutes)
        self.scheduler.add_job(
            self.process_reminders,
            'interval',
            minutes=5,
            id='process_reminders',
            replace_existing=True
        )
        
        # Start the scheduler
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
    
    def shutdown(self):
        """Shut down the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
    
    async def process_reminders(self):
        """
        Process pending reminders.
        This job runs periodically to check for and send pending appointment reminders.
        """
        logger.info(f"Processing reminders at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        db = SessionLocal()
        try:
            reminder_service = ReminderService(db)
            reminders_processed = reminder_service.process_pending_reminders()
            logger.info(f"Processed {reminders_processed} reminders")
        except Exception as e:
            logger.error(f"Error processing reminders: {str(e)}")
        finally:
            db.close()

# Create a singleton scheduler instance
scheduler = TaskScheduler() 