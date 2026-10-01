import time
import logging
import threading
from typing import Optional

from app.onboard.config import OnboardConfig
from app.onboard.buffer import OnboardEventBuffer
from app.onboard.health import SystemHealthMonitor
from app.onboard.service_manager import ServiceManager, OnboardService
from app.onboard.communication import CommunicationService
from app.onboard.adapters import PerceptionAdapterService, SpatialAdapterService, TelemetryAdapterService
from app.services.incident_engine import IncidentEngine
from app.spatial.service import SpatialService
from app.telemetry.service import TelemetryService
from app.models.onboard import OnboardStatus, ServiceStatus

logger = logging.getLogger(__name__)

class OnboardRuntime:
    """
    The main runtime for the Raspberry Pi companion computer.
    Initializes and manages all local services, buffers, and communications.
    """
    def __init__(self, config: OnboardConfig):
        self.config = config
        self.buffer = OnboardEventBuffer(max_size=config.buffer_size)
        self.health_monitor = SystemHealthMonitor(config=config)
        self.service_manager = ServiceManager()
        
        self.communication = CommunicationService(self.config, self.buffer)
        
        self._start_time = 0.0
        self._running = False
        self._health_thread = None
        
        self._setup_services()

    def _setup_services(self):
        """Registers all onboard services with the ServiceManager."""
        self.service_manager.register_service("communication", self.communication)
        
        # Domain core engines
        self.incident_engine = IncidentEngine()
        self.spatial_core = SpatialService()
        self.telemetry_core = TelemetryService()
        
        # Headless Adapters for Pi
        self.perception_adapter = PerceptionAdapterService(
            config=self.config,
            comms=self.communication,
            incident_engine=self.incident_engine
        )
        self.spatial_adapter = SpatialAdapterService(
            config=self.config,
            comms=self.communication,
            spatial_service=self.spatial_core
        )
        self.telemetry_adapter = TelemetryAdapterService(
            config=self.config,
            comms=self.communication,
            telemetry_service=self.telemetry_core
        )
        
        self.service_manager.register_service("perception", self.perception_adapter)
        self.service_manager.register_service("spatial", self.spatial_adapter)
        self.service_manager.register_service("telemetry", self.telemetry_adapter)

    def start(self):
        """Starts the onboard runtime and all services."""
        logger.info(f"Starting OnboardRuntime in {self.config.runtime_mode} mode...")
        self._running = True
        self._start_time = time.time()
        
        self.service_manager.initialize_all()
        self.service_manager.start_all()
        
        if self.config.health_monitor_enabled:
            self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
            self._health_thread.start()
            
        logger.info("OnboardRuntime started successfully.")

    def stop(self):
        """Stops the runtime and safely shuts down services."""
        logger.info("Stopping OnboardRuntime...")
        self._running = False
        
        self.service_manager.stop_all()
        
        if self._health_thread:
            self._health_thread.join(timeout=2.0)
            
        logger.info("OnboardRuntime stopped.")

    def get_status(self) -> OnboardStatus:
        """Returns a snapshot of the runtime's complete status."""
        services = {}
        statuses = self.service_manager.get_all_statuses()
        healths = self.service_manager.get_all_health()
        
        for name in statuses:
            services[name] = ServiceStatus(
                status=statuses[name],
                health=healths.get(name, {})
            )
            
        return OnboardStatus(
            state="RUNNING" if self._running else "STOPPED",
            communication_mode=self.communication.get_status(),
            buffer_count=self.buffer.count(),
            uptime_seconds=time.time() - self._start_time if self._running else 0.0,
            services=services
        )

    def _health_loop(self):
        """Periodically collects health and sends it to the ground station."""
        interval = self.config.health_monitor_interval_ms / 1000.0
        while self._running:
            try:
                report = self.health_monitor.get_health_report()
                
                # We can enqueue this to be sent to ground station
                # Only send if we want to track it historically, or just send current state
                self.communication.send_event("ONBOARD_HEALTH", report, force_sync=False)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                
            time.sleep(interval)
