import pytest
from datetime import datetime
from app.rag.models import Document, Chunk
from app.rag.documents import DocumentLoader
from app.rag.chunker import Chunker
from app.rag.embeddings import MockTFIDFEmbeddingProvider
from app.rag.vector_store import LocalMemoryVectorStore
from app.rag.query_builder import QueryBuilder
from app.rag.rag_service import RAGService
from app.rag.config import RAGConfig
from app.models.incident import Incident, Location

def test_document_loader(tmp_path):
    kb_path = tmp_path / "knowledge_base"
    rescue_dir = kb_path / "rescue"
    rescue_dir.mkdir(parents=True)
    
    doc_path = rescue_dir / "test_doc.md"
    doc_path.write_text("This is a test document about rescue operations.")
    
    loader = DocumentLoader(str(kb_path))
    docs = loader.load_all()
    
    assert len(docs) == 1
    assert docs[0].category == "rescue"
    assert "test document" in docs[0].content

def test_chunker():
    doc = Document(
        document_id="DOC-001",
        title="Test",
        content="Word1 Word2 Word3 Word4 Word5",
        source="test.md",
        category="test"
    )
    chunker = Chunker(chunk_size=3, chunk_overlap=1)
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) == 3
    assert chunks[0].text == "Word1 Word2 Word3"
    assert chunks[1].text == "Word3 Word4 Word5"
    assert chunks[2].text == "Word5"

def test_embeddings():
    provider = MockTFIDFEmbeddingProvider()
    emb = provider.embed_text("the quick brown fox")
    assert "quick" in emb
    assert "brown" in emb
    assert "the" not in emb  # stop word removed

def test_vector_store():
    store = LocalMemoryVectorStore()
    c1 = Chunk(chunk_id="C1", document_id="D1", text="rescue person detected")
    c2 = Chunk(chunk_id="C2", document_id="D2", text="drone maintenance battery")
    
    provider = MockTFIDFEmbeddingProvider()
    e1 = provider.embed_text(c1.text)
    e2 = provider.embed_text(c2.text)
    
    store.add([c1, c2], [e1, e2])
    assert store.count() == 2
    
    q = provider.embed_text("person rescue")
    results = store.search(q, top_k=1)
    
    assert len(results) == 1
    assert results[0][0].chunk_id == "C1"

def test_query_builder():
    incident = Incident(
        incident_id="INC-1",
        type="PERSON_DETECTED",
        confidence=0.4,
        timestamp=datetime.now(),
        location=Location(x=0, y=0, z=0)
    )
    qb = QueryBuilder()
    query = qb.build_query(incident)
    
    assert "person detected" in query
    assert "low confidence" in query

def test_rag_service(tmp_path):
    kb_path = tmp_path / "knowledge_base"
    rescue_dir = kb_path / "rescue"
    rescue_dir.mkdir(parents=True)
    
    (rescue_dir / "person.md").write_text("Guidelines for person detected in rescue operations.")
    (rescue_dir / "drone.md").write_text("Drone maintenance and telemetry.")
    
    config = RAGConfig(knowledge_base_path=str(kb_path))
    service = RAGService(config)
    
    service.index_knowledge_base()
    
    incident = Incident(
        incident_id="INC-1",
        type="PERSON_DETECTED",
        confidence=0.9,
        timestamp=datetime.now(),
        location=Location(x=0, y=0, z=0)
    )
    
    result = service.retrieve_for_incident(incident)
    assert result.query is not None
    assert len(result.retrieved_context) > 0
    # The first result should likely be the person doc, not the drone doc
    assert "person" in result.retrieved_context[0].content.lower()
