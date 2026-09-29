import sys
import json
from datetime import datetime
from app.rag.rag_service import RAGService
from app.rag.config import RAGConfig
from app.models.incident import Incident, Location

def run_test():
    print("\n--- AEROSAR RAG DEVELOPMENT TEST ---")
    
    # Configure path for tests
    config = RAGConfig(knowledge_base_path="knowledge_base")
    service = RAGService(config)
    
    print("\nIndexing Knowledge Base...")
    service.index_knowledge_base()
    
    # Mock Incident 1: Person Detected
    mock_incident_1 = Incident(
        incident_id="INC-TEST-001",
        mission_id="SAR-TEST",
        type="PERSON_DETECTED",
        confidence=0.91,
        timestamp=datetime.now(),
        location=Location(x=12.4, y=5.7, z=2.1),
        status="NEW"
    )
    
    # Mock Incident 2: Low confidence
    mock_incident_2 = Incident(
        incident_id="INC-TEST-002",
        mission_id="SAR-TEST",
        type="PERSON_DETECTED",
        confidence=0.45,
        timestamp=datetime.now(),
        location=Location(x=10.0, y=10.0, z=0.0),
        status="NEW"
    )

    for i, incident in enumerate([mock_incident_1, mock_incident_2], 1):
        print(f"\n======================================")
        print(f"TEST {i}: {incident.type} (Confidence: {incident.confidence})")
        
        result = service.retrieve_for_incident(incident)
        
        print(f"\nQuery: {result.query}")
        print(f"Retrieved Contexts ({len(result.retrieved_context)} found):")
        
        for idx, ctx in enumerate(result.retrieved_context, 1):
            print(f"\n  {idx}. [Score: {ctx.relevance_score}] {ctx.source_type} ({ctx.source_id})")
            # print a snippet of content
            snippet = ctx.content[:100].replace('\n', ' ') + '...' if len(ctx.content) > 100 else ctx.content
            print(f"     \"{snippet}\"")
            
        print("\nRetrieval Metadata:")
        print(json.dumps(result.retrieval_metadata.model_dump(), indent=2))

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_test()
