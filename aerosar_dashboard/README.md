# STALLION AEROSAR — Ground Station Dashboard

This is the Ground Station Dashboard for the STALLION AEROSAR project (autonomous search-and-rescue drone operating in GPS-denied/confined environments).

## Current Development Stage
**Phase 20**: Full RAG + Real LLM Integration. The system now includes a complete intelligence pipeline connecting incident detection with an AI-assisted RAG reporting module and a realtime dashboard.

## Technology Stack
- **Python 3.11+**
- **PySide6** (Qt6 for UI)
- **FastAPI & Uvicorn** (Backend API)
- **SQLAlchemy** (SQLite Persistence)
- **Pydantic** (Data modeling)
- **WebSockets** (Realtime sync)
- **OpenAI** (LLM Provider Integration)

## Architecture Overview
The application follows a clean modular architecture ensuring the UI does not directly depend on the data source.
`UI -> Data Service -> REST/WebSockets -> FastAPI Backend -> Database / LLM Pipeline`

### AEROSAR Intelligence Pipeline
The intelligence reporting workflow provides context-aware synthesis of detected facts for human operators.

1. **Detection**: Drone payload identifies a potential target.
2. **Incident**: Basic facts (Type, Confidence, Location, Frame) are transmitted and persisted as a `NEW` incident.
3. **RAG (Retrieval-Augmented Generation)**: The `RAGService` chunks and indexes operational manuals, extracting contextual guidelines relevant to the incident.
4. **Retrieved Context**: The most relevant pieces of knowledge are retrieved.
5. **LLM**: The `LLMService` formats the incident facts and retrieved context, safely instructing the language model to synthesize a report.
6. **Report**: A structured report is generated, validated, and saved.

## Configuration & Environment Variables

Configure the Intelligence Pipeline using environment variables. Credentials should NEVER be committed to Git.

- `LLM_PROVIDER`: Set to `mock` (default) for local testing or `cloud` for real integration.
- `LLM_MODEL_NAME`: e.g., `gpt-4o`
- `LLM_API_KEY`: Your provider API secret key.
- `LLM_TEMPERATURE`: e.g. `0.0`
- `LLM_MAX_TOKENS`: e.g. `500`

### Real LLM Provider
When `LLM_PROVIDER=cloud`, the system uses the `CloudLLMProvider` which interfaces with OpenAI's structured outputs SDK.

### Mock Provider (Fallback)
When `LLM_PROVIDER=mock`, the system uses the `MockLLMProvider` which instantly returns simulated responses. This allows automated CI testing and offline development without occurring API costs.

## API & WebSockets

### Report Generation Endpoint
**POST** `/api/v1/incidents/{incident_id}/generate-report`
Triggers the full intelligence pipeline and returns a structured AI report. 

### WebSocket Event
**REPORT_GENERATED**
Upon successful completion, the backend broadcasts a JSON payload. The dashboard (DataService) listens for this event to proactively fetch the new report and update the UI without manual refreshing.

## Installation & Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the backend API server and the dashboard UI:
```bash
python main.py
```

## Testing

To run standard unit tests (uses `mock` provider):
```bash
python -m unittest discover tests
```

To run the full Real LLM integration test:
```bash
# Set your API credentials first
export LLM_PROVIDER=cloud
export LLM_API_KEY="your-secret-key"
export RUN_LLM_INTEGRATION_TEST=true

python -m unittest tests.test_step20_intelligence
```

## Detection -> Spatial Localization Architecture
The system integrates visual detections (YOLO) with LiDAR and SLAM spatial data to produce Spatially Located Incidents.

```text
YOLO Detection
      ↓
Camera Geometry
      ↓
LiDAR Association
      ↓
Target Position
      ↓
Sensor Transform
      ↓
SLAM Pose
      ↓
Map Position
      ↓
Spatial Incident
```

### Camera Geometry
The `CameraGeometry` abstraction normalizes pixel detections using configurable camera intrinsics (fx, fy, cx, cy). It projects bounding box points (e.g., bottom-center) into 3D normalized rays in the camera coordinate frame (Z forward, X right, Y down).

### Sensor Coordinate Frames & Camera-LiDAR Transformation
The `CameraToLiDARTransform` module maps camera rays into the local LiDAR frame (X forward, Y left, Z up). This allows synthetic calibration and testing decoupled from physical extrinsics, and prepares the vector for spatial association.

### LiDAR Association & Range Estimation
When a detection ray is projected into the LiDAR frame, the `SpatialLocator` searches for LiDAR returns near the expected ray (using a configurable angular tolerance). A robust median estimator filters out noise from candidate points to determine an accurate `range` and `spatial_confidence`.

### Base_Link & SLAM Map Transformation
1. **Base_Link Transform:** The estimated range and ray calculate a local `(X,Y,Z)` position in the sensor/base_link frame.
2. **SLAM/Map Transform:** When SLAM tracking is active, the system transforms the base_link target into global map coordinates using the current `Pose` (yaw rotation and position offset).

### Spatial Incident Model & Failure Cases
The central `Incident` model has been extended with spatial metadata: `location`, `spatial_status`, `position_frame`, `range`, and `spatial_confidence`. 

Failure scenarios are handled gracefully:
- **SLAM LOST:** If localization is lost, incidents are recorded with `ESTIMATED` sensor-relative coordinates, while map position remains unavailable. 
- **LiDAR Failure:** If no points match, the system sets `UNAVAILABLE` spatial status and still logs the visual incident to avoid dropping detections.

### Simulation & Accuracy Evaluation
A mock spatial state pipeline simulates real target detection by projecting ground-truth drone positions and returning correlated LiDAR points. Accuracy evaluation computes absolute distance errors between known ground-truth locations and the SLAM-estimated spatial target.
