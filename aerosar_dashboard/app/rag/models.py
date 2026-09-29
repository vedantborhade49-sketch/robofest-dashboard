from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from app.models.context import RetrievedContext

class Document(BaseModel):
    document_id: str
    title: str
    content: str
    source: str
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievalMetadata(BaseModel):
    top_k: int
    retriever: str
    timestamp: str

class RAGResult(BaseModel):
    query: str
    incident_id: str
    retrieved_context: List[RetrievedContext]
    retrieval_metadata: RetrievalMetadata
