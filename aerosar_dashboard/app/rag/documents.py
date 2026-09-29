import os
import glob
import logging
from typing import List
from app.rag.models import Document

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Loads knowledge base documents from a directory structure."""
    
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        
    def load_all(self) -> List[Document]:
        """Scans the KB directory and loads Markdown and JSON files."""
        documents = []
        if not os.path.exists(self.kb_path):
            logger.warning(f"Knowledge base path not found: {self.kb_path}")
            return documents
            
        # Recursive glob for .md files
        search_pattern = os.path.join(self.kb_path, "**", "*.md")
        filepaths = glob.glob(search_pattern, recursive=True)
        
        for idx, path in enumerate(filepaths):
            try:
                doc = self._load_file(path, idx)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading document {path}: {e}")
                
        logger.info(f"Loaded {len(documents)} documents from knowledge base.")
        return documents
        
    def _load_file(self, path: str, idx: int) -> Document:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract basic metadata from path
        filename = os.path.basename(path)
        # Determine category based on parent directory
        parent_dir = os.path.basename(os.path.dirname(path))
        category = parent_dir if parent_dir != os.path.basename(self.kb_path) else "general"
        
        return Document(
            document_id=f"DOC-{category.upper()}-{idx:04d}",
            title=filename.replace(".md", "").replace("_", " ").title(),
            content=content,
            source=filename,
            category=category,
            metadata={"filepath": path}
        )
