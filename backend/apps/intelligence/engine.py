"""Insight Engine — deterministic analysis → evidence-backed insights.

Pipeline (spec §2):

    DataSnapshot / synced rows → Analyzers → AnalysisFinding
        → Insight upsert (dedup) → priority scoring → AI interpretation
        → recommendation → task (dedup) / alert (dedup + cooldown)

Rules enforced here:
- AI never invents facts: it only explains structured findings (§6).
- Every insight records provenance, snapshot, freshness, evidence (§3/§7).
- Re-runs update instead of duplicate (dedup_key), and unconfirmed insights
  expire (§14/§15).
- When data is missing the result is UNAVAILABLE_DATA / INSUFFICIENT_EVIDENCE,
  never fabricated zeros presented as findings.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from accounts.models import User

from .analyzers import AnalysisFinding
from .models import Alert, DataSnapshot, DataSource, Goal, Insight, IntegrationConnection
from .priority import score_priority
from .provenance import (
    FRESH,
    STALE,
    UNAVAILABLE,
    Freshness,
    Provenance,
    compute_freshness,
    confidence_from_evidence,
)
from .services import IntelligenceService

logger = logging.getLogger("intelligence")

# Severities whose recommended actions are worth turning into tasks (§14).
TASK_SEVERITIES = {"high", "critical"}

# How many insights receive an AI interpretation per run (cost control).
INTERPRETATION_BATCH = 3

# Connection statuses that mean the pipeline must not treat data as current.
BROKEN_CONNECTION_STATUSES = {
    "disconnected",
    "authentication_failed",
    "permission_denied",
    "rate_limited",
    "timeout",
    "network_error",
    "api_error",
    "service_unavailable",
    "invalid_credentials",
    "stale",
    "no_data",
    "unknown_error",
}

INTERPRETATION_SYSTEM = (
    "You explain verified observations to their owner. You are given facts "
    "computed from their connected data. Explain what they mean in 2-3 "
    "sentences and, if useful, what to consider doing. Never invent commits, "
    "dates, repositories, metrics, users, activity, or achievements that are "
    "not in the facts. If the facts are insufficient to conclude anything, "
    "say so plainly."
)


class InsightEngine:
    """Runs the deterministic intelligence pipeline for one user."""

    def __init__(self, user: User):
        self.user = user

    # ── Connectivity gate (§23) ─────────────────────────────────────────
    def _github_context(self) -> dict:
        """Decide whether GitHub-derived analysis may run, and with what provenance."""
        from github.models import Repository

        source = DataSource.objects.filter(owner=self.user, source_type="github").first()
        conn = IntegrationConnection.objects.filter(owner=self.user, platform="github").first()
        has_rows = Repository.objects.filter(owner=self.user).exists()

        freshness = compute_freshness(
            source.last_synced_at if source else None,
            "github",
            sync_frequency_hours=source.sync_frequency_hours if source else None,
        )

        if not has_rows:
            # No data at all — never present zeros as findings (NO_DATA rule).
            return {"run": False, "provenance": Provenance.UNAVAILABLE_DATA, "freshness": freshness, "reason": "no_github_data"}

        if freshness.level == UNAVAILABLE:
            # Rows exist but no sync was recorded — the data is real but of
            # unknown age: treat as stale (analyzable, never "fresh").
            freshness = Freshness(
                level=STALE,
                last_synced_at=None,
                hours_since_sync=None,
                fresh_hours=freshness.fresh_hours,
                stale_hours=freshness.stale_hours,
                message="Data exists but no sync timestamp is recorded — treated as stale.",
            )

        connection_broken = conn is not None and conn.status in BROKEN_CONNECTION_STATUSES

        if freshness.level == STALE or connection_broken:
            provenance = Provenance.STALE_DATA
        else:
            provenance = Provenance.REAL_CONNECTED_DATA

        return {"run": True, "provenance": provenance, "freshness": freshness, "reason": ""}

    # ── Insight upsert / expiry ─────────────────────────────────────────
    def _upsert_insight(
        self,
        finding: AnalysisFinding,
        *,
        provenance: str,
        freshness: Freshness,
        snapshot: DataSnapshot | None,
        confidence: str,
        goal_relevant: bool = False,
    ) -> tuple[Insight, bool]:
        now = timezone.now()
        insight, created = Insight.objects.get_or_create(
            owner=self.user,
            dedup_key=finding.dedup_key,
            defaults={"title": finding.title, "evidence": finding.evidence_text() or finding.description},
        )

        insight.insight_type = finding.insight_type
        insight.category = finding.category
        insight.severity = finding.severity
        insight.confidence = confidence
        insight.title = finding.title
        insight.summary = finding.description[:500]
        insight.description = finding.description
        insight.evidence = finding.evidence_text() or finding.description
        insight.structured_evidence = finding.evidence
        insight.observed_metrics = finding.observed_metrics
        insight.provenance = provenance
        insight.source_type = finding.source
        insight.snapshot = snapshot
        insight.recommended_action = finding.recommended_action
        insight.source_references = [
            {k: v for k, v in entry.items() if k in ("source", "repository", "metric", "repository_id")}
            for entry in finding.evidence[:10]
        ]
        insight.last_confirmed_at = now
        if insight.status == "expired":
            insight.status = "new"
        insight.save()

        priority, factors = score_priority(
            severity=insight.severity,
            confidence=insight.confidence,
            freshness_level=freshness.level,
            expires_at=insight.expires_at,
            goal_relevant=goal_relevant,
        )
        insight.priority = priority
        insight.priority_reasoning = factors
        insight.save(update_fields=["priority", "priority_reasoning", "updated_at"])
        return insight, created

    def _expire_unconfirmed(self, confirmed_keys: set[str], source_type: str) -> int:
        """Mark engine insights not reconfirmed by this run as expired (§7 status)."""
        qs = Insight.objects.filter(
            owner=self.user,
            source_type=source_type,
            status__in=("new", "reviewed"),
        ).exclude(dedup_key__in=confirmed_keys)
        qs = qs.exclude(dedup_key="")
        return qs.update(status="expired")

    # ── AI interpretation (§6) ──────────────────────────────────────────
    def _interpret(self, insights: list[Insight], freshness: Freshness) -> int:
        """Explain the top findings with the configured provider.

        Only REAL_AI_PROVIDER output is stored as AI interpretation; when the
        routing layer answers with the deterministic mock (or fails), the
        interpretation is recorded as unavailable rather than faked.
        """
        from ai.routing import PROVENANCE_REAL, AIRoutingService

        interpreted = 0
        candidates = [
            i
            for i in insights
            if not i.interpretation_meta.get("generated_at")
            and i.status in ("new", "reviewed")
            and i.severity in ("medium", "high", "critical")
        ][:INTERPRETATION_BATCH]

        for insight in candidates:
            facts = self._facts_text(insight, freshness)
            svc = AIRoutingService(self.user)
            try:
                text = (svc.complete(INTERPRETATION_SYSTEM, facts, temperature=0.3, max_tokens=400) or "").strip()
            except Exception:
                logger.info("Interpretation unavailable for insight %s", insight.dedup_key)
                continue  # transient — retry next run

            provenance = svc.last_provenance
            if text and provenance == PROVENANCE_REAL:
                insight.ai_interpretation = text
                insight.interpretation_meta = {
                    "available": True,
                    "provider": svc.last_provider,
                    "provenance": provenance,
                    "generated_at": timezone.now().isoformat(),
                }
            else:
                insight.ai_interpretation = ""
                insight.interpretation_meta = {
                    "available": False,
                    "provider": svc.last_provider,
                    "provenance": provenance,
                    "generated_at": timezone.now().isoformat(),
                }
            insight.save(update_fields=["ai_interpretation", "interpretation_meta", "updated_at"])
            interpreted += 1
        return interpreted

    @staticmethod
    def _facts_text(insight: Insight, freshness: Freshness) -> str:
        lines = ["Observed facts (computed from connected data, do not extend them):"]
        for entry in insight.structured_evidence[:10]:
            rendered = ", ".join(f"{k}={v}" for k, v in entry.items())
            lines.append(f"- {rendered}")
        lines.append(f"Metric: {insight.observed_metrics}")
        lines.append(f"Data freshness: {freshness.level} ({freshness.message or 'current'}).")
        lines.append("Explain what these facts mean in 2-3 sentences.")
        return "\n".join(lines)

    # ── Recommendations → tasks (§14) ───────────────────────────────────
    def _maybe_create_task(self, insight: Insight):
        from productivity.models import Task

        if insight.severity not in TASK_SEVERITIES or not insight.recommended_action:
            return None
        if not insight.dedup_key:
            return None

        key = f"insight:{insight.dedup_key}"
        if Task.objects.filter(owner=self.user, dedup_key=key).exclude(status="done").exists():
            return None
        recent_done = Task.objects.filter(
            owner=self.user, dedup_key=key, status="done", completed_at__gte=timezone.now() - timedelta(days=14)
        ).exists()
        if recent_done:
            return None

        priority_map = {"critical": "urgent", "high": "high", "medium": "medium", "low": "low", "info": "low"}
        task = Task.objects.create(
            owner=self.user,
            title=insight.title[:300],
            description=(
                f"{insight.recommended_action}\n\n"
                f"Source: {insight.source_type or 'analysis'} insight\n"
                f"Provenance: {insight.provenance}\n"
                f"Evidence:\n{insight.evidence}"
            ),
            priority=priority_map.get(insight.severity, "medium"),
            source_insight=insight,
            provenance=insight.provenance or Provenance.DETERMINISTIC_ANALYSIS,
            evidence=insight.structured_evidence,
            dedup_key=key,
        )
        if insight.status == "new":
            insight.status = "converted_to_task"
            insight.save(update_fields=["status", "updated_at"])
        return task

    # ── Alerts (§15) ────────────────────────────────────────────────────
    def _raise_alert(self, **kwargs) -> tuple[Alert, bool]:
        return IntelligenceService.create_alert(user=self.user, **kwargs)

    def condition_alerts(self) -> int:
        """Alert only for meaningful conditions, with dedup + cooldown."""
        created = 0
        now = timezone.now()

        for source in DataSource.objects.filter(owner=self.user):
            freshness = compute_freshness(
                source.last_synced_at, source.source_type, sync_frequency_hours=source.sync_frequency_hours
            )
            if freshness.level == "stale":
                _, was_created = self._raise_alert(
                    category="integration",
                    severity="medium",
                    title=f"{source.name} data is stale",
                    message=freshness.message,
                    evidence=f"Last synced: {source.last_synced_at}",
                    source_type=source.source_type,
                    dedup_key=f"freshness:stale:{source.source_type}:{source.id}",
                )
                created += 1 if was_created else 0

        for conn in IntegrationConnection.objects.filter(owner=self.user):
            if conn.status not in BROKEN_CONNECTION_STATUSES:
                continue
            _, was_created = self._raise_alert(
                category="integration",
                severity="high",
                title=f"{conn.platform} connection failed",
                message=f"The {conn.platform} integration reports: {conn.get_status_display()}.",
                evidence=conn.last_error,
                source_type=conn.platform,
                dedup_key=f"integration:failed:{conn.platform}:{conn.id}",
            )
            created += 1 if was_created else 0

        for goal in Goal.objects.filter(owner=self.user, status="active"):
            if goal.deadline and goal.deadline < now.date() and goal.progress_pct < 100:
                _, was_created = self._raise_alert(
                    category="deadline",
                    severity="high",
                    title=f"Goal deadline passed: {goal.title}",
                    message=f"Due {goal.deadline}, currently {goal.progress_pct}% complete.",
                    evidence=f"goal_id={goal.id}, deadline={goal.deadline}, progress={goal.progress_pct}%",
                    source_type="goal",
                    dedup_key=f"goal:overdue:{goal.id}",
                )
                created += 1 if was_created else 0

        return created

    # ── Main run ────────────────────────────────────────────────────────
    def run(self, source_types: list[str] | None = None) -> dict:
        """Run the pipeline. Idempotent: re-running updates, never duplicates."""
        from github.analyzers import run_github_analyzers

        now = timezone.now()
        summary: dict = {
            "created": 0,
            "updated": 0,
            "expired": 0,
            "tasks_created": 0,
            "alerts_created": 0,
            "interpreted": 0,
            "scopes": {},
            "skipped": [],
            "insight_ids": [],
        }

        wants_github = source_types is None or "github" in source_types
        if wants_github:
            ctx = self._github_context()
            if not ctx["run"]:
                summary["skipped"].append({"scope": "github", "reason": ctx["reason"], "provenance": ctx["provenance"]})
            else:
                try:
                    findings = run_github_analyzers(self.user, now=now)
                except Exception:
                    logger.exception("GitHub analyzers failed for %s", self.user.username)
                    summary["skipped"].append(
                        {"scope": "github", "reason": "analyzer_error", "provenance": Provenance.ERROR}
                    )
                    findings = None

                if findings is not None:
                    snapshot = (
                        DataSnapshot.objects.filter(owner=self.user, source__source_type="github")
                        .order_by("-snapshot_date")
                        .first()
                    )
                    confirmed: set[str] = set()
                    touched: list[Insight] = []
                    for finding in findings:
                        confidence = confidence_from_evidence(finding.evidence_count, ctx["freshness"])
                        if confidence == "insufficient":
                            continue
                        insight, created = self._upsert_insight(
                            finding,
                            provenance=ctx["provenance"],
                            freshness=ctx["freshness"],
                            snapshot=snapshot,
                            confidence=confidence,
                        )
                        confirmed.add(finding.dedup_key)
                        touched.append(insight)
                        summary["created" if created else "updated"] += 1
                    summary["expired"] += self._expire_unconfirmed(confirmed, "github")
                    summary["interpreted"] += self._interpret(touched, ctx["freshness"])
                    for insight in touched:
                        if self._maybe_create_task(insight):
                            summary["tasks_created"] += 1
                    summary["insight_ids"].extend(str(i.id) for i in touched)
                    summary["scopes"]["github"] = {
                        "findings": len(findings),
                        "insights": len(touched),
                        "provenance": ctx["provenance"],
                        "freshness": ctx["freshness"].level,
                    }

        wants_goals = source_types is None or "goals" in source_types
        if wants_goals:
            confirmed_goals: set[str] = set()
            goal_touched: list[Insight] = []
            # Goals are user-entered: their data is as fresh as the user left it.
            goal_freshness = Freshness(
                level=FRESH,
                last_synced_at=now,
                hours_since_sync=0.0,
                fresh_hours=720,
                stale_hours=2160,
                message="",
            )
            for goal in Goal.objects.filter(owner=self.user, status="active"):
                if goal.deadline and goal.deadline < now.date() and goal.progress_pct < 100:
                    days_overdue = (now.date() - goal.deadline).days
                    finding = AnalysisFinding(
                        metric="overdue_goal",
                        value=days_overdue,
                        period="current",
                        source="goals",
                        evidence=[
                            {"source": "goals", "metric": "goal_title", "value": goal.title},
                            {"source": "goals", "metric": "deadline", "value": goal.deadline.isoformat()},
                            {"source": "goals", "metric": "progress_pct", "value": goal.progress_pct},
                        ],
                        insight_type="blocker",
                        severity="high",
                        title=f"Goal deadline passed: {goal.title}",
                        description=(
                            f"'{goal.title}' was due {goal.deadline} and is {goal.progress_pct}% complete "
                            f"({days_overdue} days overdue)."
                        ),
                        recommended_action="Update the goal status, adjust the deadline, or schedule time to finish it.",
                        dedup_key=f"goal:overdue:{goal.id}",
                        category="goal",
                        observed_metrics={"days_overdue": days_overdue, "progress_pct": goal.progress_pct},
                        provenance=Provenance.USER_PROVIDED_DATA,
                    )
                    insight, created = self._upsert_insight(
                        finding,
                        provenance=Provenance.USER_PROVIDED_DATA,
                        freshness=goal_freshness,
                        snapshot=None,
                        confidence="high",
                        goal_relevant=True,
                    )
                    confirmed_goals.add(finding.dedup_key)
                    goal_touched.append(insight)
                    summary["created" if created else "updated"] += 1

            summary["expired"] += self._expire_unconfirmed(confirmed_goals, "goals")
            for insight in goal_touched:
                if self._maybe_create_task(insight):
                    summary["tasks_created"] += 1
            summary["insight_ids"].extend(str(i.id) for i in goal_touched)
            summary["scopes"]["goals"] = {"insights": len(goal_touched)}

        summary["alerts_created"] += self.condition_alerts()
        summary["totals"] = {"insights": Insight.objects.filter(owner=self.user).count()}
        return summary

    def convert_to_task(self, insight: Insight):
        """Explicit user action: turn a recommendation into a task (§13/§14).

        The severity gate that keeps *automatic* conversion conservative does
        not apply here — the user asked for this one.
        """
        if insight.owner_id != self.user.id:
            raise PermissionError("Insight belongs to another user")
        original_severity = insight.severity
        if insight.severity not in TASK_SEVERITIES:
            insight.severity = "high"
        task = self._maybe_create_task(insight)
        insight.severity = original_severity
        if task is None and insight.dedup_key:
            from productivity.models import Task

            task = Task.objects.filter(owner=self.user, dedup_key=f"insight:{insight.dedup_key}").first()
        return task
