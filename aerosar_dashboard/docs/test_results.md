# AEROSAR Test Results

## 1. Test Summary
*   **Total Tests Documented**: 15
*   **Passed**: 12
*   **Failed**: 0
*   **Blocked**: 0
*   **Pending (Hardware)**: 3

## 2. Simulated & Local Software Tests (LEVEL 1-6, 10-12)
These tests validate the architecture, mock pipelines, UI, and data integration without requiring physical drones.

| Test ID | Test Name | Expected Result | Actual Result | Status | Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-SIM-001** | Mock Camera → YOLO | Bounding boxes produced from mock images | Valid detections with confidence | PASS | SIMULATED |
| **TEST-SIM-002** | YOLO → Incident Engine | Detection triggers `Incident` creation | Incident metadata correctly stored | PASS | SIMULATED |
| **TEST-SIM-003** | Evidence Capture | Incident creation saves associated frame | Image path attached and resolvable | PASS | SIMULATED |
| **TEST-SIM-004** | Spatial Pipeline (Mock LiDAR) | Detections mapped to 3D coordinates | Coordinates generated and attached | PASS | SIMULATED |
| **TEST-SIM-005** | SLAM Status Map | Trajectory and targets display on Map | `GROUND TRUTH` and `ESTIMATE` shown | PASS | SIMULATED |
| **TEST-SIM-006** | Comms Disconnect | Incidents buffered locally on Pi | Ground receives synced data on reconnect | PASS | SIMULATED |
| **TEST-SIM-007** | RAG Integration | Retrieval of context for an incident | RAG snippets generated and stored | PASS | SIMULATED |
| **TEST-SIM-008** | LLM Integration | Generated report from context | Formatted rescue report returned | PASS | SIMULATED |
| **TEST-SIM-009** | Sensor Failure | Missing LiDAR preserves Incident | Incident created with `UNAVAILABLE` spatial | PASS | SIMULATED |
| **TEST-SIM-010** | End-to-End Simulation | Data flows from Pi -> API -> UI | Dashboard fully populates live | PASS | SIMULATED |
| **TEST-LAP-001** | Laptop WebCam Perception | Live inference bounding boxes overlay | Bounding box, confidence overlay visible | PASS | LOCAL SOFTWARE |
| **TEST-LAP-002** | Restart Recovery | Local storage persists across reboot | SQLite databases reconnect and load | PASS | LOCAL SOFTWARE |

## 3. Real Hardware Tests (LEVEL 7-9)
These tests require physical sensors and Raspberry Pi 5 to be fully validated.

| Test ID | Test Name | Expected Result | Actual Result | Status | Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-HW-001** | Pi Camera Performance | Pi maintains > 5 FPS YOLO inference | (Pending Hardware) | NOT TESTED | REAL HARDWARE |
| **TEST-HW-002** | Pi LiDAR & SLAM | Sensor fusion creates accurate Map | (Pending Hardware) | NOT TESTED | REAL HARDWARE |
| **TEST-HW-003** | MAVLink Telemetry (Pi) | Serial link acquires accurate heading/alt | (Pending Hardware) | NOT TESTED | REAL HARDWARE |

## 4. Performance Measurements (Baselines)
*(All measurements below are SIMULATED baseline averages)*
*   **Camera Capture FPS**: ~30 FPS (Mock Video Source)
*   **YOLO Inference Latency**: ~45ms (Laptop CPU/Mock)
*   **Incident Engine Latency**: ~2ms
*   **Pi → Ground Communication Latency**: ~5ms (Localhost WebSocket)
*   **Dashboard Rendering Latency**: ~10ms (PyQt6 signals)
*   **RAG Retrieval Latency**: ~150ms (ChromaDB + SentenceTransformers)
*   **LLM Report Generation**: ~2.5s (Mock LLM response delay)

## 5. Known Limitations
*   **Hardware Validation**: Cannot fully guarantee Pi 5 thermal throttling or CSI bandwidth limitations until `TEST-HW-001` is run.
*   **Camera Occlusion**: Heavy occlusion still produces false negatives, requiring temporal smoothing.
*   **LiDAR Range Limits**: Mock provider assumes perfect depth, real physical sensors will have noise which the SLAM pipeline must filter.

## 6. Ready-For-Flight Status
*   **SOFTWARE VALIDATED**: ✅ YES
*   **HARDWARE VALIDATED**: ❌ NO
*   **FIELD VALIDATED**: ❌ NO
*   **FLIGHT VALIDATED**: ❌ NO

The AEROSAR system is ready to be physically deployed onto the UAV for Hardware and Field testing.
