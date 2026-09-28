import os
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.repository import Repository
from app.models.incident import Incident, Location
from app.models.event import Event
from app.models.report import Report, IncidentSummary
from app.models.context import RetrievedContext
from app.models.detection import BoundingBox
from app.database import database

class TestDatabasePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use an in-memory SQLite database or a temporary file for tests
        cls.db_path = "sqlite:///:memory:"
        cls.engine = create_engine(cls.db_path, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Override the global engine and sessionmaker in the database module
        database.engine = cls.engine
        database.SessionLocal = cls.SessionLocal
        
        # Create tables
        Base.metadata.create_all(bind=cls.engine)
        
        # Create repository instance
        cls.repo = Repository()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def test_01_database_starts_and_tables_created(self):
        # Verify that tables exist by checking the metadata
        tables = Base.metadata.tables.keys()
        self.assertIn("incidents", tables)
        self.assertIn("reports", tables)
        self.assertIn("events", tables)
        self.assertIn("retrieved_context", tables)

    def test_02_incident_persistence(self):
        # Create
        inc = Incident(
            incident_id="TEST-INC-1",
            mission_id="SAR-001",
            type="FIRE",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
            bbox=BoundingBox(x=0.5, y=0.5, width=0.1, height=0.1),
            location=Location(x=10.0, y=20.0, z=30.0),
            status="NEW"
        )
        
        # Save
        self.repo.save_incident(inc)
        
        # Retrieve
        incidents = self.repo.get_incidents()
        self.assertGreaterEqual(len(incidents), 1)
        
        retrieved_inc = next((i for i in incidents if i.incident_id == "TEST-INC-1"), None)
        self.assertIsNotNone(retrieved_inc)
        self.assertEqual(retrieved_inc.type, "FIRE")
        self.assertEqual(retrieved_inc.location.x, 10.0)
        if retrieved_inc.bbox:
            self.assertEqual(retrieved_inc.bbox.width, 0.1)

    def test_03_event_persistence(self):
        # Create
        ev = Event(
            event_id="TEST-EVT-1",
            timestamp=datetime.now(timezone.utc),
            level="WARNING",
            source="SYSTEM",
            event_type="TEST",
            message="Test event message",
            severity="WARNING"
        )
        
        # Save
        self.repo.save_event(ev)
        
        # Retrieve
        events = self.repo.get_events()
        retrieved_ev = next((e for e in events if e.event_id == "TEST-EVT-1"), None)
        self.assertIsNotNone(retrieved_ev)
        self.assertEqual(retrieved_ev.message, "Test event message")

    def test_04_report_and_context_persistence(self):
        # Create Context
        ctx1 = RetrievedContext(
            source_id="TEST-SRC-1",
            source_type="LOG",
            content="Test log content",
            relevance_score=0.9
        )
        
        # Create Report
        rep = Report(
            report_id="TEST-RPT-1",
            incident_id="TEST-INC-1",
            mission_id="SAR-001",
            status="GENERATED",
            generated_at=datetime.now(timezone.utc),
            incident_type="FIRE",
            confidence=0.95,
            incident_summary=IncidentSummary(
                incident_id="TEST-INC-1",
                type="FIRE",
                confidence=0.95,
                timestamp=datetime.now(timezone.utc),
                location=Location(x=10.0, y=20.0, z=30.0),
                status="NEW"
            ),
            ai_report="This is a test AI report.",
            context_sources=[ctx1],
            evidence_image=None,
            evidence_source="Camera-01",
            evidence_frame=100,
            human_review_status="PENDING",
            model_name="TEST-LLM"
        )
        
        # Save
        self.repo.save_report(rep)
        
        # Retrieve
        reports = self.repo.get_reports()
        retrieved_rep = next((r for r in reports if r.report_id == "TEST-RPT-1"), None)
        self.assertIsNotNone(retrieved_rep)
        self.assertEqual(retrieved_rep.ai_report, "This is a test AI report.")
        
        # Verify Context
        self.assertEqual(len(retrieved_rep.context_sources), 1)
        self.assertEqual(retrieved_rep.context_sources[0].content, "Test log content")

    def test_05_database_close_and_reopen(self):
        # We simulate closing and reopening by creating a new engine on a temporary file
        temp_db_path = "test_persistence.db"
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
            
        try:
            # 1. Initialize DB and save data
            engine1 = create_engine(f"sqlite:///{temp_db_path}", connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=engine1)
            SessionLocal1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
            
            database.engine = engine1
            database.SessionLocal = SessionLocal1
            repo1 = Repository()
            
            inc = Incident(
                incident_id="PERSIST-INC-1",
                mission_id="SAR-001",
                type="FLOOD",
                confidence=0.99,
                timestamp=datetime.now(timezone.utc),
                location=Location(x=1.0, y=2.0, z=3.0),
                status="NEW"
            )
            repo1.save_incident(inc)
            
            # 2. Close by disposing engine
            if hasattr(SessionLocal1, 'close_all'):
                SessionLocal1.close_all()
            engine1.dispose()
            
            # 3. Reopen DB
            engine2 = create_engine(f"sqlite:///{temp_db_path}", connect_args={"check_same_thread": False})
            SessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
            
            database.engine = engine2
            database.SessionLocal = SessionLocal2
            repo2 = Repository()
            
            # 4. Read data
            incidents = repo2.get_incidents()
            retrieved_inc = next((i for i in incidents if i.incident_id == "PERSIST-INC-1"), None)
            self.assertIsNotNone(retrieved_inc)
            self.assertEqual(retrieved_inc.type, "FLOOD")
            
            engine2.dispose()
            
        finally:
            # Cleanup
            try:
                if os.path.exists(temp_db_path):
                    os.remove(temp_db_path)
            except Exception as e:
                print(f"Cleanup warning: {e}")

if __name__ == '__main__':
    unittest.main()
