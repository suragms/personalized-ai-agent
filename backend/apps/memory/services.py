"""Memory operations: write facts/decisions and search them semantically."""
import logging
from dataclasses import dataclass, field

from django.db.models import Q

from ai.routing import PROVENANCE_REAL
from ai.services import embed_text_detailed

from .models import ConversationLog, MemoryEntry, UserPreference

logger = logging.getLogger("ai")


@dataclass
class MemorySearchResult:
    """Search output with an honest report of how the ranking was produced."""

    entries: list[MemoryEntry] = field(default_factory=list)
    mode: str = "recent"  # semantic | keyword | recent | none
    message: str = ""


def remember(owner, content: str, kind: str = "note", metadata: dict | None = None) -> MemoryEntry:
    """Store a fact/decision with an embedding for later semantic recall."""
    vector, _provenance = embed_text_detailed(content, owner)
    return MemoryEntry.objects.create(
        owner=owner,
        content=content,
        kind=kind,
        metadata=metadata or {},
        embedding=vector or None,
    )


def remember_decision(owner, decision: str, context: dict | None = None) -> MemoryEntry:
    """Persist a decision the platform (or user) made, for future runs."""
    return remember(owner, decision, kind="decision", metadata=context or {})


def search_memory(owner, query: str, k: int = 8) -> MemorySearchResult:
    """Search the owner's memories, reporting the ranking mode honestly.

    Semantic ranking only happens with a real embedding provider and a working
    vector index. Otherwise the caller is told the mode fell back to keyword
    matching or recency instead of receiving silently-unordered rows (§22).
    """
    if not query:
        return MemorySearchResult([], "none", "No query provided.")

    vector, provenance = embed_text_detailed(query, owner)

    if vector and provenance == PROVENANCE_REAL:
        try:
            from pgvector.django import CosineDistance

            entries = list(
                MemoryEntry.objects.filter(owner=owner)
                .exclude(embedding=None)
                .order_by(CosineDistance("embedding", vector))[:k]
            )
            if entries:
                return MemorySearchResult(entries, "semantic", "")
        except Exception as exc:
            logger.info("Vector search unavailable (%s); falling back to keyword match.", exc)

    terms = [t for t in query.split() if len(t) >= 2]
    if terms:
        cond = Q()
        for term in terms:
            cond |= Q(content__icontains=term)
        entries = list(MemoryEntry.objects.filter(owner=owner).filter(cond).order_by("-created_at")[:k])
        return MemorySearchResult(
            entries,
            "keyword",
            "Semantic search unavailable (no real embedding provider or vector index); "
            "showing keyword matches.",
        )

    entries = list(MemoryEntry.objects.filter(owner=owner)[:k])
    return MemorySearchResult(
        entries,
        "recent",
        "Semantic search unavailable; showing most recent entries.",
    )


def log_conversation(owner, role: str, content: str, intent: str = "") -> None:
    ConversationLog.objects.create(owner=owner, role=role, content=content, intent=intent)


def get_preference(owner, key: str, default=None):
    pref = UserPreference.objects.filter(owner=owner, key=key).first()
    return pref.value if pref else default


def set_preference(owner, key: str, value) -> UserPreference:
    pref, _ = UserPreference.objects.update_or_create(owner=owner, key=key, defaults={"value": value})
    return pref
