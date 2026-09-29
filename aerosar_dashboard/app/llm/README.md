# AEROSAR LLM Intelligence Module

## Why AEROSAR Uses an LLM
The AEROSAR system relies on highly structured and complex data streams from sensors (camera, LiDAR, telemetry) processed by edge AI (YOLO, OpenCV) and matched against the AEROSAR Knowledge Base (using the standalone RAG engine). However, emergency/search-and-rescue operators need rapid, comprehensible summaries of situations. The LLM module serves strictly to synthesize structured data and contextual text into an easy-to-read, actionable human report. 

## What the LLM Receives
1. **Structured AEROSAR Incidents**: Verified facts like detection confidence, bounding boxes, object types, status, and precise XYZ location data.
2. **Retrieved RAG Context**: Trusted domain-specific search-and-rescue guidance retrieved from the local knowledge base based on the incident query.

## What the LLM Does
* Converts the structured inputs into a deterministic, human-readable markdown report.
* Outlines observed facts alongside contextual information and operator considerations.
* Emphasizes the exact confidence of detections and indicates when information (like spatial coordinates) is unavailable.

## What the LLM Must NEVER Do
* **Never invent facts**: It must not hallucinate people, coordinates, telemetry, or sensor readings.
* **Never issue autonomous commands**: It has no access to MAVLink, ArduPilot, or flight controls.
* **Never make irreversible decisions**: It generates a report for an operator; it does not automatically dismiss or resolve incidents.
* **Never claim confirmed victims**: A detected person is simply a "detected person" until an operator verifies.
* **Never claim injuries**: Unless explicitly provided in the retrieved context or metadata.

## Architecture

### Provider Abstraction (`LLMProvider`)
The system abstracts the underlying model behind a generic `LLMProvider` interface. This allows AEROSAR to easily swap out implementations (Mock, Cloud APIs, Local Models) without modifying the core pipeline or locking into a specific vendor.

### Mock Provider (`MockLLMProvider`)
By default, AEROSAR uses a `MockLLMProvider`. This ensures that the dashboard, backend, and entire RAG+LLM orchestration pipeline can run locally and be fully tested offline without requiring API keys, network access, or incurring costs. It generates deterministic responses by scraping keywords out of the prompt.

### Report Schema (`LLMResponse`)
LLM outputs are requested and strictly validated as JSON matching the `LLMResponse` Pydantic schema:
- `summary` (str)
- `observations` (List[str])
- `contextual_information` (List[str])
- `recommended_operator_actions` (List[str])
- `severity` (str)
- `confidence` (float)

This structured data is then serialized into markdown and injected into the broader `Report` model (`ai_report` field) for persistence and dashboard display.

### Prompt Architecture (`prompts.py`)
Prompts are isolated from the service code.
* **System Prompt**: Defines the strict boundary conditions (no hallucinations, no drone control, tone, and JSON structure).
* **User Prompt**: Constructed via `build_prompt()`, safely injecting the verified Incident and Retrieved Context data. 

### Configuration (`LLMConfig`)
The provider type, model name, temperatures, timeouts, and API keys are injected via environment variables (e.g. `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_TEMPERATURE`). Code never hardcodes secrets.

## Testing
Tests exist in `tests/test_step19_llm.py` and validate:
- Hallucination prevention (ensuring no coordinates are invented).
- Handling of missing contexts or missing coordinates.
- Structured Pydantic validation (catching bad LLM responses).
- Provider failures (timeouts).
- Mock execution end-to-end.

## Future Integration (Step 20)
Currently, this is a standalone LLM module. Step 20 will orchestrate the complete pipeline:
`Incident → RAG Engine → RAG Result → LLM Service → Report → Database → Dashboard`
The endpoints and websocket sync for full automated or on-demand generation will be finalized at that time.
