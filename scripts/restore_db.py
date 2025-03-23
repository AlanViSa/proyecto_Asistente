#!/usr/bin/env python3
import os
import subprocess
import sys
import logging
from pathlib import Path
import glob

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)

def list_backups():
    """Lista los backups disponibles"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        logging.error("No se encontró el directorio de backups")
        return []
    
    backups = sorted(backup_dir.glob('backup_*.sql.gz'), reverse=True)
    return backups

def restore_backup(backup_file):
    """Restaura la base de datos desde un archivo de backup"""
    try:
        # Obtener variables de entorno
        db_name = os.getenv('POSTGRES_DB', 'salon_assistant')
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        
        # Descomprimir backup
        uncompressed_file = backup_file.with_suffix('')
        subprocess.run(['gunzip', '-k', str(backup_file)], check=True)
        
        # Restaurar backup
        cmd = [
            'psql',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(uncompressed_file)
        ]
        
        # Establecer contraseña como variable de entorno
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Ejecutar comando
        subprocess.run(cmd, env=env, check=True)
        
        # Eliminar archivo descomprimido
        uncompressed_file.unlink()
        
        logging.info(f'Backup restaurado exitosamente desde: {backup_file}')
        
    except subprocess.CalledProcessError as e:
        logging.error(f'Error al restaurar backup: {e}')
        raise
    except Exception as e:
        logging.error(f'Error inesperado: {e}')
        raise

def main():
    if len(sys.argv) > 1:
        # Si se proporciona un archivo específico
        backup_file = Path(sys.argv[1])
        if not backup_file.exists():
            logging.error(f"No se encontró el archivo de backup: {backup_file}")
            sys.exit(1)
        restore_backup(backup_file)
    else:
        # Listar backups disponibles
        backups = list_backups()
        if not backups:
            logging.error("No se encontraron backups disponibles")
            sys.exit(1)
            
        print("\nBackups disponibles:")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup.name}")
            
        try:
            choice = int(input("\nSeleccione el número del backup a restaurar: "))
            if 1 <= choice <= len(backups):
                restore_backup(backups[choice-1])
            else:
                logging.error("Selección inválida")
                sys.exit(1)
        except ValueError:
            logging.error("Por favor ingrese un número válido")
            sys.exit(1)

if __name__ == '__main__':
    main() 