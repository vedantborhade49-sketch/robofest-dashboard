from typing import Tuple, Optional
from PySide6.QtCore import QObject, Signal
from app.models.settings import DashboardSettings

class SettingsService(QObject):
    """
    Centralized configuration service for the AEROSAR ground station dashboard.
    Manages in-memory dashboard configuration, handles validation, emits update signals,
    and provides restore-to-default capabilities.
    """
    settings_updated = Signal(object) # Emits DashboardSettings instance

    _instance: Optional["SettingsService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already created
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._settings: DashboardSettings = DashboardSettings()
        self._initialized = True

    def get_settings(self) -> DashboardSettings:
        """Returns a copy of current dashboard configuration settings."""
        return self._settings.model_copy()

    def update_settings(self, new_settings: DashboardSettings) -> Tuple[bool, str]:
        """
        Updates the active configuration after validation.
        Emits settings_updated signal upon success.
        """
        try:
            # Re-validate model if needed
            validated = DashboardSettings(**new_settings.model_dump())
            self._settings = validated
            self.settings_updated.emit(self.get_settings())
            return True, "Settings applied successfully."
        except Exception as e:
            return False, f"Settings validation failed: {str(e)}"

    def reset_to_defaults(self) -> DashboardSettings:
        """Restores dashboard configuration to factory defaults."""
        self._settings = DashboardSettings()
        self.settings_updated.emit(self.get_settings())
        return self.get_settings()
