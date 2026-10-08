from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.incident import Location

class SearchBoundary(BaseModel):
    min_x: float = 0.0
    max_x: float = 30.0
    min_y: float = 0.0
    max_y: float = 25.0

class MapState(BaseModel):
    drone_position: Location
    drone_heading: float = 0.0  # degrees (0° = North, clockwise)
    trajectory: List[Location] = Field(default_factory=list)
    search_boundary: SearchBoundary = Field(default_factory=SearchBoundary)
    explored_percentage: float = 0.0
    explored_polygon: List[Location] = Field(default_factory=list)
    map_status: str = "READY"
    coordinate_frame: str = "LOCAL / SLAM"
