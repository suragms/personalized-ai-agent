"""Provider-agnostic LLM interface."""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("ai")

class LLMProvider(ABC):
    name = "base"
    supports_embeddings = True

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Single-turn completion. Returns raw text."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Multi-turn chat. Messages: [{"role": "system|user|assistant", "content": ...}]."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a fixed-dimension embedding vector for `text`."""

    def is_available(self) -> bool:
        """Whether the provider can serve requests right now."""
        return True

    def fail_gracefully(self, fallback: str) -> str:
        """Log + return a fallback string when a call fails (never raise to callers)."""
        return fallback
