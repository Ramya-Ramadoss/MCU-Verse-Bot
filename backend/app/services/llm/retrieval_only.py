from backend.app.services.llm.base import BaseLLMProvider, LLMResponse


class RetrievalOnlyProvider(BaseLLMProvider):
    name = "retrieval_only"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, context: str, temperature: float = 0.7) -> LLMResponse:
        answer = self._compose_answer(prompt, context)
        return LLMResponse(content=answer, provider=self.name)

    def _compose_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return (
                "I couldn't find relevant information in the MCU knowledge base for that question. "
                "Try rephrasing or asking about a specific character, movie, or event."
            )
        return (
            f"Based on the MCU knowledge base:\n\n{context.strip()}\n\n"
            f"This answer was generated using retrieval-only mode (no external LLM configured)."
        )
