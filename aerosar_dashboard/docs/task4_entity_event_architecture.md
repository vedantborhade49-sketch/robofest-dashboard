# AEROSAR Task 4 Architecture: Entity & Event Registry

This document outlines the architecture for Phase 2 of Task 4: converting raw CV detections into persistent Entities and Anomaly Events, while preserving the existing IncidentEngine pipeline.

## 1. Database & Persistence Layer
We introduced two new primary models alongside existing models in `app/database/models.py`.

### Entity Model
Persistent identity for physical entities observed in the real world (e.g., `PERSON_001`).
* **Fields**: `entity_id`, `entity_type`, `first_seen`, `last_seen`, `first_frame_id`, `last_frame_id`, `sighting_count`, `confidence`, `status`, `image_path` (best crop), `metadata`.
* **Repository**: `EntityRepository` (`app/database/entity_repository.py`) handles CRUD operations.

### Anomaly Event Model
Persistent record of an anomalous behavior tied to an entity (e.g., `PERSON_DETECTED` for `PERSON_001`).
* **Fields**: `event_id`, `event_type`, `entity_id`, `status`, `first_seen`, `last_seen`, `first_frame_id`, `last_frame_id`, `confidence`, `spatial_information`, `metadata`.
* **Repository**: `AnomalyEventRepository` (`app/database/anomaly_event_repository.py`) handles CRUD operations.

## 2. Business Logic Registries
We created two registry services to handle in-memory mapping, deduplication, and persistence abstraction.

### EntityRegistry (`app/perception/entity_registry.py`)
- **Lifecycle**: Receives a `Detection` and frame image. Resolves the detection to either an existing `Entity` or creates a new one.
- **EntityMatcher**: Currently implements a simplistic spatial-temporal heuristic (bounding box center distance over a 5-second window). If matched, updates counters (`sighting_count`, timestamps). If not matched, returns `UNKNOWN` leading to a new entity creation.
- **Best Crop Extraction**: The registry calculates bounding box area and compares confidence. If the new detection provides a better view, it extracts a crop via `cv2.imwrite` and updates the entity's `image_path`.

### EventRegistry (`app/incidents/event_registry.py`)
- **Lifecycle**: Receives `(Detection, Entity)` pairs from the `EntityRegistry`. Evaluates the anomaly type using an `AnomalyEngine`.
- **Deduplication**: Resolves to an existing `AnomalyEvent` if one is active for the specific `entity_id` and `event_type`. Thus, 500 repeated detections of `PERSON_001` result in a single `PERSON_DETECTED` event that is continually `UPDATED`.
- **Resolution**: Features a `resolve_grace_period` (10s). If an event is not seen within this window, it transitions to `RESOLVED`.

## 3. IncidentEngine Integration
The `PerceptionWorker` (`app/perception/qt_worker.py`) has been carefully refactored to intercept the raw detections, pass them through the new Entity and Event layers, and then feed the resulting insights into the existing `SpatialAssociation` and `IncidentEngine` flow. 

**Data Flow**:
1. `PerceptionService` yields `Detection`s.
2. `EntityRegistry` processes `Detection` -> `Entity`.
3. `EventRegistry` processes `Entity` -> `AnomalyEvent`.
4. The trio `(Detection, Entity, AnomalyEvent)` is mapped against `SpatialStateHistory` to generate `SpatialAssociation`.
5. The `(Detection, SpatialAssociation)` tuples are fed transparently to `IncidentEngine.process_associations()`.
6. Existing Tasks 1-3 behavior is fully preserved.

## 4. Future Re-ID Extension
The `EntityMatcher.match()` abstraction is designed as an isolated boundary. Future phases can implement actual computer vision embedding generation, facial recognition, or re-identification logic inside `match()` without changing the repository or registry plumbing.
