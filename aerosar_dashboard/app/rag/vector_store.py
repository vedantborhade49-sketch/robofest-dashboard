import math
import logging
from typing import List, Dict, Tuple, Any
from abc import ABC, abstractmethod
from app.rag.models import Chunk

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    @abstractmethod
    def add(self, chunks: List[Chunk], embeddings: List[Any]):
        pass
        
    @abstractmethod
    def search(self, query_embedding: Any, top_k: int = 3, threshold: float = 0.0) -> List[Tuple[Chunk, float]]:
        pass
        
    @abstractmethod
    def clear(self):
        pass
        
    @abstractmethod
    def count(self) -> int:
        pass

class LocalMemoryVectorStore(VectorStore):
    """
    A pure Python in-memory vector store matching our MockTFIDFEmbeddingProvider.
    Calculates cosine similarity between term-frequency dictionaries.
    """
    
    def __init__(self):
        self._chunks: List[Chunk] = []
        self._embeddings: List[Dict[str, float]] = []
        
    def add(self, chunks: List[Chunk], embeddings: List[Dict[str, float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")
            
        self._chunks.extend(chunks)
        self._embeddings.extend(embeddings)
        logger.info(f"Added {len(chunks)} chunks to vector store. Total: {len(self._chunks)}")
        
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        # Cosine similarity between two sparse dictionaries
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        
        sum1 = sum(val ** 2 for val in vec1.values())
        sum2 = sum(val ** 2 for val in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return numerator / denominator
        
    def search(self, query_embedding: Dict[str, float], top_k: int = 3, threshold: float = 0.0) -> List[Tuple[Chunk, float]]:
        if not query_embedding:
            return []
            
        results = []
        for chunk, chunk_emb in zip(self._chunks, self._embeddings):
            score = self._cosine_similarity(query_embedding, chunk_emb)
            if score >= threshold:
                results.append((chunk, score))
                
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
        
    def clear(self):
        self._chunks = []
        self._embeddings = []
        
    def count(self) -> int:
        return len(self._chunks)
