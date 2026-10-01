#!/bin/bash
# stop_aerosar.sh
# Stops the AEROSAR Onboard Runtime on Raspberry Pi

echo "Stopping AEROSAR Onboard Runtime..."

# Check if running via systemd
if systemctl is-active --quiet aerosar.service; then
    echo "Stopping systemd service..."
    sudo systemctl stop aerosar.service
    echo "Service stopped."
else
    echo "AEROSAR is not running as a systemd service, looking for processes..."
    # Find and kill the python processes running the launcher in RASPBERRY_PI mode
    pids=$(pgrep -f "launcher --mode RASPBERRY_PI")
    
    if [ -z "$pids" ]; then
        echo "No AEROSAR processes found."
    else
        echo "Killing processes: $pids"
        kill -15 $pids
        sleep 2
        # Force kill if still running
        pids=$(pgrep -f "launcher --mode RASPBERRY_PI")
        if [ ! -z "$pids" ]; then
            echo "Force killing processes: $pids"
            kill -9 $pids
        fi
        echo "AEROSAR processes stopped."
    fi
fi
