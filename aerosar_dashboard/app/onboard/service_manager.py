import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class OnboardService(ABC):
    """Base interface for all services running on the Raspberry Pi."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize resources. Returns True if successful."""
        pass

    @abstractmethod
    def start(self):
        """Start the service (e.g. background threads)."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the service gracefully."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Return the current status (e.g., INIT, RUNNING, STOPPED, ERROR)."""
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """Return a dictionary of health metrics."""
        pass


class ServiceManager:
    """
    Manages the lifecycle of all onboard services.
    Ensures that a failure in one service does not crash the entire system.
    """
    def __init__(self):
        self.services: Dict[str, OnboardService] = {}
        self.statuses: Dict[str, str] = {}

    def register_service(self, name: str, service: OnboardService):
        """Registers a service under a specific name."""
        self.services[name] = service
        self.statuses[name] = "REGISTERED"
        logger.info(f"Service registered: {name}")

    def initialize_all(self):
        """Initializes all registered services."""
        for name, service in self.services.items():
            try:
                self.statuses[name] = "INITIALIZING"
                if service.initialize():
                    self.statuses[name] = "INITIALIZED"
                    logger.info(f"Service initialized: {name}")
                else:
                    self.statuses[name] = "INIT_FAILED"
                    logger.error(f"Service failed to initialize: {name}")
            except Exception as e:
                self.statuses[name] = "INIT_ERROR"
                logger.error(f"Error initializing service {name}: {e}")

    def start_all(self):
        """Starts all initialized services."""
        for name, service in self.services.items():
            if self.statuses[name] == "INITIALIZED":
                try:
                    self.statuses[name] = "STARTING"
                    service.start()
                    self.statuses[name] = "RUNNING"
                    logger.info(f"Service started: {name}")
                except Exception as e:
                    self.statuses[name] = "ERROR"
                    logger.error(f"Error starting service {name}: {e}")

    def stop_all(self):
        """Stops all running services."""
        for name, service in reversed(list(self.services.items())):
            try:
                if self.statuses[name] in ["RUNNING", "ERROR"]:
                    self.statuses[name] = "STOPPING"
                    service.stop()
                    self.statuses[name] = "STOPPED"
                    logger.info(f"Service stopped: {name}")
            except Exception as e:
                logger.error(f"Error stopping service {name}: {e}")
                self.statuses[name] = "STOP_ERROR"

    def get_all_statuses(self) -> Dict[str, str]:
        """Returns the status of all managed services."""
        for name, service in self.services.items():
            if self.statuses[name] == "RUNNING":
                try:
                    self.statuses[name] = service.get_status()
                except Exception:
                    self.statuses[name] = "ERROR"
        return self.statuses.copy()

    def get_all_health(self) -> Dict[str, Any]:
        """Returns the health metrics of all managed services."""
        health_data = {}
        for name, service in self.services.items():
            try:
                health_data[name] = service.get_health()
            except Exception:
                health_data[name] = {"error": "Failed to retrieve health"}
        return health_data
