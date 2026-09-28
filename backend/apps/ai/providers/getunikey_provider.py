"""GetUniKey provider."""
from django.conf import settings
from .openai_provider import OpenAIProvider


class GetUniKeyProvider(OpenAIProvider):
    name = "getunikey"

    def _client(self):
        from openai import OpenAI

        key = self.api_key or getattr(settings, "GETUNIKEY_API_KEY", "")
        base = self.base_url or getattr(settings, "GETUNIKEY_BASE_URL", "https://www.getunikey.ai/v1")
        kwargs = {"api_key": key}
        if base:
            kwargs["base_url"] = base

        return OpenAI(**kwargs)

    def is_available(self) -> bool:
        return bool(self.api_key or getattr(settings, "GETUNIKEY_API_KEY", ""))

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        model_name = self.model or getattr(settings, "GETUNIKEY_MODEL", "gpt-5.5")
        kwargs = {"model": model_name, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        client = self._client()
        response = client.chat.completions.create(messages=messages, **kwargs)
        return response.choices[0].message.content or ""
