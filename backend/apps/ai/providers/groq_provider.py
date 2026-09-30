"""Groq (and Grok / xAI compatible) provider."""
from django.conf import settings

from .openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    name = "groq"

    def _client(self):
        from openai import OpenAI

        key = (
            self.api_key
            or getattr(settings, "GROQ_API_KEY", "")
            or getattr(settings, "GROK_API_KEY", "")
        )
        base = (
            self.base_url
            or getattr(settings, "GROQ_BASE_URL", "")
            or getattr(settings, "GROK_BASE_URL", "https://api.groq.com/openai/v1")
        )
        kwargs = {"api_key": key}
        if base:
            kwargs["base_url"] = base

        return OpenAI(**kwargs)

    def is_available(self) -> bool:
        return bool(
            self.api_key
            or getattr(settings, "GROQ_API_KEY", "")
            or getattr(settings, "GROK_API_KEY", "")
        )

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        model_name = (
            self.model
            or getattr(settings, "GROQ_MODEL", "")
            or getattr(settings, "GROK_MODEL", "qwen/qwen3.8-27b")
        )
        kwargs = {"model": model_name, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        client = self._client()
        response = client.chat.completions.create(messages=messages, **kwargs)
        return response.choices[0].message.content or ""

    def embed(self, text: str) -> list[float]:
        # Groq doesn't provide embeddings; return empty or fall back
        return []
