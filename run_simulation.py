import asyncio
import os
import sys
import threading
import time
import subprocess

# Add aerosar_dashboard to sys.path so that 'from app.*' imports work correctly
dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aerosar_dashboard")
sys.path.insert(0, dashboard_dir)

import uvicorn
from app.api.app import app
from app.models.communication import UAVMessage

SIMULATOR_PORT = 8000
BASE_URL = f"http://127.0.0.1:{SIMULATOR_PORT}"

def start_backend():
    print("[Simulator] Starting Ground FastAPI Backend...")
    uvicorn.run(app, host="127.0.0.1", port=SIMULATOR_PORT, log_level="warning")

def run_uav_simulation():
    print("[Simulator] Starting UAV Telemetry Simulation...")
    # Wait for backend to start
    time.sleep(3)
    
    # We will simulate HTTP requests to the backend for telemetry updates (or use WebSocket if configured)
    # Since we are mocking the UAV, we will just use the HTTP endpoints or direct event bus posting if inside the same process.
    # Wait, the Ground API has `/api/v1/uav/ws` for WebSocket communication.
    import websockets
    import json
    
    async def uav_loop():
        uri = f"ws://127.0.0.1:{SIMULATOR_PORT}/api/v1/uav/ws"
        try:
            async with websockets.connect(uri) as websocket:
                print("[Simulator] UAV connected to Ground Station.")
                seq = 0
                while True:
                    # Send Telemetry
                    payload = {
                        "flight": {
                            "latitude": 34.0522 + (seq * 0.0001),
                            "longitude": -118.2437,
                            "altitude": 100.0,
                            "heading": 45.0,
                            "speed": 10.0,
                            "battery": 95.0 - (seq * 0.1),
                            "signal": 100.0,
                            "position": {"latitude": 34.0522, "longitude": -118.2437, "x": 10.0, "y": 20.0, "z": 100.0}
                        }
                    }
                    msg = {
                        "message_id": f"msg_{seq}",
                        "mission_id": "TEST_MISSION",
                        "sender_id": "UAV_1",
                        "message_type": "TELEMETRY_UPDATE",
                        "sequence_number": seq,
                        "timestamp": time.time(),
                        "delivery_class": "BEST_EFFORT",
                        "payload": payload
                    }
                    await websocket.send(json.dumps(msg))
                    
                    if seq % 10 == 0:
                        # Send occasional incident
                        incident_payload = {
                            "incident": {
                                "incident_id": f"SIM_INC_{seq}",
                                "type": "person",
                                "confidence": 0.95,
                                "status": "NEW",
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                            }
                        }
                        inc_msg = {
                            "message_id": f"inc_{seq}",
                            "mission_id": "TEST_MISSION",
                            "sender_id": "UAV_1",
                            "message_type": "INCIDENT_CREATED",
                            "sequence_number": seq + 1000,
                            "timestamp": time.time(),
                            "delivery_class": "RELIABLE",
                            "payload": incident_payload
                        }
                        await websocket.send(json.dumps(inc_msg))
                    
                    seq += 1
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"[Simulator] UAV Simulation error: {e}")
            
    asyncio.run(uav_loop())

def start_dashboard():
    print("[Simulator] Starting Dashboard in LIVE mode...")
    env = os.environ.copy()
    env["DATA_MODE"] = "live"
    # Use the same python executable
    dashboard_path = os.path.join(os.path.dirname(__file__), "aerosar_dashboard", "main.py")
    subprocess.Popen([sys.executable, dashboard_path], env=env)

if __name__ == "__main__":
    print("==================================================")
    print(" AEROSAR Step 28: Live Data End-to-End Simulation ")
    print("==================================================")
    
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    uav_thread = threading.Thread(target=run_uav_simulation, daemon=True)
    uav_thread.start()
    
    # Wait a bit before starting dashboard
    time.sleep(4)
    start_dashboard()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Simulator] Shutting down...")
