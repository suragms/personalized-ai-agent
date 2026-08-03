"""Provider-agnostic LLM interface.

Every backend (mock, Ollama, OpenAI, Gemini) implements this ABC. The rest of
the platform talks only to `LLMProvider`, so swapping models never touches agent
code.
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("ai")


class LLMProvider(ABC):
    name = "base"
    supports_embeddings = True

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
