# Raspberry Pi 5 Deployment Guide

This guide details the procedure for deploying the **STALLION AEROSAR** onboard runtime to a Raspberry Pi 5 companion computer.

## 1. OS Assumptions
- **OS**: Raspberry Pi OS (Bookworm, 64-bit)
- **Python Version**: Python 3.11+
- **Hardware**: Raspberry Pi 5 (8GB RAM recommended)

## 2. Dependencies
Ensure the following system dependencies are installed:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libgl1-mesa-glx libglib2.0-0 htop
```

## 3. Project Installation
Clone the repository and run the setup script:
```bash
git clone https://github.com/your-org/aerosar.git
cd aerosar
chmod +x scripts/*.sh
./scripts/setup_raspberry_pi.sh
```

## 4. Model Installation
Place your YOLO model inside the `models/` directory:
```bash
mkdir -p models
# Copy your best.pt to models/best.pt
```

## 5. Environment Variables
Create a `.env` file in the project root to configure the runtime without modifying code:
```env
AEROSAR_RUNTIME_MODE=PI
AEROSAR_CAMERA_PROVIDER=pi
AEROSAR_YOLO_MODEL=models/best.pt
AEROSAR_YOLO_DEVICE=cpu
AEROSAR_GROUND_URL=http://<GROUND_STATION_IP>:8000
AEROSAR_GROUND_WS=ws://<GROUND_STATION_IP>:8000/api/v1/uav/ws
```

## 6. Hardware Configuration

### Camera
- Connected via CSI or USB.
- Default configured as `pi` provider in `.env`.
- Ensure camera is enabled via `sudo raspi-config` (Legacy/libcamera).

### LiDAR
- Connected via USB/Serial (e.g., `/dev/ttyUSB0`).
- **Status:** TO BE VERIFIED depending on exact LiDAR model used.

### MAVLink
- Connected via UART (e.g., `/dev/ttyAMA0` or `/dev/serial0`).
- **Status:** TO BE VERIFIED depending on Flight Controller wiring.

## 7. Database Setup
The local SQLite database (`onboard_buffer.db`) is automatically created and managed by the runtime in `aerosar_dashboard/data/`.

## 8. Service Management

### Starting AEROSAR
To start manually:
```bash
./scripts/start_aerosar.sh
```
To start via systemd (starts automatically on boot):
```bash
sudo systemctl start aerosar
```

### Stopping AEROSAR
```bash
./scripts/stop_aerosar.sh
# OR
sudo systemctl stop aerosar
```

### Checking Status
```bash
./scripts/status_aerosar.sh
# OR
sudo systemctl status aerosar
```

### Health Check
Run the built-in health check to monitor CPU, RAM, Disk, and Temperature:
```bash
./scripts/health_check.sh
```

### Checking Logs
If running via systemd, view logs with `journalctl`:
```bash
journalctl -u aerosar -f
```

## 9. Troubleshooting & Recovery
- **Camera disconnected:** The `PerceptionAdapterService` will automatically attempt to reconnect every 2 seconds.
- **Network loss:** The `CommunicationService` buffers events locally in the SQLite DB and syncs them once reconnected.
- **High CPU / Temp:** The `SystemHealthMonitor` logs resource warnings. Ensure the Pi has active cooling (fan).
- **Service Crash:** The `systemd` service is configured with `Restart=always` and `RestartSec=5` to automatically recover.

## 10. Deployment Checklist
- [x] Raspberry Pi OS configured
- [x] Python configured
- [x] Dependencies installed
- [x] AEROSAR repository installed
- [x] YOLO model available
- [ ] Camera detected (TO BE VERIFIED)
- [ ] LiDAR detected (TO BE VERIFIED)
- [ ] MAVLink detected (TO BE VERIFIED)
- [x] Network configured
- [x] Ground endpoint configured
- [x] Database initialized
- [x] Evidence directory created
- [x] Logs configured
- [x] Runtime starts
- [x] Health check passes
- [ ] Camera detection tested
- [ ] Telemetry tested
- [ ] Communication tested
- [ ] Incident tested
- [ ] Dashboard tested
