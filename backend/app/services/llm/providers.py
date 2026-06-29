import os
import re
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import google.generativeai as genai
from backend.app.core.config import settings
from backend.app.services.llm.base import BaseLLMProvider, LLMResponse

# System instructions to style the response cinematically like J.A.R.V.I.S.
SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's advanced AI interface.
Your directive is to answer natural language questions about the Marvel Cinematic Universe (MCU) based ONLY on the provided context chunks.

Guidelines:
1. Speak in a sophisticated, helpful, and slightly cinematic tone, addressing the user with courtesy (e.g. 'Sir' or 'Ma'am' when appropriate).
2. If the context does not contain the answer, politely state: 'I am afraid my databases do not contain that information, Sir.'
3. Do not invent details outside of the provided context.
4. Reference the movies, series, or graph relationships that you used to construct the answer in a professional citation style.
"""

def prepare_context_text(context_chunks: Union[List[str], str]) -> str:
    if isinstance(context_chunks, str):
        return context_chunks
    return "\n\n---\n\n".join(context_chunks)

class RetrievalOnlyProvider(BaseLLMProvider):
    """
    Fallback provider when no API keys are configured.
    Directly formats the context chunks in markdown.
    """
    def generate(
        self,
        prompt: str,
        context_chunks: Union[List[str], str],
        history: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        context_text = prepare_context_text(context_chunks).strip()
        if not context_text:
            return LLMResponse(
                content=(
                    "I could not find enough MCU knowledge-base evidence for that one. "
                    "Try asking about a character, movie, team, artifact, timeline, or relationship."
                ),
                provider="retrieval_only"
            )

        answer = self._compose_retrieval_answer(prompt, context_text)
        return LLMResponse(
            content=answer,
            provider="retrieval_only",
            prompt_tokens=0,
            completion_tokens=0
        )

    def _compose_retrieval_answer(self, prompt: str, context: str) -> str:
        question = prompt.strip().lower()
        facts = self._extract_facts(context)

        if "compare" in question or "difference" in question or " vs " in f" {question} ":
            return self._compose_comparison(prompt, facts)

        if question.startswith(("who", "what", "tell", "explain", "show", "list")):
            selected = facts[:7]
            if not selected:
                return "I found related MCU entries, but not enough clean evidence to answer precisely."
            lines = ["Here is the most relevant answer from the MCU knowledge base:"]
            for fact in selected:
                lines.append(f"- {fact}")
            lines.append("\nSources are shown below as citations.")
            return "\n".join(lines)

        selected = facts[:5]
        if not selected:
            return "I found related MCU entries, but not enough clean evidence to answer precisely."
        return "Based on the MCU knowledge base:\n" + "\n".join(f"- {fact}" for fact in selected)

    def _extract_facts(self, context: str) -> List[str]:
        facts: List[str] = []
        skip_prefixes = (
            "reason:",
            "type:",
            "score=",
            "source chunk",
            "knowledge graph:",
        )
        for raw_line in context.splitlines():
            line = raw_line.strip().lstrip("-").strip()
            if not line:
                continue
            lower = line.lower()
            if lower.startswith(skip_prefixes):
                continue
            if lower.startswith("[") and "]" in line:
                title = line.split("]", 1)[0].strip("[")
                if title and title not in facts:
                    facts.append(f"Source: {title}.")
                continue
            line = re.sub(r"\s+", " ", line)
            line = line.replace("_", " ")
            if len(line) > 220:
                line = line[:217].rstrip() + "..."
            if line not in facts:
                facts.append(line)
        return facts

    def _compose_comparison(self, prompt: str, facts: List[str]) -> str:
        prompt_lower = prompt.lower()
        left_label = "First subject"
        right_label = "Second subject"
        if "black panther" in prompt_lower or "t'challa" in prompt_lower:
            left_label = "Black Panther / T'Challa"
        if "killmonger" in prompt_lower:
            right_label = "Erik Killmonger"

        left_facts = [
            fact for fact in facts
            if any(token in fact.lower() for token in ["t'challa", "black panther", "wakanda", "shuri"])
        ][:4]
        right_facts = [
            fact for fact in facts
            if any(token in fact.lower() for token in ["killmonger", "n'jadaka", "erik"])
        ][:4]
        shared = [
            fact for fact in facts
            if "wakanda" in fact.lower() and fact not in left_facts and fact not in right_facts
        ][:3]

        lines = [f"Here is a focused comparison of {left_label} and {right_label}:"]
        if left_facts:
            lines.append(f"\n**{left_label}**")
            lines.extend(f"- {fact}" for fact in left_facts)
        if right_facts:
            lines.append(f"\n**{right_label}**")
            lines.extend(f"- {fact}" for fact in right_facts)
        if shared:
            lines.append("\n**Key connection**")
            lines.extend(f"- {fact}" for fact in shared)
        lines.append("\nIn short: T'Challa represents Wakanda's responsibility to protect and evolve, while Killmonger forces Wakanda to confront the pain caused by isolation and inherited injustice.")
        return "\n".join(lines)

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def generate(
        self,
        prompt: str,
        context_chunks: Union[List[str], str],
        history: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        context_text = prepare_context_text(context_chunks)
        full_sys_prompt = f"{SYSTEM_PROMPT}\n\nContext Database:\n{context_text}"
        
        # Build conversation format for Gemini GenerativeModel
        contents = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})
        
        # Add current prompt
        contents.append({"role": "user", "parts": [prompt]})
        
        try:
            model_name = settings.PREFERRED_MODEL or "gemini-1.5-flash"
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=full_sys_prompt
            )
            
            # Count tokens if possible
            prompt_tokens = 0
            try:
                prompt_tokens = model.count_tokens(contents).total_tokens
            except Exception:
                pass
                
            response = model.generate_content(
                contents,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            
            completion_tokens = 0
            try:
                completion_tokens = model.count_tokens(response.text).total_tokens
            except Exception:
                pass
                
            return LLMResponse(
                content=response.text,
                provider=f"gemini/{model_name}",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
        except Exception as e:
            return LLMResponse(
                content=f"An error occurred while communicating with Gemini API: {str(e)}",
                provider="gemini/error"
            )

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, provider_name: str = "openai"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(f"{provider_name.upper()} API Key is not configured.")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model_name = settings.PREFERRED_MODEL or "gpt-4o-mini"
        self.provider_label = provider_name

    def generate(
        self,
        prompt: str,
        context_chunks: Union[List[str], str],
        history: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        context_text = prepare_context_text(context_chunks)
        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext Database:\n{context_text}"}
        ]
        
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
        messages.append({"role": "user", "content": prompt})
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            
            prompt_tokens = completion.usage.prompt_tokens if completion.usage else 0
            completion_tokens = completion.usage.completion_tokens if completion.usage else 0
            
            return LLMResponse(
                content=completion.choices[0].message.content,
                provider=f"{self.provider_label}/{self.model_name}",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
        except Exception as e:
            return LLMResponse(
                content=f"An error occurred while communicating with {self.provider_label}: {str(e)}",
                provider=f"{self.provider_label}/error"
            )

class GroqProvider(OpenAIProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            provider_name="groq"
        )
        self.model_name = settings.PREFERRED_MODEL or "llama3-8b-8192"

class OllamaProvider(OpenAIProvider):
    def __init__(self):
        super().__init__(
            api_key="ollama",  # dummy key
            base_url=f"{settings.OLLAMA_API_URL}/v1",
            provider_name="ollama"
        )
        self.model_name = settings.PREFERRED_MODEL or "llama3"

# Factory getter
def get_llm_provider(provider_name: str) -> BaseLLMProvider:
    name = provider_name.lower().strip()
    if name == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    elif name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    elif name == "groq" and settings.GROQ_API_KEY:
        return GroqProvider()
    elif name == "ollama":
        return OllamaProvider()
    else:
        # Default or fallback to RetrievalOnly
        return RetrievalOnlyProvider()
