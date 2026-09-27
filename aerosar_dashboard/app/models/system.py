from pydantic import BaseModel

class SystemHealth(BaseModel):
    cpu_usage: float
    memory_usage: float
    temperature: float
    communication_status: str
