"""OpenCode Zen provider."""
from django.conf import settings
from .openai_provider import OpenAIProvider


class OpenCodeProvider(OpenAIProvider):
    name = "opencode"

    def _client(self):
        from openai import OpenAI

        key = self.api_key or getattr(settings, "OPENCODE_API_KEY", "")
        base = self.base_url or getattr(settings, "OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
        kwargs = {"api_key": key}
        if base:
            kwargs["base_url"] = base

        return OpenAI(**kwargs)

    def is_available(self) -> bool:
        return bool(self.api_key or getattr(settings, "OPENCODE_API_KEY", ""))

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        model_name = self.model or getattr(settings, "OPENCODE_MODEL", "big-pickle")
        kwargs = {"model": model_name, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        client = self._client()
        response = client.chat.completions.create(messages=messages, **kwargs)
        return response.choices[0].message.content or ""
