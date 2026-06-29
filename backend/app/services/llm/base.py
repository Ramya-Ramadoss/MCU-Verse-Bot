from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class LLMResponse:
    def __init__(self, content: str, provider: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.content = content
        self.provider = provider
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        context_chunks: Union[List[str], str],
        history: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generates a natural language response given a prompt, query context chunks,
        and conversation history.
        """
        pass
