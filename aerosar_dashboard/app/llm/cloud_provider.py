import json
import logging
from openai import OpenAI
from app.llm.provider import LLMProvider
from app.llm.models import LLMResponse
from app.llm.config import LLMConfig

logger = logging.getLogger(__name__)

import os

class CloudLLMProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = self.config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("CloudLLMProvider initialized without an API key. Generation will likely fail.")
            
        base_url = None
        if os.getenv("GEMINI_API_KEY") or "gemini" in self.config.model_name.lower():
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            # We use the structured outputs feature if available.
            response = self.client.beta.chat.completions.parse(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=LLMResponse,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            parsed_response = response.choices[0].message.parsed
            if parsed_response:
                return parsed_response
            else:
                raise ValueError("Parsed response is None")
        except Exception as e:
            logger.error(f"Cloud LLM generation failed: {e}")
            raise RuntimeError(f"Cloud LLM Error: {e}") from e
