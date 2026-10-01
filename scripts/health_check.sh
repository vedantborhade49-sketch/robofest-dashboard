#!/bin/bash
# health_check.sh
# Checks CPU, RAM, Temperature and Disk Usage on Raspberry Pi

echo "=== AEROSAR ONBOARD HEALTH CHECK ==="
date

echo -e "\n[CPU]"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "Usage: " 100 - $1"%"}'

echo -e "\n[Memory]"
free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'

echo -e "\n[Disk]"
df -h / | awk 'NR==2{printf "Disk Usage: %s/%s (%.2f%%)\n", $3,$2,$5 }'

echo -e "\n[Temperature]"
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    cpu_temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    cpu_temp_c=$(awk "BEGIN {print $cpu_temp/1000}")
    echo "CPU Temp: ${cpu_temp_c}°C"
else
    echo "Temperature sensor not found."
fi

echo -e "\n[AEROSAR Processes]"
pids=$(pgrep -f "launcher --mode RASPBERRY_PI")
if [ ! -z "$pids" ]; then
    echo "Running (PIDs: $pids)"
else
    echo "Not running."
fi
echo "===================================="
