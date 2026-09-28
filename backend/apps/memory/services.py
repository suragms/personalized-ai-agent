"""Memory operations: write facts/decisions and search them semantically."""
import logging

from ai.services import embed_text

from .models import ConversationLog, MemoryEntry, UserPreference

logger = logging.getLogger("ai")


def remember(owner, content: str, kind: str = "note", metadata: dict | None = None) -> MemoryEntry:
    """Store a fact/decision with an embedding for later semantic recall."""
    vector = embed_text(text=content, owner=owner)
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


def search_memory(owner, query: str, k: int = 8) -> list[MemoryEntry]:
    """Cosine-similarity search over the owner's memory entries."""
    vector = embed_text(text=query, owner=owner)
    if not vector:
        return list(MemoryEntry.objects.filter(owner=owner)[:k])
    try:
        from pgvector.django import CosineDistance

        return list(
            MemoryEntry.objects.filter(owner=owner)
            .order_by(CosineDistance("embedding", vector))[:k]
        )
    except Exception:
        return list(MemoryEntry.objects.filter(owner=owner)[:k])


def log_conversation(owner, role: str, content: str, intent: str = "") -> None:
    ConversationLog.objects.create(owner=owner, role=role, content=content, intent=intent)


def get_preference(owner, key: str, default=None):
    pref = UserPreference.objects.filter(owner=owner, key=key).first()
    return pref.value if pref else default


def set_preference(owner, key: str, value) -> UserPreference:
    pref, _ = UserPreference.objects.update_or_create(owner=owner, key=key, defaults={"value": value})
    return pref
