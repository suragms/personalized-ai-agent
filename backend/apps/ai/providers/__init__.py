"""Provider registry — resolve the configured LLM provider."""
from django.conf import settings

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .getunikey_provider import GetUniKeyProvider
from .groq_provider import GroqProvider
from .mock import MockProvider
from .ollama_provider import OllamaProvider
from .opencode_provider import OpenCodeProvider
from .openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "grok": GroqProvider,
    "getunikey": GetUniKeyProvider,
    "opencode": OpenCodeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    """Return a configured provider instance (default: settings.AI_PROVIDER)."""
    key = (name or settings.AI_PROVIDER or "mock").lower()
    cls = _PROVIDERS.get(key, MockProvider)
    return cls()


def available_providers() -> list[dict]:
    """Status for the Settings page."""
    # Deduplicate groq / grok for UI list display
    display_names = ["gemini", "groq", "getunikey", "opencode", "openai", "ollama", "mock"]
    results = []
    for name in display_names:
        provider_cls = _PROVIDERS.get(name)
        if not provider_cls:
            continue
        inst = provider_cls()
        is_active = (name == (settings.AI_PROVIDER or "mock").lower()) or (
            name == "groq" and (settings.AI_PROVIDER or "").lower() == "grok"
        )
        results.append(
            {
                "name": name,
                "active": is_active,
                "available": inst.is_available(),
            }
        )
    return results
