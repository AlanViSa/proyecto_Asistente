"""
Script to create all database tables
"""
import os
from pathlib import Path
import sys

# Add the project root to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from sqlalchemy import create_engine
from app.core.config import settings
from app.db.database import Base

# Import models - these imports will register with the Base metadata
models_to_import = [
    "app.models.client",
    "app.models.user",
    "app.models.appointment",
    "app.models.service",
    "app.models.reminder",
    "app.models.notification_preference",
    "app.models.blocked_schedule",
    "app.models.health"
]

# Import the models that exist
for model in models_to_import:
    try:
        __import__(model)
        print(f"Successfully imported {model}")
    except ImportError as e:
        print(f"Warning: Could not import {model}: {e}")

def init_db():
    """Initialize the database by creating all tables"""
    print(f"Using database URL: {settings.DATABASE_URL}")
    
    # Create a folder for the database if it's SQLite
    if "sqlite" in settings.DATABASE_URL and "///" in settings.DATABASE_URL:
        db_path = settings.DATABASE_URL.split("///")[1]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    # Create a SQLAlchemy engine
    engine = create_engine(
        settings.DATABASE_URL, 
        echo=True  # Set to True to see SQL statements
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("All tables created successfully!")

if __name__ == "__main__":
    init_db() 