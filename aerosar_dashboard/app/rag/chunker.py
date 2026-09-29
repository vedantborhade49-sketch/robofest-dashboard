from typing import List
from app.rag.models import Document, Chunk
import logging

logger = logging.getLogger(__name__)

class Chunker:
    """Splits documents into smaller text chunks for retrieval."""
    
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def chunk_document(self, doc: Document) -> List[Chunk]:
        chunks = []
        words = doc.content.split()
        
        if not words:
            return chunks
            
        idx = 0
        chunk_index = 1
        while idx < len(words):
            end_idx = min(idx + self.chunk_size, len(words))
            chunk_words = words[idx:end_idx]
            
            chunk_text = " ".join(chunk_words)
            chunk = Chunk(
                chunk_id=f"{doc.document_id}-CHK-{chunk_index:03d}",
                document_id=doc.document_id,
                text=chunk_text,
                metadata={
                    "title": doc.title,
                    "category": doc.category,
                    "source": doc.source
                }
            )
            chunks.append(chunk)
            
            idx += (self.chunk_size - self.chunk_overlap)
            chunk_index += 1
            
        return chunks
        
    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        all_chunks = []
        for doc in documents:
            try:
                doc_chunks = self.chunk_document(doc)
                all_chunks.extend(doc_chunks)
            except Exception as e:
                logger.error(f"Error chunking document {doc.document_id}: {e}")
                
        logger.info(f"Generated {len(all_chunks)} chunks from {len(documents)} documents.")
        return all_chunks
