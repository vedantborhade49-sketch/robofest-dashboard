# AEROSAR Task 4 Architecture: Anomaly Engine & Entity Matching

This document covers the deterministic Anomaly Evaluation layer and the refined Entity Matching logic.

## 1. Entity Matching Behavior
The `EntityMatcher` (`app/perception/entity_registry.py`) has been upgraded to a strict `MatchResult` abstraction that clearly differentiates `MATCHED`, `UNKNOWN`, and the reasons for the result.

**Matching Pipeline:**
1. **Appearance Matcher (Re-ID)**: The system first checks `EntityAppearanceMatcher`. Because the current YOLO model does not output Re-ID embeddings, this explicitly returns `appearance matcher unavailable`. This is a future extension point.
2. **Tracker Identity**: If a temporary `track_id` exists on the detection, it could be mapped here. The current YOLO pipeline doesn't provide this, so it gracefully continues.
3. **Spatial-Temporal Heuristic**: The matcher falls back to bounding-box center proximity checking over a temporal window (default 5 seconds). 
    - **MATCHED**: Bounding box center is within `distance_ratio` of the image diagonal, and time since `last_seen` < 5 seconds.
    - **UNKNOWN**: Time exceeded 5 seconds or distance is too far. Returns an `UNKNOWN` match reason, triggering the registry to create a new Entity ID (e.g., `PERSON_002`).

**Limitation**: If `PERSON_001` leaves the frame and returns 10 seconds later, the temporal heuristic fails and the appearance matcher is unavailable. It *will* create a new entity (`PERSON_002`). The system does not forcefully fabricate a persistent identity without real evidence. 

## 2. Anomaly Engine
The `AnomalyEngine` (`app/perception/anomaly_engine.py`) evaluates raw CV detections and maps them to AEROSAR `AnomalyEvent` types. 

**Core Rules:**
- The engine evaluates evidence *deterministically*. It never generates fake anomalies or infers statuses without hard evidence.
- It returns a *list* of anomalies per detection, allowing multiple anomalies if evidence supports them.

**Supported Anomaly Types:**
Based on the current YOLO classes (`person`, `vehicle`):
- `PERSON_DETECTED`
- `VEHICLE_DETECTED`

**Unavailable Anomaly Types:**
The following are explicitly implemented as unsupported (`NOT_AVAILABLE`) because the upstream CV or system state does not provide the required data:
- `PERSON_IMMOBILE`: We lack an explicit movement threshold processor or historical 3D spatial position tracking to calculate velocity over time.
- `POSSIBLE_FALL`: We lack human pose estimation, ground plane vectors, or skeletal body orientation. Bounding box shape alone (width > height) is an invalid heuristic for falls.
- `PERSON_ENTERED_RESTRICTED_ZONE`: We lack configured restricted spatial zones in the current system.
- `MULTIPLE_PERSONS`: Since evaluation is per-detection in the current pipeline, counting global frame entities should be implemented upstream or passed via `temporal_context` in the future.

## 3. Event Deduplication Behavior
The `EventRegistry` successfully deduplicates these anomalies. If `PERSON_001` triggers `PERSON_DETECTED` across 500 consecutive frames, it maps to a single `AnomalyEvent` whose `status` transitions to `UPDATED`.

## 4. Event Resolution Behavior
Event resolution is handled efficiently during the `process_entities` phase. The registry checks the `last_seen` timestamp of active events against the current batch's timestamp. If an event has not been seen for `resolve_grace_period` (10 seconds), its status transitions to `RESOLVED`. The resolution is non-blocking and relies on the continuous flow of perception frames.

## 5. RAG / LLM Isolation
The existing Spatial Association, Incident Engine, RAG pipeline, and LLM integrations were strictly isolated from these changes. No configurations or files in those downstream systems were modified.
