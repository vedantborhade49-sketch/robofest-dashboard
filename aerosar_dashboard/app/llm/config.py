import os
from pydantic import BaseModel

class LLMConfig(BaseModel):
    provider: str = os.getenv("LLM_PROVIDER", "mock")
    model_name: str = os.getenv("LLM_MODEL_NAME", "mock-rag-llm")
    api_key: str = os.getenv("LLM_API_KEY", "")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "500"))
