import pytest
from datetime import datetime, timezone
from app.models.incident import Incident, Location

def get_sample_incident_001() -> Incident:
    return Incident(
        incident_id="SAMPLE-001",
        type="PERSON",
        confidence=0.94,
        timestamp=datetime.now(timezone.utc),
        location=Location(x=10.5, y=20.1, z=5.0),
        range=8.4,
        spatial_status="LOCATED",
        spatial_confidence=0.91,
        status="NEW"
    )

def get_sample_incident_002() -> Incident:
    return Incident(
        incident_id="SAMPLE-002",
        type="PERSON",
        confidence=0.81,
        timestamp=datetime.now(timezone.utc),
        location=None,
        range=None,
        spatial_status="UNAVAILABLE",
        spatial_confidence=None,
        status="NEW"
    )

def get_sample_incident_003() -> Incident:
    return Incident(
        incident_id="SAMPLE-003",
        type="PERSON",
        confidence=0.88,
        timestamp=datetime.now(timezone.utc),
        location=Location(x=15.0, y=10.0, z=2.0),
        range=12.1,
        spatial_status="ESTIMATED",
        spatial_confidence=0.63,
        status="NEW"
    )
