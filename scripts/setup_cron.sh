#!/bin/bash

# Obtener el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Crear directorio de logs si no existe
LOGS_DIR="$ROOT_DIR/logs"
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "Directorio de logs creado en: $LOGS_DIR"
fi

# Ruta al script de Python
PYTHON_SCRIPT="$ROOT_DIR/app/scripts/enviar_recordatorios.py"

# Verificar que el script existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: No se encontró el script en $PYTHON_SCRIPT"
    exit 1
fi

# Hacer el script ejecutable
chmod +x "$PYTHON_SCRIPT"

# Crear el archivo temporal para el crontab
TEMP_CRON=$(mktemp)

# Exportar el crontab actual
crontab -l > "$TEMP_CRON" 2>/dev/null

# Eliminar la tarea anterior si existe
sed -i "/enviar_recordatorios\.py/d" "$TEMP_CRON"

# Agregar la nueva tarea (cada 30 minutos)
echo "*/30 * * * * cd $ROOT_DIR && python $PYTHON_SCRIPT >> $LOGS_DIR/recordatorios.log 2>&1" >> "$TEMP_CRON"

# Instalar el nuevo crontab
if crontab "$TEMP_CRON"; then
    echo "Tarea cron configurada exitosamente"
    echo "Script: $PYTHON_SCRIPT"
    echo "Intervalo: 30 minutos"
    echo "Logs: $LOGS_DIR/recordatorios.log"
else
    echo "Error al configurar la tarea cron"
    exit 1
fi

# Limpiar archivo temporal
rm "$TEMP_CRON" 