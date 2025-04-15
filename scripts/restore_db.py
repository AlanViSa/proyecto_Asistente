#!/usr/bin/env python3
import os
import subprocess
import sys
import logging
from pathlib import Path
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)

def list_backups() -> list[Path]:
    """Lists available backups"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        logging.error("Backups directory not found")
        return []
    
    backups = sorted(backup_dir.glob('backup_*.sql.gz'), reverse=True)
    return backups

def restore_backup(backup_file):
    """Restores the database from a backup file"""
    try:
        # Get environment variables
        db_name = os.getenv('POSTGRES_DB', 'salon_assistant')
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        
        # Decompress backup
        uncompressed_file = backup_file.with_suffix('')
        subprocess.run(['gunzip', '-k', str(backup_file)], check=True)
        
        # Restore backup
        cmd = [
            'psql',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(uncompressed_file)
        ]
        
        # Set password as environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Execute command
        subprocess.run(cmd, env=env, check=True)
        
        # Delete uncompressed file
        uncompressed_file.unlink()
        
        logging.info(f'Backup successfully restored from: {backup_file}')
        
    except subprocess.CalledProcessError as e:
        logging.error(f'Error restoring backup: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        raise

def main():
    if len(sys.argv) > 1:
        # Si se proporciona un archivo específico
        backup_file = Path(sys.argv[1])
        if not backup_file.exists():
            logging.error(f"Backup file not found: {backup_file}")
            sys.exit(1)
        restore_backup(backup_file)
    else:
        # List available backups
        backups = list_backups()
        if not backups:
            logging.error("No backups available")
            sys.exit(1)
            
        print("\nAvailable Backups:")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup.name}")
            
        try:
            choice = int(input("\nSelect the number of the backup to restore: "))
            if 1 <= choice <= len(backups):
                restore_backup(backups[choice-1])
            else:
                logging.error("Invalid selection")
                sys.exit(1)
        except ValueError:
            logging.error("Please enter a valid number")
            sys.exit(1)

if __name__ == '__main__':
    main() 