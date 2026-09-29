from abc import ABC, abstractmethod
from app.llm.models import LLMResponse
from app.llm.config import LLMConfig

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Ensures that different models (Mock, Cloud, Local) implement the same generation interface.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Takes a system prompt and a user prompt, returning a structured LLMResponse.
        """
        pass
