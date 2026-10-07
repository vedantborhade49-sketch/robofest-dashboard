# AEROSAR Codebase Onboarding - Task 2 Architecture Map

## 1. Current Architecture

```text
NetworkFrame (app/perception/types.py)
    ↓
PerceptionWorker (app/perception/qt_worker.py) / PerceptionService (app/perception/perception_service.py)
    ↓
YOLODetector (app/perception/detector.py) -> returns raw dict
    ↓
process_raw_detections (app/perception/detection_processor.py)
    ↓
Detection (app/perception/models.py)
    ↓
IncidentEngine (app/incidents/incident_engine.py)
    ↓
Incident (app/models/incident.py)
    ↓
DataService (app/services/data_service.py) / Repository (app/database/repository.py)
    ↓
IntelligenceService (app/intelligence/service.py)
    ↓
RAGService (app/rag/rag_service.py)
    ↓
LLMService (app/llm/service.py)
    ↓
Report (app/models/report.py)
```

## 2. Existing Reusable Components

| Component | File | Purpose | Reuse for Task 2 |
|---|---|---|---|
| `NetworkFrame` | `app/perception/types.py` | Represents a decoded video frame with timestamp/camera metadata. | EXISTS, DO NOT TOUCH |
| `Detection` | `app/perception/models.py` | Generic bounding box + confidence struct. | REUSABLE |
| `BBox` | `app/perception/models.py` | Subcomponent of Detection. | REUSABLE |
| `IncidentEngine` | `app/incidents/incident_engine.py` | Validates detections, suppresses duplicates, creates Incidents. | REUSABLE |
| `Incident` | `app/models/incident.py` | Core actionable intelligence struct. | EXISTS, DO NOT TOUCH |
| `Evidence` | `app/models/evidence.py` | Holds snapshot metadata (file_path, frame_id). | REUSABLE |
| `DataService` | `app/services/data_service.py` | Entrypoint for persisting incidents and dispatching to LLM/UI. | EXISTS, DO NOT TOUCH |
| `RAGService` | `app/rag/rag_service.py` | Given an Incident, builds query & fetches context. | EXISTS, DO NOT TOUCH |
| `LLMService` | `app/llm/service.py` | Prompts LLM with Incident + Context -> Report. | EXISTS, DO NOT TOUCH |

## 3. Existing Data Models

- **`NetworkFrame`** (Dataclass): `frame_id: int`, `timestamp: datetime`, `image: np.ndarray`, `camera_id: str`, `metadata: dict`.
- **`Detection`** (Pydantic): `detection_id`, `timestamp`, `frame_id`, `class_id`, `class_name`, `confidence`, `bbox`, `source`.
- **`Incident`** (Pydantic): `incident_id`, `type`, `confidence`, `timestamp`, `location`, `status`, `evidence_image`.
- **`Evidence`** (Pydantic): `evidence_id`, `incident_id`, `timestamp`, `type`, `file_path`, `frame_id`.
- **`Report`** (Pydantic): AI-generated final summary containing `ai_report`, `confidence`, `human_review_status`.
- **`IncidentModel`, `ReportModel`, `EvidenceModel`** (SQLAlchemy): Corresponding DB schemas.

## 4. Current Data Flow

1. `FrameReceiver` (TCP loop) generates `NetworkFrame` and stores it safely.
2. `LiveFeedView` spawns a `QThread` running `PerceptionWorker`.
3. `PerceptionWorker` pulls `NetworkFrame` via `PerceptionService.run_once()`.
4. `PerceptionService` feeds `YOLODetector.predict(frame)`.
5. `YOLODetector` returns raw dictionaries like `{"class_name": "person", "confidence": 0.9, ...}`.
6. `process_raw_detections` converts these dicts into Pydantic `Detection` objects.
7. `PerceptionWorker` passes `Detection` list to `IncidentEngine.process_detections()`.
8. `IncidentEngine` performs basic distance/timing duplicate suppression and maps classes (e.g. "person" -> "PERSON_DETECTED"). It emits `Incident` objects.
9. `PerceptionWorker` loops over generated incidents and commits them via `DataService.add_incident()`.
10. `IntelligenceService` intercepts the incident, fetches RAG context using `QueryBuilder(incident)`, calls the LLM, and creates a `Report`.

## 5. Current Gaps

- **Missing `CVProcessor` interface:** Currently, `PerceptionService` is hardcoded tightly to `YOLODetector`. There is no abstract base class representing generic CV operations.
- **Missing `CVResult` struct:** The `YOLODetector` outputs raw Python dictionaries instead of a strongly typed result class.
- **Lack of clean Adapter Boundary:** `process_raw_detections` acts as an ad-hoc adapter but expects the exact dictionary schema YOLO outputs.
- **Evidence Gap:** `IncidentEngine` creates incidents but doesn't capture the `NetworkFrame` image into an `Evidence` object or persist a snapshot to disk. The `evidence_image` field remains `None`.

## 6. Recommended Task 2 Integration Boundary

To prevent modifying Task 1 TCP layers and to preserve the existing Incident infrastructure, the Backend Architect should introduce the following boundaries:

```python
# app/perception/processor.py
from abc import ABC, abstractmethod
from typing import List

class CVResult(BaseModel):
    # Normalized structure containing bounding boxes, class names, masks, etc.
    ...

class CVProcessor(ABC):
    @abstractmethod
    def process(self, frame: NetworkFrame) -> List[CVResult]:
        pass
```

And an adapter layer:

```python
# app/perception/insight_adapter.py
class InsightAdapter:
    @staticmethod
    def to_detections(results: List[CVResult], frame: NetworkFrame) -> List[Detection]:
        # Converts normalized CVResults into the existing AEROSAR Detection structure
        pass
```
The `PerceptionService` would be refactored *only* to consume the generic `CVProcessor` and `InsightAdapter`, remaining entirely decoupled from YOLO specifics.

## 7. Risks

- **Coupled CV Execution:** `PerceptionWorker` runs inference inside the QThread. For heavy models, this might lag. The bounded frame buffer in Task 1 protects the TCP loop, but latency could still rise.
- **Duplicate Identifiers:** `IncidentEngine` currently uses simple bounding box distance formulas. Complex scenes may yield duplicates if not tuned correctly.
- **Evidence Leakage:** We must ensure the `image` (`np.ndarray`) is snapshot safely and removed from memory immediately. It should NEVER be pushed down into RAG/LLM payloads.

## 8. Files that should NOT be modified (FROZEN)

- `app/communication/frame_receiver.py` (Task 1 Complete)
- `app/communication/frame_sender.py`
- `app/data/api_provider.py`
- `app/ui/realtime_client.py`
- `app/rag/*`
- `app/llm/*`
- Any Central Video Distributor files.
