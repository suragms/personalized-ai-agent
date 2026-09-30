"""Deterministic analyzer framework.

Analyzers turn raw, already-collected data into structured findings. They
never call an LLM and never invent values: every number is computed from
persisted rows, and every finding carries structured evidence (spec §5).

    raw data → Analyzer → AnalysisFinding[] → InsightEngine → Insight
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnalysisFinding:
    """One structured, evidence-backed observation.

    Mirrors the spec example:
        {"metric": "stale_pull_requests", "value": 3, "period": "30d",
         "source": "github", "evidence": [...]}
    """

    metric: str
    value: Any
    period: str
    source: str
    evidence: list[dict]
    insight_type: str  # Insight.TYPE_CHOICES value
    severity: str  # Insight.SEVERITY_CHOICES value
    title: str
    description: str
    recommended_action: str
    dedup_key: str  # stable per observation for idempotent upserts
    category: str = "development"
    observed_metrics: dict = field(default_factory=dict)
    provenance: str = "REAL_CONNECTED_DATA"

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    def evidence_text(self) -> str:
        """Human-readable rendering of the structured evidence."""
        lines = [f"{k}: {v}" for entry in self.evidence for k, v in entry.items()]
        return "\n".join(f"- {line}" for line in lines)


class BaseAnalyzer:
    """Interface for deterministic analyzers."""

    source: str = ""

    def analyze(self, user, **kwargs) -> list[AnalysisFinding]:
        raise NotImplementedError
