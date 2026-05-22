"""
Caché local para evitar llamadas repetidas al LLM durante el desarrollo.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


class LLMCache:
    def __init__(self, path: str):
        self.path = Path(path)
        self._storage: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {}

    def get(self, prompt: str) -> Optional[str]:
        return self._storage.get(prompt)

    def set(self, prompt: str, response: str) -> None:
        self._storage[prompt] = response
        self._save()

    def _save(self) -> None:
        try:
            with self.path.open("w", encoding="utf-8") as handle:
                json.dump(self._storage, handle, indent=2, ensure_ascii=False)
        except OSError:
            pass
