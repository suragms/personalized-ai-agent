"""Shared AI helpers used by agents across the platform."""
import logging

from .routing import PROVENANCE_MOCK, PROVENANCE_TEMPLATE, AIRoutingService

logger = logging.getLogger("ai")


def generate_prose_detailed(
    system: str,
    user: str,
    *,
    fallback: str,
    owner=None,
    skip_mock: bool = False,
) -> tuple[str, str]:
    """Generate prose and report what actually produced it.

    Returns ``(text, provenance)`` where provenance is one of
    ``REAL_AI_PROVIDER`` / ``MOCK_PROVIDER`` / ``DETERMINISTIC_TEMPLATE``.

    Never raises: any provider failure falls back to a template string so agent
    runs always complete. `fallback` should be deterministic markdown built from
    computed metrics.

    ``skip_mock=True`` keeps the curated fallback when the routing layer would
    answer with the deterministic mock (whose digests would degrade prose the
    caller already templated well — e.g. resume summaries).
    """
    if not owner:
        return fallback, PROVENANCE_TEMPLATE

    svc = AIRoutingService(owner)
    try:
        result = svc.complete(system, user, temperature=0.5).strip()
    except Exception as exc:
        logger.warning("LLM prose generation failed (%s); using fallback.", exc)
        return fallback, PROVENANCE_TEMPLATE

    if not result:
        return fallback, PROVENANCE_TEMPLATE

    provenance = svc.last_provenance or PROVENANCE_TEMPLATE
    if skip_mock and provenance == PROVENANCE_MOCK:
        return fallback, PROVENANCE_TEMPLATE
    return result, provenance


def generate_prose(
    system: str,
    user: str,
    *,
    fallback: str,
    owner=None,
    skip_mock: bool = False,
) -> str:
    """Generate prose via the configured provider (text only).

    Never raises: any provider failure falls back to a template string so agent
    runs always complete. Use :func:`generate_prose_detailed` when the caller
    needs to persist or display the provenance of the output.
    """
    return generate_prose_detailed(
        system, user, fallback=fallback, owner=owner, skip_mock=skip_mock
    )[0]


def embed_text_detailed(text: str, owner) -> tuple[list[float], str | None]:
    """Embed text and report which provider produced it (or None on failure)."""
    svc = AIRoutingService(owner)
    try:
        vector = svc.embed(text)
    except Exception as exc:
        logger.warning("Embedding failed (%s); returning empty vector.", exc)
        return [], None
    return vector or [], svc.last_provenance


def embed_text(text: str, owner) -> list[float]:
    """Embed text for the memory store. Falls back to an empty vector on failure."""
    return embed_text_detailed(text, owner)[0]
