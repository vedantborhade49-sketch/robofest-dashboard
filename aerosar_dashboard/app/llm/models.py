from pydantic import BaseModel, Field
from typing import List

class LLMResponse(BaseModel):
    """
    Structured response expected from the LLM provider.
    """
    summary: str = Field(..., description="A short summary of the incident")
    observations: List[str] = Field(default_factory=list, description="List of factual observations based only on the incident data")
    contextual_information: List[str] = Field(default_factory=list, description="List of relevant context points retrieved from the knowledge base")
    recommended_operator_actions: List[str] = Field(default_factory=list, description="Recommended actions for the operator")
    severity: str = Field(default="UNKNOWN", description="Assessed severity (e.g., LOW, MEDIUM, HIGH, CRITICAL)")
    confidence: float = Field(default=0.0, description="Overall confidence of the assessment")

    def to_markdown(self) -> str:
        """
        Converts the structured response into a human-readable markdown format suitable for the existing ai_report field.
        """
        md = f"**INCIDENT SUMMARY**\n{self.summary}\n\n"
        
        md += "**OBSERVATIONS (DETECTED FACTS)**\n"
        if not self.observations:
            md += "- None\n"
        for obs in self.observations:
            md += f"- {obs}\n"
            
        md += "\n**CONTEXTUAL INFORMATION**\n"
        if not self.contextual_information:
            md += "- None\n"
        for ctx in self.contextual_information:
            md += f"- {ctx}\n"
            
        md += "\n**OPERATOR CONSIDERATIONS**\n"
        if not self.recommended_operator_actions:
            md += "- None\n"
        for act in self.recommended_operator_actions:
            md += f"- {act}\n"
            
        md += f"\n**SEVERITY**: {self.severity}"
        md += f"\n**ASSESSMENT CONFIDENCE**: {self.confidence:.2f}"
        return md
