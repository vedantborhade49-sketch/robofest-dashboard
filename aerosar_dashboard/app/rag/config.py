from pydantic import BaseModel

class RAGConfig(BaseModel):
    knowledge_base_path: str = "knowledge_base"
    chunk_size: int = 200
    chunk_overlap: int = 50
    top_k: int = 3
    similarity_threshold: float = 0.1
