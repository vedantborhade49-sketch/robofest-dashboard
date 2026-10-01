# REAL CAMERA TEST

## AEROSAR — REAL CAMERA + YOLO + INCIDENT VALIDATION

This document tracks the first physical perception validation pipeline (Camera -> OpenCV -> YOLO -> Incident Engine -> Dashboard).

### Configuration Details
1. **Camera used:** (e.g., Laptop Webcam)
2. **Camera resolution:** (e.g., 1280x720)
3. **Camera FPS:** (e.g., 30)
4. **YOLO model used:** `yolov8n.pt`
5. **Model classes:** `person`
6. **Confidence threshold:** 0.5
7. **Inference device:** CPU (or CUDA if configured)
8. **Average inference FPS:** 
9. **Average latency:** 
10. **CPU usage:** 
11. **RAM usage:** 
12. **Detection results:** 
13. **Incident results:** 
14. **Evidence results:** 
15. **Database results:** 
16. **WebSocket results:** 
17. **Dashboard results:** 
18. **Failure tests:** 
19. **Long-run results:** 
20. **Issues discovered:** 
21. **Issues fixed:** 
22. **Remaining limitations:** 

---

### Test Matrix

| Test                  | Expected           | Actual | Status |
| --------------------- | ------------------ | ------ | ------ |
| Camera initialization | Camera opens       |        | PENDING |
| Frame capture         | Frames arrive      |        | PENDING |
| YOLO loading          | Model loads        |        | PENDING |
| Person detection      | Person detected    |        | PENDING |
| Bounding box          | Correct box        |        | PENDING |
| Confidence            | Valid confidence   |        | PENDING |
| Incident creation     | Incident generated |        | PENDING |
| Evidence              | Evidence stored    |        | PENDING |
| Database              | Incident persisted |        | PENDING |
| Dashboard             | Incident visible   |        | PENDING |
| WebSocket             | Real-time update   |        | PENDING |
| Camera disconnect     | Graceful failure   |        | PENDING |
| Camera reconnect      | Recovery           |        | PENDING |
| No detection          | No false incident  |        | PENDING |
| Multiple people       | Correct behavior   |        | PENDING |
| Long run              | Stable             |        | PENDING |

---

### Conclusion
*(To be written after test completion)*
