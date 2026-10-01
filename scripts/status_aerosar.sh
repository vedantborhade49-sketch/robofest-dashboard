#!/bin/bash
# status_aerosar.sh
# Checks if AEROSAR runtime is running

echo "=== AEROSAR SYSTEM STATUS ==="

if systemctl is-active --quiet aerosar.service; then
    echo "Service: RUNNING (systemd)"
    systemctl status aerosar.service --no-pager | grep -E "Active:|Main PID"
else
    echo "Service: NOT RUNNING via systemd"
    
    pids=$(pgrep -f "launcher --mode RASPBERRY_PI")
    if [ ! -z "$pids" ]; then
        echo "Processes running manually:"
        ps -f -p $pids
    else
        echo "No manual processes found."
    fi
fi
