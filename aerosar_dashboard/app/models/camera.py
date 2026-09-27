from pydantic import BaseModel

class Camera(BaseModel):
    connected: bool
    fps: float
    latency: float
    frame_count: int = 0
    dropped_frames: int = 0
    resolution: str = "1280x720"
