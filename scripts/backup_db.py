"""
Script para realizar backup automático de la base de datos
"""
#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

def create_backup():
    """
    Crea un backup de la base de datos
    """
    try:
        # Crear directorio de backups si no existe
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        # Obtener variables de entorno
        db_name = os.getenv('POSTGRES_DB', 'salon_assistant')
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        
        # Crear nombre del archivo de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'backup_{timestamp}.sql'
        
        # Crear backup usando pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(backup_file)
        ]
        
        # Establecer contraseña como variable de entorno
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Ejecutar comando
        subprocess.run(cmd, env=env, check=True)
        
        # Comprimir backup
        subprocess.run(['gzip', str(backup_file)], check=True)
        
        logging.info(f'Backup creado exitosamente: {backup_file}.gz')
        
        # Eliminar backups antiguos (mantener últimos 7 días)
        cleanup_old_backups(backup_dir)
        
    except subprocess.CalledProcessError as e:
        logging.error(f'Error al crear backup: {e}')
        raise
    except Exception as e:
        logging.error(f'Error inesperado: {e}')
        raise

def cleanup_old_backups(backup_dir):
    """Elimina backups más antiguos de 7 días"""
    try:
        # Obtener todos los archivos .gz en el directorio de backups
        backup_files = list(backup_dir.glob('*.gz'))
        
        # Ordenar por fecha de modificación
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Mantener solo los últimos 7 días
        for old_file in backup_files[7:]:
            old_file.unlink()
            logging.info(f'Backup antiguo eliminado: {old_file}')
            
    except Exception as e:
        logging.error(f'Error al limpiar backups antiguos: {e}')

if __name__ == '__main__':
    create_backup() 