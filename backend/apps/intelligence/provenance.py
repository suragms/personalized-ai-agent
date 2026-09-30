"""Data provenance, freshness, and confidence vocabulary.

Every analysis output must identify where its data came from, how old it is,
and how much the evidence supports it. Pure functions only — no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone


class Provenance:
    """Explicit provenance categories for analysis results (spec §3)."""

    REAL_CONNECTED_DATA = "REAL_CONNECTED_DATA"
    USER_PROVIDED_DATA = "USER_PROVIDED_DATA"
    USER_ENTERED_MANUAL_DATA = "USER_ENTERED_MANUAL_DATA"
    AI_DERIVED_ANALYSIS = "AI_DERIVED_ANALYSIS"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    DETERMINISTIC_ANALYSIS = "DETERMINISTIC_ANALYSIS"
    MOCK_DATA = "MOCK_DATA"
    STALE_DATA = "STALE_DATA"
    UNAVAILABLE_DATA = "UNAVAILABLE_DATA"
    ERROR = "ERROR"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

    ALL = (
        REAL_CONNECTED_DATA,
        USER_PROVIDED_DATA,
        USER_ENTERED_MANUAL_DATA,
        AI_DERIVED_ANALYSIS,
        AI_RECOMMENDATION,
        DETERMINISTIC_ANALYSIS,
        MOCK_DATA,
        STALE_DATA,
        UNAVAILABLE_DATA,
        ERROR,
        INSUFFICIENT_EVIDENCE,
    )


# Freshness levels
FRESH = "fresh"
AGING = "aging"
STALE = "stale"
UNAVAILABLE = "unavailable"

# Per-source freshness thresholds in hours: (fresh_within, aging_within).
# Different integrations update at different cadences — one threshold for
# everything would mislabel slow sources as stale (spec §10).
FRESHNESS_THRESHOLDS: dict[str, tuple[int, int]] = {
    "github": (24, 72),
    "website": (168, 336),
    "linkedin": (168, 336),
    "instagram": (168, 336),
    "facebook": (168, 336),
    "twitter": (168, 336),
    "analytics": (24, 72),
    "calendar": (24, 72),
    "manual": (720, 2160),  # user-entered data ages slowly
    "derived": (24, 72),
}
DEFAULT_THRESHOLDS = (24, 72)


@dataclass(frozen=True)
class Freshness:
    """Freshness verdict for one data source."""

    level: str  # fresh | aging | stale | unavailable
    last_synced_at: datetime | None
    hours_since_sync: float | None
    fresh_hours: int  # threshold used for "fresh"
    stale_hours: int  # threshold used for "stale" (beyond this)
    message: str

    @property
    def is_usable(self) -> bool:
        """True when the data may be presented as current."""
        return self.level in (FRESH, AGING)

    @property
    def provenance(self) -> str:
        """Provenance category that data of this age should carry."""
        if self.level == UNAVAILABLE:
            return Provenance.UNAVAILABLE_DATA
        if self.level == STALE:
            return Provenance.STALE_DATA
        return Provenance.REAL_CONNECTED_DATA


def compute_freshness(
    last_synced_at: datetime | None,
    source_type: str = "",
    *,
    now: datetime | None = None,
    sync_frequency_hours: int | None = None,
) -> Freshness:
    """Classify how fresh a source's data is (spec §10).

    Thresholds are per source type; ``sync_frequency_hours`` (the source's own
    configured cadence) wins when provided so each integration is judged
    against its own schedule.
    """
    if sync_frequency_hours:
        fresh_hours = sync_frequency_hours
        stale_hours = sync_frequency_hours * 3
    else:
        fresh_hours, stale_hours = FRESHNESS_THRESHOLDS.get(source_type, DEFAULT_THRESHOLDS)

    if last_synced_at is None:
        return Freshness(
            level=UNAVAILABLE,
            last_synced_at=None,
            hours_since_sync=None,
            fresh_hours=fresh_hours,
            stale_hours=stale_hours,
            message="Data has never been synchronized.",
        )

    now = now or timezone.now()
    hours = (now - last_synced_at).total_seconds() / 3600

    if hours <= fresh_hours:
        level, message = FRESH, ""
    elif hours <= stale_hours:
        level = AGING
        message = f"Data is aging (last synchronized {int(hours)} hours ago)."
    else:
        level = STALE
        message = (
            f"Data was last synchronized {int(hours // 24)} days ago. "
            "Current values may differ."
        )

    return Freshness(
        level=level,
        last_synced_at=last_synced_at,
        hours_since_sync=round(hours, 2),
        fresh_hours=fresh_hours,
        stale_hours=stale_hours,
        message=message,
    )


# Confidence levels
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_INSUFFICIENT = "insufficient"


def confidence_from_evidence(
    evidence_count: int,
    freshness: Freshness,
    *,
    direct_api_evidence: bool = True,
) -> str:
    """Score evidence quality (spec §9).

    - direct, current evidence → high
    - multiple observations or aging data → medium
    - limited or stale data → low
    - nothing to go on → insufficient (never disguised as a real level)
    """
    if evidence_count <= 0:
        return CONFIDENCE_INSUFFICIENT

    if freshness.level in (UNAVAILABLE,):
        return CONFIDENCE_INSUFFICIENT

    if freshness.level == STALE:
        return CONFIDENCE_LOW

    if freshness.level == AGING:
        return CONFIDENCE_MEDIUM if evidence_count >= 2 else CONFIDENCE_LOW

    # fresh
    if direct_api_evidence:
        return CONFIDENCE_HIGH if evidence_count == 1 else CONFIDENCE_HIGH
    return CONFIDENCE_MEDIUM if evidence_count >= 2 else CONFIDENCE_LOW


def freshness_summary(sources) -> list[dict]:
    """Serialise freshness for a queryset/iterable of DataSource rows."""
    out = []
    for source in sources:
        f = compute_freshness(
            source.last_synced_at,
            source.source_type,
            sync_frequency_hours=source.sync_frequency_hours,
        )
        out.append(
            {
                "source_id": str(source.id),
                "source_type": source.source_type,
                "name": source.name,
                "state": source.state,
                "level": f.level,
                "last_synced_at": source.last_synced_at.isoformat() if source.last_synced_at else None,
                "hours_since_sync": f.hours_since_sync,
                "message": f.message,
                "provenance": f.provenance,
            }
        )
    return out
