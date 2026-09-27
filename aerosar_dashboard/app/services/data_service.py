from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider

class DataService:
    def __init__(self, provider: DataProvider = None):
        self._provider = provider or MockDataProvider()
        
    def get_mission_data(self): return self._provider.get_mission()
    def get_drone_data(self): return self._provider.get_drone()
    def get_telemetry_data(self): return self._provider.get_telemetry()
    def get_camera_data(self): return self._provider.get_camera()
    def get_ai_data(self): return self._provider.get_ai_status()
    def get_system_health(self): return self._provider.get_system_health()
    def get_incidents(self): return self._provider.get_incidents()
    def get_events(self): return self._provider.get_events()
    def get_detections(self): return self._provider.get_detections()
