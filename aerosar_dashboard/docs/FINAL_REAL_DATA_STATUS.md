# FINAL REAL DATA STATUS

This document reflects the exact status of the AEROSAR Ground Station components. Per the REAL DATA CONTRACT, no modules silently fall back to mock data. If hardware or a capability is missing, it is explicitly marked as unavailable or offline.

## System Components

- **Camera**: LIVE (USB Webcam connected on index 0)
- **Computer Vision**: LIVE (YOLO processing frame-by-frame)
- **Entity Tracking (Registry)**: LIVE (SQLite tracking, saving filesystem crops in `data/entities`)
- **Anomaly Engine**: LIVE (Rules-based event generation based on entities)
- **Spatial / LiDAR**: UNAVAILABLE (Explicitly stubbed, hardware missing)
- **Drone Telemetry**: UNAVAILABLE (Fails to connect/awaiting real MAVLink stream on UDP)
- **Generative AI (RAG / Reports)**: LIVE (Gemini API via CloudLLMProvider)
- **Database (Persistence)**: LIVE (SQLite storing Incidents, Reports, Events, Entities)
- **Dashboard UI**: LIVE (PySide6 consuming strictly REAL or UNAVAILABLE data, never MOCK)

## Evidence Pipeline
- Incident creation directly saves the actual video frame from the USB Webcam to the `evidence/YYYY/MM/DD/INC-...` directory with associated metadata.

## Contract Compliance
- No mocked video frames.
- No mocked detections.
- No simulated drone positions fed into the spatial service if LiDAR is missing.
- Telemetry explicitly shows OFFLINE/UNAVAILABLE instead of simulating a flight path.
