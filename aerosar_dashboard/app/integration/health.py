import time
from typing import Dict, Any, Optional
from app.integration.readiness import ReadinessState, ComponentState

class HealthAggregator:
    """Aggregates health metrics across all subsystems."""
    
    def __init__(self, readiness_manager):
        self.readiness = readiness_manager
        self.last_updates: Dict[str, float] = {}
        self.errors: Dict[str, str] = {}
        self.latencies: Dict[str, float] = {}
        
    def report_heartbeat(self, component: str, latency: Optional[float] = None, error: Optional[str] = None):
        """Records a heartbeat from a component."""
        self.last_updates[component] = time.time()
        
        if latency is not None:
            self.latencies[component] = latency
            
        if error:
            self.errors[component] = error
            self.readiness.update_component_state(component, ComponentState.ERROR)
        else:
            if component in self.errors:
                del self.errors[component]
            
            # Simple state mapping, this could be more sophisticated
            if self.readiness.get_component_state(component) in [ComponentState.ERROR, ComponentState.UNAVAILABLE, ComponentState.DISCONNECTED]:
                self.readiness.update_component_state(component, ComponentState.CONNECTED)

    def get_system_health(self) -> Dict[str, Any]:
        """Returns aggregated health report for the dashboard."""
        now = time.time()
        components_health = {}
        
        for comp in self.readiness.categories.keys():
            last_update = self.last_updates.get(comp)
            time_since = now - last_update if last_update else None
            
            components_health[comp] = {
                "status": self.readiness.get_component_state(comp).value,
                "last_update": last_update,
                "time_since_last_update": time_since,
                "error": self.errors.get(comp),
                "latency": self.latencies.get(comp)
            }
            
        return {
            "system_state": self.readiness.system_state.value,
            "timestamp": now,
            "components": components_health
        }
