#!/usr/bin/env python3
"""
Script to perform automatic database backup
"""
import os
import subprocess
from datetime import datetime
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler(),
    ],
)


def create_backup():
    """Creates a database backup"""
    try:
        # Create backup directory if it does not exist
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        # Get environment variables
        db_name = os.getenv("POSTGRES_DB", "salon_assistant")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        db_host = os.getenv("POSTGRES_HOST", "localhost")

        # Create backup file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.sql"

        # Create backup using pg_dump
        cmd = [
            "pg_dump",
            "-h",
            db_host,
            "-U",
            db_user,
            "-d",
            db_name,
            "-f",
            str(backup_file),
        ]

        # Set password as environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        # Execute command
        subprocess.run(cmd, env=env, check=True)

        # Compress backup
        subprocess.run(["gzip", str(backup_file)], check=True)

        logging.info(f"Backup created successfully: {backup_file}.gz")

        # Delete old backups (keep last 7 days)
        cleanup_old_backups(backup_dir)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error creating backup: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def cleanup_old_backups(backup_dir):
    """Deletes backups older than 7 days"""
    try:
        # Get all .gz files in the backup directory
        backup_files = list(backup_dir.glob("*.gz"))

        # Sort by modification date
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Keep only the last 7 days
        for old_file in backup_files[7:]:
            old_file.unlink()
            logging.info(f"Old backup deleted: {old_file}")

    except Exception as e:
        logging.error(f"Error cleaning up old backups: {e}")


if __name__ == '__main__':
    create_backup()