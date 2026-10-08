import json
import logging
import os
import anthropic
from app.llm.provider import LLMProvider
from app.llm.models import LLMResponse
from app.llm.config import LLMConfig

logger = logging.getLogger(__name__)

class CloudLLMProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("CloudLLMProvider initialized without an ANTHROPIC_API_KEY. Generation will likely fail.")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            schema = LLMResponse.model_json_schema()
            
            tool = {
                "name": "generate_incident_report",
                "description": "Generate a structured incident report.",
                "input_schema": schema,
            }
            
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens or 1024,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                tools=[tool],
                tool_choice={"type": "tool", "name": "generate_incident_report"}
            )
            
            tool_call = next((block for block in response.content if block.type == "tool_use"), None)
            if not tool_call:
                raise ValueError("Model did not return a tool call.")
            
            return LLMResponse(**tool_call.input)
            
        except Exception as e:
            logger.error(f"Cloud LLM generation failed: {e}")
            raise RuntimeError(f"Cloud LLM Error: {e}") from e
