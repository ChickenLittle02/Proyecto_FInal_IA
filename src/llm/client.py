"""
Wrapper para la configuración del LLM de Gemini y envío de prompts.
"""
import os
import re
import time
from typing import Dict, Optional

from dotenv import load_dotenv
import google.generativeai as genai

from .prompts import coherence_prompt, fragment_prompt
from .cache import LLMCache

# Cargar variables de entorno desde el archivo .env
load_dotenv()


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_path: Optional[str] = None,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self.model = model or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        
        # Configurar la API de Gemini si corresponde
        if self.provider == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
        else:
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
        if self.provider == "gemini":
            if not self.api_key:
                raise ValueError("Error: GEMINI_API_KEY no está configurada en las variables de entorno o archivo .env")
            try:
                # Retraso de cortesía para respetar el límite de 15 RPM en el plan gratuito de Gemini
                time.sleep(1.0)
                
                model = genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Error llamando a la API de Gemini: {e}")
                return "0.0"
        else:
            # Fallback para otros proveedores (por ejemplo, OpenAI)
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

