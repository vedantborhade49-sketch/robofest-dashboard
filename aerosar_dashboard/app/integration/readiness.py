from enum import Enum
from typing import Dict, Any, List

class ReadinessState(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

class ComponentState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    READY = "READY"
    LOADING = "LOADING"
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING"
    TRACKING = "TRACKING"
    LOST = "LOST"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"

class ComponentCategory(str, Enum):
    CRITICAL_FOUNDATION = "CRITICAL_FOUNDATION"
    PERCEPTION_CRITICAL = "PERCEPTION_CRITICAL"
    SPATIAL_CRITICAL = "SPATIAL_CRITICAL"
    VEHICLE_TELEMETRY = "VEHICLE_TELEMETRY"
    INTELLIGENCE = "INTELLIGENCE"
    COMMUNICATION = "COMMUNICATION"

class ReadinessManager:
    """Tracks component-level and system-wide readiness states."""
    
    def __init__(self):
        self.system_state = ReadinessState.STOPPED
        self.component_states: Dict[str, ComponentState] = {}
        
        # Component categorization for degraded vs error states
        self.categories = {
            "config": ComponentCategory.CRITICAL_FOUNDATION,
            "logging": ComponentCategory.CRITICAL_FOUNDATION,
            "database": ComponentCategory.CRITICAL_FOUNDATION,
            "state": ComponentCategory.CRITICAL_FOUNDATION,
            
            "camera": ComponentCategory.PERCEPTION_CRITICAL,
            "yolo": ComponentCategory.PERCEPTION_CRITICAL,
            "incident_engine": ComponentCategory.PERCEPTION_CRITICAL,
            
            "lidar": ComponentCategory.SPATIAL_CRITICAL,
            "slam": ComponentCategory.SPATIAL_CRITICAL,
            
            "mavlink": ComponentCategory.VEHICLE_TELEMETRY,
            
            "rag": ComponentCategory.INTELLIGENCE,
            "llm": ComponentCategory.INTELLIGENCE,
            
            "communication": ComponentCategory.COMMUNICATION
        }

    def update_component_state(self, component: str, state: ComponentState):
        """Update a specific component's readiness state and re-evaluate system state."""
        self.component_states[component] = state
        self.re_evaluate_system_state()

    def get_component_state(self, component: str) -> ComponentState:
        return self.component_states.get(component, ComponentState.UNAVAILABLE)

    def re_evaluate_system_state(self):
        """Determine system state based on component states and their critical categories."""
        if self.system_state in [ReadinessState.STARTING, ReadinessState.STOPPING, ReadinessState.STOPPED]:
            return
            
        has_critical_error = False
        has_degraded_optional = False
        
        for comp, state in self.component_states.items():
            category = self.categories.get(comp)
            
            if state in [ComponentState.ERROR, ComponentState.UNAVAILABLE, ComponentState.DISCONNECTED, ComponentState.LOST]:
                if category == ComponentCategory.CRITICAL_FOUNDATION:
                    has_critical_error = True
                elif category == ComponentCategory.PERCEPTION_CRITICAL:
                    # Camera/YOLO failure degrades the system but may not fully crash if spatial/telemetry works
                    has_degraded_optional = True
                else:
                    has_degraded_optional = True
                    
        if has_critical_error:
            self.system_state = ReadinessState.ERROR
        elif has_degraded_optional:
            self.system_state = ReadinessState.DEGRADED
        else:
            self.system_state = ReadinessState.READY
