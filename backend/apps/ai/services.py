"""Shared AI helpers used by agents across the platform."""
import logging

from .routing import AIRoutingService
from .exceptions import AIProviderError

logger = logging.getLogger("ai")


def generate_prose(system: str, user: str, *, fallback: str, owner=None) -> str:
    """Generate prose via the configured provider.

    Never raises: any provider failure falls back to a template string so agent
    runs always complete. `fallback` should be deterministic markdown built from
    computed metrics.
    """
    if not owner:
        return fallback

    svc = AIRoutingService(owner)
    try:
        result = svc.complete(system, user, temperature=0.5).strip()
        return result or fallback
    except Exception as exc:
        logger.warning("LLM prose generation failed (%s); using fallback.", exc)
        return fallback


def embed_text(text: str, owner) -> list[float]:
    """Embed text for the memory store. Falls back to a zero-vector on failure."""
    svc = AIRoutingService(owner)
    try:
        return svc.embed(text)
    except Exception as exc:
        logger.warning("Embedding failed (%s); returning empty vector.", exc)
        return []
