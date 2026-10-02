import logging
from app.rag.config import RAGConfig
from app.rag.documents import DocumentLoader
from app.rag.chunker import Chunker
from app.rag.vector_store import LocalMemoryVectorStore
from app.rag.query_builder import QueryBuilder
from app.rag.retriever import Retriever
from app.rag.models import RAGResult
from app.models.incident import Incident

logger = logging.getLogger(__name__)

from typing import Optional

from app.rag.embeddings import EmbeddingProvider, SentenceTransformerEmbeddingProvider

class RAGService:
    """
    High-level service facade for the RAG Engine.
    Handles initialization, knowledge base indexing, and retrieval.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        
        # Initialize components
        self.document_loader = DocumentLoader(kb_path=self.config.knowledge_base_path)
        self.chunker = Chunker(
            chunk_size=self.config.chunk_size, 
            chunk_overlap=self.config.chunk_overlap
        )
        self.embedding_provider = SentenceTransformerEmbeddingProvider()
        self.vector_store = LocalMemoryVectorStore()
        self.query_builder = QueryBuilder()
        
        self.retriever = Retriever(
            embedding_provider=self.embedding_provider,
            vector_store=self.vector_store,
            query_builder=self.query_builder,
            top_k=self.config.top_k,
            similarity_threshold=self.config.similarity_threshold
        )
        
        self._is_indexed = False
        
    def index_knowledge_base(self):
        """Loads documents, chunks them, embeds them, and stores them in the vector store."""
        logger.info("Starting Knowledge Base indexing...")
        
        self.vector_store.clear()
        
        # Load docs
        documents = self.document_loader.load_all()
        if not documents:
            logger.warning("No documents found to index.")
            return
            
        # Chunk docs
        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            logger.warning("No chunks generated from documents.")
            return
            
        # Embed chunks
        chunk_texts = [c.text for c in chunks]
        embeddings = self.embedding_provider.embed_documents(chunk_texts)
        
        # Store
        self.vector_store.add(chunks, embeddings)
        self._is_indexed = True
        logger.info(f"Knowledge Base indexing complete. {self.vector_store.count()} chunks stored.")
        
    def retrieve_for_incident(self, incident: Incident) -> RAGResult:
        """
        Main entrypoint for retrieving context given an incident.
        """
        if not self._is_indexed:
            logger.warning("Vector store is not indexed. Indexing now...")
            self.index_knowledge_base()
            
        return self.retriever.retrieve_for_incident(incident)
