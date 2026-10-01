import os
import sys
import logging
import argparse
import subprocess
import time

from app.integration.coordinator import IntegrationService
from app.integration.readiness import ReadinessState
from app.onboard.config import OnboardConfig
from app.onboard.runtime import OnboardRuntime
import uvicorn
from app.api.app import app as ground_app
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

def run_simulation():
    """Runs both Ground Station and Mock Onboard in the same process/machine."""
    logger.info("Starting SIMULATION mode...")
    integration = IntegrationService(mode="SIMULATION")
    integration.startup_sequence()
    
    def start_backend():
        logger.info("[SIMULATION] Starting Ground FastAPI Backend...")
        uvicorn.run(ground_app, host="127.0.0.1", port=8000, log_level="warning")

    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    def start_dashboard():
        logger.info("[SIMULATION] Starting Dashboard in LIVE mode...")
        env = os.environ.copy()
        env["DATA_MODE"] = "live"
        dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "main.py")
        subprocess.Popen([sys.executable, dashboard_path], env=env)

    # Wait for backend
    time.sleep(3)
    start_dashboard()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.shutdown()


def run_raspberry_pi():
    """Runs the onboard Pi runtime with real hardware adapters."""
    logger.info("Starting RASPBERRY_PI mode...")
    config = OnboardConfig(runtime_mode="PI")
    runtime = OnboardRuntime(config=config)
    
    integration = IntegrationService(mode="RASPBERRY_PI")
    integration.register_service("onboard_runtime", runtime)
    integration.startup_sequence()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.shutdown()


def run_ground_station():
    """Runs only the Ground Station API and persistence."""
    logger.info("Starting GROUND_STATION mode...")
    integration = IntegrationService(mode="GROUND_STATION")
    integration.startup_sequence()
    
    logger.info("[GROUND] Starting FastAPI Backend...")
    uvicorn.run(ground_app, host="0.0.0.0", port=8000)


def run_laptop():
    """Runs onboard runtime with mock hardware adapters for dev testing."""
    logger.info("Starting LAPTOP mode...")
    config = OnboardConfig(runtime_mode="LAPTOP")
    runtime = OnboardRuntime(config=config)
    
    integration = IntegrationService(mode="LAPTOP")
    integration.register_service("onboard_runtime", runtime)
    integration.startup_sequence()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AEROSAR System Launcher")
    parser.add_argument("--mode", type=str, choices=["SIMULATION", "RASPBERRY_PI", "GROUND_STATION", "LAPTOP"], 
                        default="SIMULATION", help="Runtime mode")
    
    args = parser.parse_args()
    
    if args.mode == "SIMULATION":
        run_simulation()
    elif args.mode == "RASPBERRY_PI":
        run_raspberry_pi()
    elif args.mode == "GROUND_STATION":
        run_ground_station()
    elif args.mode == "LAPTOP":
        run_laptop()
