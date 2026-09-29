import logging
from typing import List, Tuple
from datetime import datetime
from app.rag.models import RAGResult, RetrievalMetadata
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import VectorStore
from app.rag.query_builder import QueryBuilder
from app.models.incident import Incident
from app.models.context import RetrievedContext

logger = logging.getLogger(__name__)

class Retriever:
    """Orchestrates the retrieval of relevant context from the vector store."""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        query_builder: QueryBuilder,
        top_k: int = 3,
        similarity_threshold: float = 0.1
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.query_builder = query_builder
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
    def retrieve_for_incident(self, incident: Incident) -> RAGResult:
        """Transforms incident to query and searches the vector store."""
        
        # 1. Build query
        query_str = self.query_builder.build_query(incident)
        logger.info(f"Generated RAG query for incident {incident.incident_id}: '{query_str}'")
        
        # 2. Embed query
        query_embedding = self.embedding_provider.embed_text(query_str)
        
        # 3. Search vector store
        results = self.vector_store.search(
            query_embedding, 
            top_k=self.top_k, 
            threshold=self.similarity_threshold
        )
        
        # 4. Format results
        retrieved_contexts = []
        for chunk, score in results:
            ctx = RetrievedContext(
                source_id=chunk.chunk_id,
                source_type="Knowledge Base Document",
                content=chunk.text,
                relevance_score=round(score, 4)
            )
            retrieved_contexts.append(ctx)
            
        logger.info(f"Retrieved {len(retrieved_contexts)} relevant contexts for incident {incident.incident_id}.")
            
        metadata = RetrievalMetadata(
            top_k=self.top_k,
            retriever="LocalMemoryRetriever (TF-IDF)",
            timestamp=datetime.now().isoformat()
        )
        
        return RAGResult(
            query=query_str,
            incident_id=incident.incident_id,
            retrieved_context=retrieved_contexts,
            retrieval_metadata=metadata
        )
