# AEROSAR Task 4 Audit: Anomaly & Event Memory → RAG

## 1. Current Architecture Flow
Based on the codebase audit, the current pipeline from CV to RAG operates as follows:

1. **CV Processing**: `PerceptionWorker` invokes `PerceptionService.run_once()` which returns a list of `Detection`s.
2. **Spatial Association**: Inside `PerceptionWorker.capture_and_process()`, each `Detection` is immediately associated with a `SpatialState` (fetched via `SpatialStateHistory` using `det.timestamp`) to form a `SpatialAssociation`.
3. **Incident Generation**: The list of `(Detection, SpatialAssociation)` tuples is passed to `IncidentEngine.process_associations()`.
4. **Deduplication**: `IncidentEngine._is_duplicate(det)` applies a rudimentary spatial-temporal deduplication purely based on 2D bounding box centers and a 5-second time window. If not a duplicate, a new `Incident` object (Status = `NEW`) is created and cached in `_active`.
5. **Persistence**: `PerceptionWorker` calls `DataService.add_incident()` to save the incident to the DB (`IncidentModel`) and broadcast a UI event.
6. **Intelligence / RAG**: Separately, when a report is requested, `IntelligenceService.generate_incident_report(incident)` passes the `Incident` to `RAGService.retrieve_for_incident()`, then to `LLMService.generate_report()`, persisting a `ReportModel` and emitting a websocket event.

## 2. Missing Concepts (Task 4 Target)
The system currently jumps straight from raw 2D `Detection`s to persistent `Incident`s. The following layers are completely missing:
- **ENTITY**: No persistent entity tracking or re-identification across frames (e.g. assigning a unique ID to a person across 10 frames).
- **ANOMALY**: No logic to determine if an entity's behavior constitutes an anomaly.
- **EVENT (CV Anomaly Event)**: Currently, the only `Event` (`app/models/event.py`) is a system log event (`INFO`, `ERROR`, etc.). There is no persistent CV Event model representing an anomaly instance.

## 3. Implementation Plan Requirements
To implement the desired pipeline without breaking Tasks 1-3, we must insert the new layers into `PerceptionWorker` (or a dedicated `IntelligenceWorker`), adhering to the target pipeline:
`CVResult -> Entity Tracking -> Anomaly Engine -> Event Registry -> Spatial Association -> Insight -> IncidentEngine`

### 3.1 Constraints & Invariants (FROZEN Tasks 1-3)
- `IncidentEngine` and its `Incident` outputs must remain structurally intact.
- `RAGService` and `LLMService` must continue to operate downstream.
- RAG must not invent facts.

### 3.2 Required Modules
1. **Entity Tracker**: Assigns tracking IDs to consecutive detections using IoU or distance heuristics.
2. **Anomaly Engine**: Evaluates tracked entities (e.g., speed, duration, location) to flag anomalies.
3. **Event Registry**: Deduplicates and stores persistent anomalies as events before they become incidents.
4. **Insight Adapter**: Bridges the new Event model into the existing `IncidentEngine` (e.g., by presenting the event as an `Insight` or highly-confident aggregated `Detection`).

## 4. Next Steps
1. Create models for `Entity` and `AnomalyEvent`.
2. Implement `EntityTracker` (in memory).
3. Implement `AnomalyEngine` (rule-based).
4. Implement `EventRegistry` (in memory / DB persistence).
5. Modify `PerceptionWorker` to route `CVResult` through these engines *before* invoking `SpatialAssociation` and `IncidentEngine`.
