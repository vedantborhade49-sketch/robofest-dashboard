from pydantic import BaseModel

class RetrievedContext(BaseModel):
    """
    Structured model for retrieved contextual intelligence (future RAG output).
    Represents documents, prior mission passes, terrain data, or historical sightings.
    """
    source_id: str
    source_type: str
    content: str
    relevance_score: float
