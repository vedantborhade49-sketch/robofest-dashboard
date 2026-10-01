from enum import Enum

class ScreenSize(Enum):
    LARGE = 1      # >= 1600
    STANDARD = 2   # 1280 - 1599
    COMPACT = 3    # 1000 - 1279
    MINIMUM = 4    # < 1000

def get_screen_size(width: int) -> ScreenSize:
    if width >= 1600:
        return ScreenSize.LARGE
    elif width >= 1280:
        return ScreenSize.STANDARD
    elif width >= 1000:
        return ScreenSize.COMPACT
    else:
        return ScreenSize.MINIMUM
