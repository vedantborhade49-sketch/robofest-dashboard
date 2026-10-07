from typing import List
import re
import math
from collections import Counter
from app.rag.embeddings import EmbeddingProvider

class MockTFIDFEmbeddingProvider(EmbeddingProvider):
    """
    A simple, dependency-free local 'embedding' provider based on word frequencies.
    It returns a dict of term frequencies to be used for basic cosine similarity.
    (This avoids forcing a heavy LLM or SentenceTransformers install for the first step).
    """
    
    def __init__(self):
        # We could build an IDF dict if we trained it, but for simplicity
        # we'll just use raw term frequency (TF) to represent the vector.
        pass
        
    def _tokenize(self, text: str) -> List[str]:
        # Lowercase and split by non-alphanumeric
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out basic stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "it", "this", "that"}
        return [w for w in words if w not in stop_words]

    def embed_text(self, text: str) -> Dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        
        counts = Counter(tokens)
        total_terms = len(tokens)
        
        # Calculate term frequency (TF)
        tf = {word: count / total_terms for word, count in counts.items()}
        return tf

    def embed_documents(self, texts: List[str]) -> List[Dict[str, float]]:
        return [self.embed_text(text) for text in texts]
