#!/bin/bash
# start_aerosar.sh
# Starts the AEROSAR Onboard Runtime on Raspberry Pi

# Go to project root
cd "$(dirname "$0")/.."

# Load configuration if present
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Ensure virtual environment is activated
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run setup_raspberry_pi.sh first."
    exit 1
fi

echo "Starting AEROSAR onboard runtime in RASPBERRY_PI mode..."

# Set required PYTHONPATH
export PYTHONPATH=$(pwd)

# Run the runtime
python -m aerosar_dashboard.app.integration.launcher --mode RASPBERRY_PI
