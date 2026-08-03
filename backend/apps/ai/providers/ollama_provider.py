"""Ollama provider (local models) — works fully offline once a model is pulled."""
import httpx
from django.conf import settings

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    @property
    def _url(self) -> str:
        return settings.OLLAMA_BASE_URL.rstrip("/")

    def is_available(self) -> bool:
        try:
            return httpx.get(f"{self._url}/api/tags", timeout=3).status_code == 200
        except Exception:
            return False

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        return self.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        payload = {"model": settings.OLLAMA_MODEL, "messages": messages, "stream": False, "options": {"temperature": temperature}}
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        resp = httpx.post(f"{self._url}/api/chat", json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    def embed(self, text: str) -> list[float]:
        resp = httpx.post(
            f"{self._url}/api/embeddings",
            json={"model": settings.OLLAMA_MODEL, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("embedding", [])
