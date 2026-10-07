import json
from app.llm.provider import LLMProvider
from app.llm.models import LLMResponse
from app.llm.config import LLMConfig

class MockLLMProvider(LLMProvider):
    """
    Mock implementation of LLMProvider for testing and offline development.
    Returns deterministic responses based on the input prompts.
    """
    
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        # Simple extraction logic for the mock to seem somewhat dynamic
        # Note: A real LLM would use the system_prompt and output JSON directly.
        incident_type = "Unknown Incident"
        confidence_str = "0.0%"
        has_context = "No additional context" not in user_prompt
        
        for line in user_prompt.split('\n'):
            if line.startswith("Incident Type:"):
                incident_type = line.split(":", 1)[1].strip()
            elif line.startswith("Confidence:"):
                confidence_str = line.split(":", 1)[1].strip()
                
        try:
            conf_val = float(confidence_str.strip('%')) / 100.0
        except ValueError:
            conf_val = 0.0

        observations = [
            f"{incident_type} detection recorded.",
            f"Detection confidence: {confidence_str}."
        ]
        
        if "Location: Unavailable" in user_prompt:
            observations.append("Exact spatial coordinates unavailable.")
            
        contextual_info = []
        if has_context:
            contextual_info.append("Retrieved guidance relevant to detection.")
            
        operator_actions = [
            "Verify the evidence image.",
            "Review the incident on the mission map when spatial information is available."
        ]

        # Construct the structured output
        return LLMResponse(
            summary=f"{incident_type} detected in the search area with a confidence of {confidence_str}.",
            observations=observations,
            contextual_information=contextual_info,
            recommended_operator_actions=operator_actions,
            severity="MEDIUM" if conf_val < 0.9 else "HIGH",
            confidence=conf_val
        )
