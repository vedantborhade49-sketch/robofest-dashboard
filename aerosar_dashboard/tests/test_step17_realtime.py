import pytest
import asyncio
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.api.app import app
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType, RealTimeEvent
from app.services.incident_service import IncidentService
from app.models.incident import Incident, Location
from app.models.evidence import Evidence, EvidenceType
from app.database.database import init_db
from PySide6.QtCore import QTimer, QCoreApplication
import sys
from datetime import datetime

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_env():
    # Setup async loop for event bus
    loop = asyncio.new_event_loop()
    event_bus.set_loop(loop)
    
    # Mock the database repository but keep get_incident returning what we pass
    with patch("app.services.incident_service.Repository"):
        yield
    
    loop.close()

def test_websocket_connection_and_broadcast():
    with client.websocket_connect("/api/v1/ws") as websocket:
        assert len(event_bus.connection_manager.active_connections) == 1
        
        # Test event broadcasting manually since TestClient loops can cause deadlocks
        event = RealTimeEvent(event_type=EventType.SYSTEM_EVENT, payload={"message": "hello"})
        
        # Run broadcast directly
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(event_bus.connection_manager.broadcast(event))
        
        data = websocket.receive_json()
        assert data["event_type"] == "SYSTEM_EVENT"
        assert data["payload"]["message"] == "hello"
        
    assert len(event_bus.connection_manager.active_connections) == 0

@patch("app.services.incident_service.event_bus.publish")
def test_incident_created_event(mock_publish):
    service = IncidentService()
    incident = Incident(
        incident_id="INC-TEST-01",
        mission_id="SAR-001",
        type="PERSON",
        location=Location(x=0, y=0, z=0),
        confidence=0.9,
        timestamp=datetime.now()
    )
    
    service.create_incident(incident)
    mock_publish.assert_called_once()
    args, kwargs = mock_publish.call_args
    assert args[0] == EventType.INCIDENT_CREATED
    assert kwargs["payload"]["incident"]["incident_id"] == "INC-TEST-01"

@patch("app.services.incident_service.event_bus.publish")
def test_incident_status_changed_event(mock_publish):
    service = IncidentService()
    incident = Incident(
        incident_id="INC-TEST-02",
        mission_id="SAR-001",
        type="PERSON",
        location=Location(x=0, y=0, z=0),
        confidence=0.9,
        status="NEW",
        timestamp=datetime.now()
    )
    service.create_incident(incident)
    
    
    mock_publish.reset_mock()
    with patch.object(service, 'get_incident', return_value=incident):
        service.update_status("INC-TEST-02", "REVIEW")
        
    mock_publish.assert_called_once()
    args, kwargs = mock_publish.call_args
    assert args[0] == EventType.INCIDENT_STATUS_CHANGED
    assert kwargs["payload"]["incident_id"] == "INC-TEST-02"
    assert kwargs["payload"]["old_status"] == "NEW"
    assert kwargs["payload"]["new_status"] == "REVIEW"

@patch("app.services.incident_service.event_bus.publish")
def test_evidence_created_event(mock_publish, tmp_path):
    service = IncidentService()
    incident = Incident(
        incident_id="INC-TEST-03",
        mission_id="SAR-001",
        type="PERSON",
        location=Location(x=0, y=0, z=0),
        confidence=0.9,
        timestamp=datetime.now()
    )
    service.create_incident(incident)
    
    # Set controlled evidence directory
    service.evidence_service.base_dir = tmp_path
    evidence_path = tmp_path / "test.jpg"
    evidence_path.write_text("dummy image data")
    
    evidence = Evidence(
        evidence_id="EV-TEST-01",
        incident_id="INC-TEST-03",
        type=EvidenceType.FRAME,
        file_path=str(evidence_path)
    )
    
    mock_publish.reset_mock()
    with patch.object(service, 'get_incident', return_value=incident):
        service.attach_evidence("INC-TEST-03", evidence)
        
    mock_publish.assert_called_once()
    args, kwargs = mock_publish.call_args
    assert args[0] == EventType.EVIDENCE_CREATED
    assert kwargs["payload"]["incident_id"] == "INC-TEST-03"
    assert kwargs["payload"]["evidence_id"] == "EV-TEST-01"

def test_realtime_client_mock_mode():
    from app.ui.realtime_client import RealtimeClient
    
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
        
    rt_client = RealtimeClient("ws://localhost:8000/ws")
    rt_client.set_mock_mode(True)
    
    rt_client.connect_to_server()
    # Shouldn't try to connect, so it remains disconnected
    assert rt_client._is_connected == False
    assert rt_client.reconnect_timer.isActive() == False
