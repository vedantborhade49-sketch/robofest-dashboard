# AEROSAR Task 3 — Spatial Codebase Audit

## A. Existing Spatial Architecture (`app/spatial/`)
The spatial backend is driven by the `SpatialService` which wraps a `LiDARProvider` and `SLAMProvider`. 
This service is explicitly synchronized into the `StateManager` by the `CentralUpdateLoop` (which ticks every 500ms via `QTimer` inside `app/core/update_loop.py`). 
This means the entire spatial state update (LiDAR parsing, Obstacle Extraction, and SLAM updates) currently runs synchronously on the main GUI thread, unlike YOLO (which is backgrounded via `QThread`).

## B. Existing Spatial Models (`app/models/spatial.py`)
The system defines a comprehensive set of spatial models, though many fields are currently stubbed:
*   `SpatialState`: The root state object holding `latest_scan`, `obstacles`, `local_position`, `current_pose`, `trajectory`, `local_map`, and sensor status.
*   `Pose`: Vehicle pose containing `x`, `y`, `z` (meters) and `roll`, `pitch`, `yaw` (radians).
*   `SpatialTarget`: Represents a localized target containing `frame_id`, `x`, `y`, `z`, and `range`.
*   `LocalPosition`, `LiDARScan`, `LiDARPoint`, `Obstacle`, `OccupancyGrid`, `CameraGeometry`, `DetectionGeometry`.

## C. SLAM Provider Implementations
Found in `app/spatial/slam_provider.py`.
*   `SLAMProvider`: Abstract base interface.
*   `RealSLAMProvider`: A placeholder implementation that raises `NotImplementedError("RealSLAMProvider: Cannot start breezyslam without real hardware")`. It immediately returns `ERROR_NO_HARDWARE` for its status and does not compute real trajectories.

## D. LiDAR Provider Implementations
Found in `app/spatial/provider.py`.
*   `LiDARProvider`: Abstract base interface.
*   `RealLiDARProvider`: Hardcoded to look for `/dev/ttyUSB0`. If hardware is missing, it raises `NotImplementedError("RealLiDARProvider: Hardware not available...")`.

## E. Mock/Stub Usage
Due to the lack of hardware implementations, the system entirely relies on mock providers for the dashboard UI.
*   `tests/mocks/mock_slam_provider.py`: Provides a simulated SLAM path (a predefined figure-8 trajectory) to test map rendering.
*   `tests/mocks/mock_lidar_provider.py`: Simulates simple point clouds.
The `DataService` instantiates these mocks when initialized in test/mock mode.

## F. Spatial Synchronization Mechanism (Temporal Association)
**TEMPORAL ASSOCIATION: MISSING / FLAWED.**
There is currently no temporal synchronization between the CV pipeline and the Spatial pipeline.
In `app/core/qt_worker.py`, the `PerceptionWorker` (YOLO) runs asynchronously on a background thread. When it finishes a frame, it passes the `CVResult` back to the main thread. Before generating the `Incident`, the main thread fetches the *latest available* `SpatialState` directly from the `StateManager`:
```python
# qt_worker.py
spatial_state = state.spatial if state else None
incidents = self._incident_engine.process_detections(detections, spatial_state)
```
This means a 500ms delayed video frame will be spatially localized against the drone's position *right now*, causing projection errors proportional to the drone's speed. `NetworkFrame.timestamp` is never matched against `SpatialState.timestamp`.

## G. Coordinate Frames
*   **Camera Frame**: `Z` forward, `X` right, `Y` down.
*   **LiDAR / `base_link`**: `X` forward, `Y` left, `Z` up (Standard robotics).
*   **World / `map`**: Translated and rotated via SLAM `Pose.yaw`.
*   **UI / Screen Frame**: Evaluated in `mission_map.py` where `+Y` points North/Up.

## H. UI Integration
The UI correctly handles missing spatial data. 
Widgets like `mission_map.py`, `map_info_panel.py`, and `telemetry_panels.py` check `incident.location` or `state.spatial.slam_status`. 
If `incident.location` is `None`, the UI gracefully degrades (e.g. `mission_map.py` skips drawing the target). The detail panels explicitly render `LOCAL SLAM: UNAVAILABLE`.

## I. Hardware Dependencies
The system explicitly requires a real LiDAR device attached at `/dev/ttyUSB0` to use `RealLiDARProvider`, and expects an underlying BreezySLAM C-extension for `RealSLAMProvider`. Currently, neither can run without connected hardware.

## J. Incident Location Integration
The spatial association logic exists in `app/spatial/locator.py` (`SpatialLocator`):
1. `IncidentEngine.process_detection` calculates the bottom-center pixel of the bounding box.
2. It passes these pixel coordinates to `SpatialLocator.locate_target`.
3. `locate_target` transforms the 2D pixel to a 3D camera ray using intrinsic camera geometry.
4. The camera ray is transformed to a LiDAR ray via `CameraToLiDARTransform` (assumes camera is mounted slightly above and forward of the LiDAR).
5. The LiDAR ray is geometrically associated with the `latest_scan` to estimate `target_range`.
6. The target is projected into `base_link` (LiDAR frame).
7. If SLAM is `TRACKING`, the target is transformed via `current_pose` into the `map` coordinate frame and appended to the `Incident` as an `ESTIMATED` location.
