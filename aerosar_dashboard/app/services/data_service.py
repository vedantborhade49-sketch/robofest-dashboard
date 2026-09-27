from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider

class DataService:
    """
    Service layer that acts as an intermediary between the UI and the data provider.
    This architecture ensures UI logic is decoupled from data sources.
    """
    
    def __init__(self, provider: DataProvider = None):
        # Default to mock provider for development
        self._provider = provider or MockDataProvider()
        
    def get_mission_data(self):
        return self._provider.get_mission()

    def get_drone_data(self):
        return self._provider.get_drone()
        
    def get_telemetry_data(self):
        return self._provider.get_telemetry()
