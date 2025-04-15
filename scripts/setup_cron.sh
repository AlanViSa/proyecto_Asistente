#!/bin/bash

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Create logs directory if it doesn't exist
LOGS_DIR="$ROOT_DIR/logs"
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "Logs directory created at: $LOGS_DIR"
fi

# Path to the Python script
PYTHON_SCRIPT="$ROOT_DIR/app/scripts/enviar_recordatorios.py"

# Verify that the script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Make the script executable
chmod +x "$PYTHON_SCRIPT"

# Create a temporary file for the crontab
TEMP_CRON=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null

# Remove the previous task if it exists
sed -i "/enviar_recordatorios\.py/d" "$TEMP_CRON"

# Add the new task (every 30 minutes)
echo "*/30 * * * * cd $ROOT_DIR && python $PYTHON_SCRIPT >> $LOGS_DIR/recordatorios.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
if crontab "$TEMP_CRON"; then
    echo "Cron task configured successfully"
    echo "Script: $PYTHON_SCRIPT"
    echo "Interval: 30 minutes"
    echo "Logs: $LOGS_DIR/recordatorios.log"
else
    echo "Error al configurar la tarea cron"
    exit 1
fi

# Clean up temporary file
rm "$TEMP_CRON" 