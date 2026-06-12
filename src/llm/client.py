"""
Wrapper para la configuración del LLM y envío de prompts.

Soporta:
- gemini: Google Gemini (google-generativeai)
- openai / groq: APIs compatibles con OpenAI (OpenAI, Groq, etc.)
"""
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI, RateLimitError

from .prompts import coherence_prompt, fragment_prompt, summary_evaluation_prompt
from .cache import LLMCache

# Cargar variables de entorno desde el archivo .env
load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_COMPATIBLE_PROVIDERS = {"openai", "groq"}


@dataclass(frozen=True)
class SummaryEvaluation:
    """Puntuaciones macro de un resumen completo (relevancia, coherencia, global)."""

    relevance: float
    coherence: float
    overall: float


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._openai_client: Optional[OpenAI] = None

        if self.provider == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
        elif self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
            if self.provider == "groq" and not self.base_url:
                self.base_url = GROQ_BASE_URL
            if self.api_key:
                self._openai_client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url or None,
                )
        else:
            raise ValueError(
                f"Proveedor LLM no soportado: {self.provider!r}. "
                f"Usa uno de: gemini, openai, groq."
            )

        self.cache = LLMCache(cache_path or ".llm_cache.json")

    @property
    def api_key_env_name(self) -> str:
        if self.provider == "gemini":
            return "GEMINI_API_KEY"
        return "OPENAI_API_KEY"

    def score_fragment(self, fragment) -> float:
        prompt = fragment_prompt(fragment.text)
        response = self._model_call(prompt)
        return self._parse_score(response)

    def score_coherence(self, first_fragment, second_fragment) -> float:
        prompt = coherence_prompt(first_fragment.text, second_fragment.text)
        response = self._model_call(prompt)
        return self._parse_score(response)

    def evaluate_summary(self, summary_text: str, max_duration: float) -> SummaryEvaluation:
        """Evalúa relevancia, coherencia y calidad global de un resumen completo."""
        prompt = summary_evaluation_prompt(summary_text, max_duration)
        response = self._model_call(prompt)
        return self._parse_summary_evaluation(response)

    def _model_call(self, prompt: str) -> str:
        cached = self.cache.get(prompt)
        if cached is not None:
            return cached
        response = self._invoke_model(prompt)
        self.cache.set(prompt, response)
        return response

    def _courtesy_delay(self) -> float:
        if self.provider == "gemini":
            return 1.0
        if self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return 2.1
        return 0.0

    def _invoke_model(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._invoke_gemini(prompt)
        if self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return self._invoke_openai_compatible(prompt)
        return "0.0"

    def _invoke_gemini(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Error: GEMINI_API_KEY no está configurada en las variables de entorno o archivo .env"
            )
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(self._courtesy_delay())
                model = genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_text = str(e)
                if "429" in error_text and attempt < max_retries - 1:
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_text, re.IGNORECASE)
                    wait_seconds = float(retry_match.group(1)) + 1 if retry_match else 35
                    print(f"Rate limit alcanzado, reintentando en {wait_seconds:.0f}s...")
                    time.sleep(wait_seconds)
                    continue
                print(f"Error llamando a la API de Gemini: {e}")
                return "0.0"
        return "0.0"

    def _invoke_openai_compatible(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Error: OPENAI_API_KEY no está configurada en las variables de entorno o archivo .env"
            )
        if self._openai_client is None:
            raise ValueError("Cliente OpenAI-compatible no inicializado.")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(self._courtesy_delay())
                response = self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                content = response.choices[0].message.content
                return content if content else "0.0"
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_seconds = 35
                    print(f"Rate limit alcanzado, reintentando en {wait_seconds:.0f}s...")
                    time.sleep(wait_seconds)
                    continue
                print(f"Error llamando a la API OpenAI-compatible (rate limit): {e}")
                return "0.0"
            except Exception as e:
                print(f"Error llamando a la API OpenAI-compatible: {e}")
                return "0.0"
        return "0.0"

    @staticmethod
    def _parse_score(response: str) -> float:
        try:
            # Buscar el primer número entero o decimal entre 0.0 y 1.0 en la respuesta del modelo
            match = re.search(r'\b(0(\.\d+)?|1(\.0+)?)\b', response)
            if match:
                return float(match.group(0))
            return float(response.strip())
        except ValueError:
            return 0.0

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _extract_scores_from_numbers(text: str) -> Optional[SummaryEvaluation]:
        numbers = [float(match) for match in re.findall(r"\b(?:0\.\d+|1(?:\.0+)?|0)\b", text)]
        if len(numbers) >= 3:
            return SummaryEvaluation(
                relevance=LLMClient._clamp_score(numbers[0]),
                coherence=LLMClient._clamp_score(numbers[1]),
                overall=LLMClient._clamp_score(numbers[2]),
            )
        if len(numbers) == 1:
            value = LLMClient._clamp_score(numbers[0])
            return SummaryEvaluation(relevance=value, coherence=value, overall=value)
        return None

    @classmethod
    def _parse_summary_evaluation(cls, response: str) -> SummaryEvaluation:
        text = response.strip()
        if not text or text == "0.0":
            return SummaryEvaluation(0.0, 0.0, 0.0)

        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if isinstance(data, dict):
                    return SummaryEvaluation(
                        relevance=cls._clamp_score(float(data.get("relevance", 0.0))),
                        coherence=cls._clamp_score(float(data.get("coherence", 0.0))),
                        overall=cls._clamp_score(float(data.get("overall", 0.0))),
                    )
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        from_numbers = cls._extract_scores_from_numbers(text)
        if from_numbers is not None:
            return from_numbers

        overall = cls._parse_score(text)
        return SummaryEvaluation(relevance=overall, coherence=overall, overall=overall)
