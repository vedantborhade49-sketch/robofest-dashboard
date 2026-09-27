from pydantic import BaseModel

class AIStatus(BaseModel):
    status: str
    model_name: str
    inference_fps: float
    detections_count: int
