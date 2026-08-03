"""OpenAI provider (default model GPT-5.5)."""
from django.conf import settings

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def _client(self):
        from openai import OpenAI

        return OpenAI(api_key=settings.OPENAI_API_KEY)

    def is_available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

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
        kwargs = {"model": settings.OPENAI_MODEL, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        response = self._client().chat.completions.create(messages=messages, **kwargs)
        return response.choices[0].message.content or ""

    def embed(self, text: str) -> list[float]:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(model="text-embedding-3-small", input=[text])
        return response.data[0].embedding
