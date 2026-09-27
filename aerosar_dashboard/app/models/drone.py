from pydantic import BaseModel

class Drone(BaseModel):
    drone_id: str
    status: str
    battery: float
    altitude: float
    speed: float
    heading: float
    signal_strength: float
