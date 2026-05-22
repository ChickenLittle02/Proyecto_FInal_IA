"""
Wrapper básico para la configuración de un LLM y envío de prompts.
"""
import os
from typing import Dict, Optional

from .prompts import coherence_prompt, fragment_prompt
from .cache import LLMCache


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_path: Optional[str] = None,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4.1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.cache = LLMCache(cache_path or ".llm_cache.json")

    def score_fragment(self, fragment) -> float:
        prompt = fragment_prompt(fragment.text)
        response = self._model_call(prompt)
        return self._parse_score(response)

    def score_coherence(self, first_fragment, second_fragment) -> float:
        prompt = coherence_prompt(first_fragment.text, second_fragment.text)
        response = self._model_call(prompt)
        return self._parse_score(response)

    def _model_call(self, prompt: str) -> str:
        cached = self.cache.get(prompt)
        if cached is not None:
            return cached
        response = self._invoke_model(prompt)
        self.cache.set(prompt, response)
        return response

    def _invoke_model(self, prompt: str) -> str:
        # Placeholder para integrar la API real del proveedor.
        # En día 1 bastará con esta abstracción; luego se conecta a OpenAI, Anthropic, Ollama, etc.
        return "0.0"

    @staticmethod
    def _parse_score(response: str) -> float:
        try:
            return float(response.strip())
        except ValueError:
            return 0.0
