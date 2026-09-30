"""OpenAI provider."""
from django.conf import settings

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def _client(self):
        from openai import OpenAI

        kwargs = {}
        # Prioritize connection args, fallback to settings Defaults
        key = self.api_key or getattr(settings, "OPENAI_API_KEY", "")
        if key:
            kwargs["api_key"] = key

        base = self.base_url or getattr(settings, "OPENAI_BASE_URL", "")
        if base:
            kwargs["base_url"] = base

        try:
            return OpenAI(**kwargs)
        except Exception:
            return OpenAI(api_key=key) # fallback for api_key requirement exceptions

    def is_available(self) -> bool:
        return bool(self.api_key or getattr(settings, "OPENAI_API_KEY", ""))

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
        model_name = self.model or getattr(settings, "OPENAI_MODEL", "gpt-4o")
        kwargs = {"model": model_name, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        client = self._client()
        response = client.chat.completions.create(messages=messages, **kwargs)
        return response.choices[0].message.content or ""

    def embed(self, text: str) -> list[float]:
        client = self._client()
        response = client.embeddings.create(model="text-embedding-3-small", input=[text])
        return response.data[0].embedding
