import logging
from django.conf import settings
from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.ollama_provider import OllamaProvider
from .providers.groq_provider import GroqProvider
from .providers.getunikey_provider import GetUniKeyProvider
from .providers.opencode_provider import OpenCodeProvider
from .providers.mock import MockProvider

logger = logging.getLogger("ai")

ADAPTER_MAP = {
    "openai_chat": OpenAIProvider,
    "openai_responses": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "groq": GroqProvider,
    "grok": GroqProvider,
    "getunikey": GetUniKeyProvider,
    "opencode": OpenCodeProvider,
    "mock": MockProvider,
}

def instantiate_adapter(protocol: str, **kwargs) -> LLMProvider:
    cls = ADAPTER_MAP.get(protocol, MockProvider)
    return cls(**kwargs)
