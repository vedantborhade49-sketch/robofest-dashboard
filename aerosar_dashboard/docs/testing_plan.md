# AEROSAR Testing Plan

## 1. Objective
This plan outlines the testing ladder designed to systematically validate the AEROSAR system starting from simulated software up to physical field tests. It defines the formal structure required before moving to subsequent levels.

## 2. Test Ladder

### LEVEL 1 — SOFTWARE ONLY
*   **Description**: Validates the complete architecture without hardware using mock providers.
*   **Criteria**: Mock Camera -> Mock YOLO -> Detection -> Incident Engine -> Mock Spatial Data -> Mock Telemetry -> Communication -> Ground Station -> Dashboard -> RAG -> LLM.

### LEVEL 2 — LAPTOP + REAL CAMERA
*   **Description**: Uses a laptop USB/webcam to test the perception pipeline.
*   **Criteria**: Must show live camera, bounding boxes, classes, confidence, FPS, and inference status when a person is detected.

### LEVEL 3 — CAMERA → INCIDENT
*   **Description**: Validates incident creation from live camera feeds.
*   **Criteria**: When a person is detected, an `Incident` is generated with valid metadata and appears in the dashboard.

### LEVEL 4 — CAMERA + EVIDENCE
*   **Description**: Validates evidence attachment.
*   **Criteria**: Incident creation triggers evidence capture. Tests missing images and storage failures to ensure incidents are still preserved.

### LEVEL 5 — CAMERA + LIDAR
*   **Description**: Combines perception and mock/physical LiDAR for range estimation.
*   **Criteria**: Verifies that range estimates are attached to incidents without generating arbitrary coordinates if association is unreliable.

### LEVEL 6 — CAMERA + LIDAR + SLAM
*   **Description**: Tests spatial incident localization.
*   **Criteria**: Mission map must display UAV pose, trajectory, LiDAR points, and incident locations, clearly distinguishing `GROUND TRUTH` from `SLAM ESTIMATE`.

### LEVEL 7 — RASPBERRY PI CAMERA TEST
*   **Description**: Moves perception to the actual onboard companion computer (Pi 5).
*   **Criteria**: Measure FPS, CPU, RAM, temperature, and latency.

### LEVEL 8 — RASPBERRY PI + LIDAR + SLAM
*   **Description**: Tests hardware sensors together on the Pi.
*   **Criteria**: Checks sensor timestamps, coordinate frames, and map updates.

### LEVEL 9 — RASPBERRY PI + ARDUPILOT
*   **Description**: Tests MAVLink telemetry mapping.
*   **Criteria**: Verifies normalization of altitude, position, heading, battery, etc., without sending flight commands.

### LEVEL 10 — RASPBERRY PI → GROUND STATION
*   **Description**: Validates end-to-end communication from the Pi.
*   **Criteria**: All messages (telemetry, incidents, spatial, health, events) must reach the ground dashboard successfully.

## 3. Resilience and Failure Scenarios
*   **Communication Loss**: Must buffer incidents and synchronize on reconnect without duplication.
*   **Camera Failure**: System degrades but telemetry and comms continue. Recovers on reconnect.
*   **LiDAR Failure**: Incident engine continues, spatial localization drops.
*   **SLAM Loss**: Preserves previous state, clearly displays degraded spatial status.
*   **MAVLink Failure**: Dashboard continues to function based on available data.
*   **RAG/LLM Failure**: System handles failures gracefully without crashing.

## 4. End-to-End Mission Validation
A controlled scenario where a simulated rescue target is found, an incident is created, localized, stored, communicated, displayed, and an AI report is generated.

## 5. Performance Baselines
We will log metrics including capture FPS, inference FPS, latency across the pipeline, and retrieval/generation times.
