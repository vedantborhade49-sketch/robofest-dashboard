#!/bin/bash
# setup_raspberry_pi.sh
# Sets up dependencies for Raspberry Pi 5 deployment

echo "Setting up AEROSAR for Raspberry Pi 5..."

# 1. System packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libgl1-mesa-glx libglib2.0-0 htop

# 2. Python Environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Dependencies
pip install --upgrade pip
pip install -r aerosar_dashboard/requirements.txt
# Ensure Pi specific packages are installed
pip install psutil ultralytics opencv-python-headless pydantic-settings

# 4. Directories
mkdir -p aerosar_dashboard/data/logs
mkdir -p aerosar_dashboard/data/evidence

# 5. Service Configuration (systemd)
SERVICE_FILE="/etc/systemd/system/aerosar.service"
echo "Creating systemd service at $SERVICE_FILE (requires sudo)"

sudo bash -c "cat > $SERVICE_FILE << EOF
[Unit]
Description=AEROSAR Onboard Runtime
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/scripts/start_aerosar.sh
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=aerosar

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable aerosar.service

echo "Setup complete. AEROSAR service is enabled but not started."
echo "To start AEROSAR manually: ./scripts/start_aerosar.sh"
echo "To start via systemd: sudo systemctl start aerosar"
