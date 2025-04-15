"""
Script to create a default admin user
"""
import os
from pathlib import Path
import sys

# Add the project root to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user():
    """Create a default admin user if none exists"""
    print(f"Using database URL: {settings.DATABASE_URL}")
    
    # Create a SQLAlchemy engine
    engine = create_engine(
        settings.DATABASE_URL, 
        echo=True  # Set to True to see SQL statements
    )
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if an admin user already exists
        admin = db.query(User).filter(User.is_admin == True).first()
        
        if admin:
            print(f"Admin user already exists: {admin.email}")
        else:
            # Create a default admin user
            admin_user = User(
                email="admin@salonassistant.com",
                full_name="Admin User",
                phone="+1-555-123-4567",
                hashed_password=get_password_hash("adminpassword"),
                is_active=True,
                is_admin=True,
                is_superuser=True
            )
            
            db.add(admin_user)
            db.commit()
            print(f"Admin user created: {admin_user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 