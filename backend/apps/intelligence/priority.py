"""Deterministic priority scoring (spec §12).

Transparent, factor-based scoring — no subjective judgments. Every score
stores the factors and reasons that produced it so the user can audit it.
"""
from __future__ import annotations

from datetime import datetime

from django.utils import timezone

SEVERITY_BASE = {
    "critical": 40,
    "high": 30,
    "medium": 20,
    "low": 10,
    "info": 0,
}

CONFIDENCE_WEIGHT = {
    "high": 15,
    "medium": 8,
    "low": 3,
    "insufficient": 0,
}

FRESHNESS_WEIGHT = {
    "fresh": 10,
    "aging": 5,
    "stale": 0,
    "unavailable": 0,
}


def score_priority(
    *,
    severity: str,
    confidence: str,
    freshness_level: str = "fresh",
    expires_at: datetime | None = None,
    goal_relevant: bool = False,
    now: datetime | None = None,
) -> tuple[str, list[dict]]:
    """Return ``(priority_label, factors)`` for an insight.

    Factors are explicit so stored reasoning is machine- and user-readable.
    """
    now = now or timezone.now()
    factors: list[dict] = []

    base = SEVERITY_BASE.get(severity, 0)
    factors.append({"name": "severity", "value": severity, "points": base, "reason": f"Severity is {severity}."})

    conf = CONFIDENCE_WEIGHT.get(confidence, 0)
    factors.append(
        {
            "name": "evidence_confidence",
            "value": confidence,
            "points": conf,
            "reason": f"Evidence confidence is {confidence}.",
        }
    )

    fresh = FRESHNESS_WEIGHT.get(freshness_level, 0)
    factors.append(
        {
            "name": "data_freshness",
            "value": freshness_level,
            "points": fresh,
            "reason": f"Underlying data is {freshness_level}.",
        }
    )

    if expires_at is not None:
        hours_left = (expires_at - now).total_seconds() / 3600
        if hours_left <= 0:
            points = 20
            reason = "Deadline has passed."
        elif hours_left <= 48:
            points = 15
            reason = f"Deadline is within {int(hours_left)} hours."
        else:
            points = 5
            reason = "A deadline is attached."
        factors.append({"name": "deadline_proximity", "value": expires_at.isoformat(), "points": points, "reason": reason})

    if goal_relevant:
        factors.append(
            {
                "name": "goal_relevance",
                "value": True,
                "points": 10,
                "reason": "Linked to an active goal.",
            }
        )

    total = sum(f["points"] for f in factors)
    if total >= 60:
        label = "critical"
    elif total >= 40:
        label = "high"
    elif total >= 20:
        label = "medium"
    else:
        label = "low"

    return label, factors
