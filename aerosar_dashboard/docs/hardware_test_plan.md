# AEROSAR Hardware Test Plan

## 1. Overview
This plan specifies the testing procedures for integrating and validating physical sensors and compute hardware within the AEROSAR ecosystem.

## 2. Hardware Test Protocol

### 2.1 Raspberry Pi 5 Compute Tests
*   **Objective**: Establish baseline performance limits.
*   **Procedures**: 
    1. Run YOLO inference loop continuously for 15 minutes.
    2. Monitor thermal output, memory consumption, and CPU throttling.
    3. Measure maximum sustainable FPS under load.

### 2.2 Camera Verification (CSI/USB)
*   **Objective**: Validate real-world capture properties.
*   **Procedures**:
    1. Test capture latency and resolution constraints.
    2. Test low-light conditions and occlusion scenarios.
    3. Monitor for dropped frames or buffer overflows during continuous operation.

### 2.3 LiDAR Sensor Verification
*   **Objective**: Validate point cloud density and driver compatibility.
*   **Procedures**:
    1. Map physical driver output to `MockLiDARProvider` expected data structures.
    2. Validate maximum range and angular resolution measurements.
    3. Disconnect/reconnect during operation to verify recovery handles.

### 2.4 ArduPilot MAVLink Integration
*   **Objective**: Confirm reliable read-only telemetry acquisition.
*   **Procedures**:
    1. Connect physical Serial Rx/Tx between Pi and ArduPilot.
    2. Validate baud rate and message frequency (Heartbeat, Attitude, Global_Position_Int).
    3. Ensure no flight-control commands are accidentally broadcast by the onboard node.

## 3. Acceptable Hardware Tolerances
*   **Thermal**: Must not exceed 85°C on the Pi during inference.
*   **Latency**: End-to-end hardware perception (Camera -> YOLO) must remain under 300ms.
*   **Telemetry**: Must receive minimum 5Hz updates from MAVLink.

## 4. Hardware Failure Emulation
Physically disconnect cables (USB, Serial, Power) during active operation to confirm the software `ReadinessManager` accurately reflects `DISCONNECTED` or `DEGRADED` states.
