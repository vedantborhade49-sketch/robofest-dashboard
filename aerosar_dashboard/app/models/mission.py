from pydantic import BaseModel

class Mission(BaseModel):
    mission_id: str
    mission_status: str
    elapsed_time: float
    search_progress: float
    connection_status: str
