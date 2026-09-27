from pydantic import BaseModel
from .incident import Location

class Telemetry(BaseModel):
    altitude: float
    speed: float
    heading: float
    battery: float
    signal: float
    position: Location
