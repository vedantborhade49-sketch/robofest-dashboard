import logging
import time
from typing import Dict, Any, Optional

from app.integration.readiness import ReadinessManager, ReadinessState, ComponentState
from app.integration.health import HealthAggregator

logger = logging.getLogger(__name__)

class IntegrationService:
    """
    Central orchestration layer.
    Coordinates startup, readiness checking, and shutdown of all subsystems.
    """
    
    def __init__(self, mode: str = "SIMULATION"):
        self.mode = mode
        self.readiness = ReadinessManager()
        self.health = HealthAggregator(self.readiness)
        
        # We will hold references to all orchestrated subsystems here
        self.services = {}
        
    def register_service(self, name: str, service_obj):
        """Registers a service for orchestration."""
        self.services[name] = service_obj
        self.readiness.update_component_state(name, ComponentState.INITIALIZING)

    def startup_sequence(self):
        """
        Executes deterministic startup sequence.
        1. Configuration / Logging
        2. Database / State
        3. Communication
        4. MAVLink / Telemetry
        5. Camera / LiDAR / SLAM
        6. Perception / Incident
        7. Intelligence (RAG/LLM)
        """
        logger.info(f"Starting AEROSAR System Integration in {self.mode} mode...")
        self.readiness.system_state = ReadinessState.STARTING
        
        try:
            # Group 1: Foundations
            self._start_service("database")
            self._start_service("state")
            
            # Group 2: Comms
            self._start_service("communication")
            
            # Group 3: Telemetry
            self._start_service("mavlink")
            
            # Group 4: Spatial & Perception
            self._start_service("camera")
            self._start_service("lidar")
            self._start_service("slam")
            self._start_service("yolo")
            self._start_service("incident_engine")
            
            # Group 5: Intelligence
            self._start_service("rag")
            self._start_service("llm")
            
            # Re-evaluate overall readiness
            self.readiness.system_state = ReadinessState.READY
            self.readiness.re_evaluate_system_state()
            logger.info(f"System startup complete. State: {self.readiness.system_state.value}")
            
        except Exception as e:
            logger.error(f"Critical error during startup: {e}")
            self.readiness.system_state = ReadinessState.ERROR

    def _start_service(self, name: str):
        if name in self.services:
            logger.info(f"Starting {name}...")
            try:
                # Assuming services have a start() method
                svc = self.services[name]
                if hasattr(svc, "start"):
                    svc.start()
                self.readiness.update_component_state(name, ComponentState.READY)
                self.health.report_heartbeat(name)
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")
                self.readiness.update_component_state(name, ComponentState.ERROR)
                self.health.report_heartbeat(name, error=str(e))
        else:
            logger.warning(f"Service {name} not registered. Skipping.")
            self.readiness.update_component_state(name, ComponentState.UNAVAILABLE)

    def shutdown(self):
        """Safely shutdown all services."""
        logger.info("Initiating system shutdown...")
        self.readiness.system_state = ReadinessState.STOPPING
        
        # Shutdown in reverse order generally
        shutdown_order = [
            "llm", "rag", "incident_engine", "yolo", "slam", "lidar", "camera",
            "mavlink", "communication", "state", "database"
        ]
        
        for name in shutdown_order:
            if name in self.services:
                logger.info(f"Stopping {name}...")
                try:
                    svc = self.services[name]
                    if hasattr(svc, "stop"):
                        svc.stop()
                    self.readiness.update_component_state(name, ComponentState.DISCONNECTED)
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
                    
        self.readiness.system_state = ReadinessState.STOPPED
        logger.info("System shutdown complete.")
