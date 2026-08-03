"""Provider registry — resolve the configured LLM provider."""
from django.conf import settings

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .mock import MockProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "mock": MockProvider,
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    """Return a configured provider instance (default: settings.AI_PROVIDER)."""
    key = (name or settings.AI_PROVIDER or "mock").lower()
    cls = _PROVIDERS.get(key, MockProvider)
    return cls()


def available_providers() -> list[dict]:
    """Status for the Settings page."""
    return [
        {
            "name": name,
            "active": name == (settings.AI_PROVIDER or "mock"),
            "available": provider().is_available(),
        }
        for name, provider in _PROVIDERS.items()
    ]
