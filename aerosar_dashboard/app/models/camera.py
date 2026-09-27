from pydantic import BaseModel

class Camera(BaseModel):
    connected: bool
    fps: float
    latency: float
