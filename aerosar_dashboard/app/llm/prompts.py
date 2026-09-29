from app.models.incident import Incident
from app.rag.models import RAGResult

SYSTEM_PROMPT = """You are the AEROSAR incident-reporting assistant.
Your job is to transform structured incident information and retrieved trusted context into a concise operator-facing report.

Rules:
1. Use only supplied incident information and retrieved context.
2. Never invent facts, coordinates, telemetry, or sensor readings.
3. Clearly distinguish detected facts from contextual guidance.
4. Never claim that a person is injured unless explicitly provided in the data.
5. Never claim that a detected person is a confirmed victim. Use words like 'detected person' or 'individual'.
6. Never issue autonomous flight commands.
7. Never change mission state.
8. Never override human operators.
9. If information is missing, explicitly state that it is unavailable.
10. Keep reports concise and operationally useful.
11. Preserve confidence values and source information.
12. Do not hallucinate coordinates or telemetry.

Return your response strictly as a JSON object matching the requested schema.
"""

def build_prompt(incident: Incident, retrieved_context: RAGResult) -> str:
    """Builds a formatted prompt from an incident and retrieved context."""
    
    # Format Incident Data
    location_str = "Unavailable"
    if incident.location:
        location_str = f"X: {incident.location.x}, Y: {incident.location.y}, Z: {incident.location.z}"
    
    incident_text = f"Incident Type: {incident.type}\n"
    incident_text += f"Confidence: {incident.confidence * 100:.1f}%\n"
    incident_text += f"Timestamp: {incident.timestamp}\n"
    incident_text += f"Location: {location_str}\n"
    incident_text += f"Status: {incident.status}\n"
    
    # Format Context Data
    context_text = ""
    if not retrieved_context or not retrieved_context.retrieved_context:
        context_text = "No additional context retrieved."
    else:
        for idx, ctx in enumerate(retrieved_context.retrieved_context):
            context_text += f"[Context {idx+1}]: {ctx.content}\n"

    prompt = (
        "Please generate an incident report based on the following information.\n\n"
        "--- DETECTED FACTS ---\n"
        f"{incident_text}\n"
        "--- RETRIEVED CONTEXT ---\n"
        f"{context_text}\n"
    )
    
    return prompt
