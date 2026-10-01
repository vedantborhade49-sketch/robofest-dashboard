class Theme:
    # --- COLORS ---
    BACKGROUND = "#0B0F14"
    SURFACE = "#11161D"
    SURFACE_ELEVATED = "#151B23"
    BORDER = "#252D38"
    
    TEXT_PRIMARY = "#E8EDF2"
    TEXT_SECONDARY = "#8C98A6"
    
    ACCENT = "#00B4D8"
    ACCENT_HOVER = "#0096B4"
    ACCENT_SELECTED = "#007790"
    
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    INFO = "#3B82F6"

    # Status/Legacy mappings
    BG_BASE = BACKGROUND
    BG_SECONDARY = SURFACE
    BG_PANEL = SURFACE_ELEVATED
    STATUS_SUCCESS = SUCCESS
    STATUS_WARNING = WARNING
    STATUS_CRITICAL = DANGER
    STATUS_ERROR = DANGER

    # Incident Colors
    INCIDENT_NEW = "#F59E0B"        # Warning/Amber
    INCIDENT_REVIEW = "#3B82F6"     # Info/Blue
    INCIDENT_CONFIRMED = "#EF4444"  # Danger/Red
    INCIDENT_RESOLVED = "#22C55E"   # Success/Green
    INCIDENT_DISMISSED = "#8C98A6"  # Secondary/Gray

    # --- TYPOGRAPHY ---
    FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif"
    
    # --- SPACING ---
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32

    @classmethod
    def get_global_stylesheet(cls) -> str:
        return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {cls.BACKGROUND};
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        
        QLabel {{
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {cls.BACKGROUND};
            width: 8px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.BORDER};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            border: none;
            background: {cls.BACKGROUND};
            height: 8px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {cls.BORDER};
            min-width: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        """
