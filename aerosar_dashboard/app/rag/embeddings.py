import math
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import re
from collections import Counter

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> Any:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[Any]:
        pass

class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Real embedding provider using SentenceTransformers.
    Requires sentence-transformers to be installed.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        try:
            from sentence_transformers import SentenceTransformer
            # Note: The model is loaded on initialization, which might take a moment.
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("sentence-transformers is not installed. Please install it using 'pip install sentence-transformers'")

    def embed_text(self, text: str) -> Any:
        # returns numpy array or tensor depending on the model, default is numpy array
        return self.model.encode(text)

    def embed_documents(self, texts: List[str]) -> List[Any]:
        # returns list of numpy arrays or a batched tensor
        embeddings = self.model.encode(texts)
        return [emb for emb in embeddings]
