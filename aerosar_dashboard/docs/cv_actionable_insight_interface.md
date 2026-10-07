# CV to Actionable Insight Interface

## Architecture

The AEROSAR dashboard architecture implements a strict boundary between computer vision inference and actionable insight generation. This ensures that the downstream Intelligence layers (RAG and LLM) do not need to understand CV internals, and the system can seamlessly switch or stack detection models.

```text
NetworkFrame
 ↓
CVProcessor (Implementation e.g., YOLOProcessor)
 ↓
CVResult (Normalized output containing DetectionResults)
 ↓
InsightAdapter
 ↓
IncidentEngine (Validates, deduplicates, suppresses)
 ↓
Incident
 ↓
IntelligenceService
 ↓
RAG (Context retrieval using metadata)
 ↓
LLM (Prompt construction & summarization)
 ↓
Report (Final human-readable summary)
```

## Contracts

### 1. NetworkFrame
A stable, frozen contract representing a decoded video frame with corresponding metadata.
*   **Properties:** `frame_id`, `timestamp`, `image` (numpy array), `camera_id`, `metadata`.

### 2. CVProcessor
An abstract base class (`ABC`) defining the generic contract for CV processing algorithms.
*   **Purpose:** Takes a `NetworkFrame` and returns a `CVResult`.
*   **Method:** `process(self, frame: NetworkFrame) -> CVResult`. Does not raise raw exceptions; handles errors gracefully by returning a populated `error` field in the result.

### 3. CVResult
A strongly typed model (`Pydantic`) representing the outcome of processing a single frame.
*   **Properties:** `frame_id`, `timestamp`, `detections: List[DetectionResult]`, `processing_time`, `model_name`, `model_version`, `error`, `metadata`.
*   **Note:** Contains 0 or more detections. An empty `detections` list is a perfectly valid state.

### 4. DetectionResult
A normalized, CV-level representation of an object detection.
*   **Properties:** `class_name`, `confidence`, `bbox`, `class_id`, `track_id`, `metadata`.

### 5. InsightAdapter
A bridge adapter that takes a `CVResult` and the original `NetworkFrame`, extracting and mapping the structured CV output to the existing AEROSAR `Detection` representation required by `IncidentEngine`.
*   **Purpose:** Preserves provenance (timestamps, frame IDs). Connects CV output directly into the existing validation and deduplication pipeline.

## Responsibilities

*   **CV Layer (CVProcessor / CVResult):**
    "What is visible?" Identifies objects, bounding boxes, and confidences in the current frame. Does not make operational decisions.

*   **Incident Engine:**
    "Is this actionable?" Validates, suppresses duplicates, and assesses temporal consistency. Responsible for emitting a unified `Incident`.

*   **RAG (Retrieval-Augmented Generation):**
    "What operational knowledge applies?" Fetches standard operating procedures, hazard data, and contextual manuals based on the `Incident` parameters (e.g., location, type). 

*   **LLM (Large Language Model):**
    "How should this be summarized for the operator?" Merges the structured incident data and RAG context into a cohesive human-readable `Report`.

## Non-responsibilities

*   **CV does not control the drone.** It only outputs semantic perception tags.
*   **CV does not generate flight commands.**
*   **CV does not invent coordinates.** (Must respect the "Real Data or Explicitly Unavailable" constraint).
*   **RAG does not analyze raw images.** It only interacts with structured text keywords and metadata derived from the `Incident`.
*   **LLM does not replace sensor measurements** or hallucinate metrics.
*   **LLM does not control the drone.**
*   **CVResult is not automatically an incident.** `IncidentEngine` determines if a detection is actionable.
