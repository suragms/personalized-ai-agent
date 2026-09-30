import logging

from .providers.base import LLMProvider
from .providers.gemini_provider import GeminiProvider
from .providers.getunikey_provider import GetUniKeyProvider
from .providers.groq_provider import GroqProvider
from .providers.mock import MockProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .providers.opencode_provider import OpenCodeProvider

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
