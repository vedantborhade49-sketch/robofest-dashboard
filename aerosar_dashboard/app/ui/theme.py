class Theme:
    # Colors
    BG_BASE = "#0B0F14"
    BG_SECONDARY = "#11161D"
    BG_PANEL = "#151B23"
    BORDER = "#252D38"
    
    TEXT_PRIMARY = "#E8EDF2"
    TEXT_SECONDARY = "#8C98A6"
    
    ACCENT = "#00B4D8" # Aerospace cyan/blue
    ACCENT_HOVER = "#0096B4"
    ACCENT_SELECTED = "#007790"
    
    STATUS_SUCCESS = "#22C55E"
    STATUS_WARNING = "#F59E0B"
    STATUS_CRITICAL = "#EF4444"
    
    # Typography
    FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif"
    
    @classmethod
    def get_global_stylesheet(cls) -> str:
        return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {cls.BG_BASE};
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        
        QLabel {{
            background-color: transparent;
        }}
        """
