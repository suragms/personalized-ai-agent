"""Intelligence Engine service layer — core business logic."""
import hashlib
import logging
from datetime import date, timedelta
from typing import Any

from django.utils import timezone

from accounts.models import User

from .models import (
    Alert,
    DailyPlan,
    DataSource,
    Goal,
    Insight,
    IntegrationConnection,
    PerformanceMetric,
    Report,
    UserProfile,
)
from .provenance import Provenance, compute_freshness, freshness_summary

logger = logging.getLogger("intelligence")

# One alert row per condition: repeats within the cooldown only bump the
# occurrence counter instead of spamming new rows (spec §15).
ALERT_COOLDOWN = timedelta(hours=24)


class IntelligenceService:
    """Central intelligence pipeline: data → analysis → insights → recommendations."""

    @staticmethod
    def get_or_create_profile(user: User) -> UserProfile:
        """Get or create user profile."""
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def is_onboarding_complete(user: User) -> bool:
        """Check if user has completed onboarding."""
        try:
            return user.intelligence_profile.onboarding_completed
        except UserProfile.DoesNotExist:
            return False

    @staticmethod
    def get_data_health(user: User) -> dict[str, Any]:
        """Return data health status for all sources."""
        sources = DataSource.objects.filter(owner=user)
        integrations = IntegrationConnection.objects.filter(owner=user)

        health = {
            "sources": [],
            "integrations": [],
            "overall_status": "healthy",
        }

        for source in sources:
            freshness = compute_freshness(
                source.last_synced_at,
                source.source_type,
                sync_frequency_hours=source.sync_frequency_hours,
            )

            health["sources"].append(
                {
                    "type": source.source_type,
                    "name": source.name,
                    "state": source.state,
                    "freshness": freshness.level,
                    "message": freshness.message,
                    "last_synced": source.last_synced_at,
                }
            )

        for integration in integrations:
            health["integrations"].append(
                {
                    "platform": integration.platform,
                    "status": integration.status,
                    "connected_account": integration.connected_account,
                    "last_synced": integration.last_synced_at,
                }
            )

        # Overall status
        if any(s["state"] == "error" for s in health["sources"]):
            health["overall_status"] = "error"
        elif any(s["freshness"] == "stale" for s in health["sources"]):
            health["overall_status"] = "stale"
        elif not health["sources"] and not health["integrations"]:
            health["overall_status"] = "no_data"

        return health

    @staticmethod
    def generate_insights(user: User, source_type: str | None = None) -> list[Insight]:
        """Run the Insight Engine and return the insights it touched.

        Delegates to `InsightEngine` so every generation path (API, sync,
        Celery) shares one deterministic, deduplicating pipeline.
        """
        from .engine import InsightEngine

        summary = InsightEngine(user).run(source_types=[source_type] if source_type else None)
        ids = summary.get("insight_ids", [])
        if not ids:
            return []
        return list(Insight.objects.filter(id__in=ids))

    @staticmethod
    def generate_daily_plan(user: User, target_date: date | None = None) -> DailyPlan:
        """Generate or update the morning plan for a date (delegates to daily.py)."""
        from .daily import generate_morning_plan

        return generate_morning_plan(user, target_date)

    @staticmethod
    def create_alert(
        user: User,
        category: str,
        severity: str,
        title: str,
        message: str,
        evidence: str = "",
        source_type: str = "",
        dedup_key: str = "",
    ) -> tuple[Alert, bool]:
        """Create or coalesce an alert.

        Returns ``(alert, created)``. Conditions identified by ``dedup_key``
        (or derived from category + title when not given) reuse the existing
        row: active/read rows bump `occurrences` — refreshing their content
        only once the cooldown has passed — dismissed rows are never
        re-raised, and resolved conditions may fire a fresh row (spec §15).
        """
        now = timezone.now()
        if not dedup_key:
            digest = hashlib.sha1(f"{category}:{title.strip().lower()}".encode()).hexdigest()[:40]
            dedup_key = f"auto:{category}:{digest}"

        existing = (
            Alert.objects.filter(owner=user, dedup_key=dedup_key).order_by("-created_at").first()
        )
        if existing is not None:
            if existing.status == "dismissed":
                return existing, False
            if existing.status == "resolved":
                # The condition cleared and may fire again as a new instance.
                pass
            else:
                within_cooldown = existing.last_fired_at is not None and (
                    now - existing.last_fired_at
                ) < ALERT_COOLDOWN
                existing.occurrences += 1
                existing.last_fired_at = now
                if not within_cooldown:
                    # Cooldown passed — refresh the visible content.
                    existing.message = message
                    existing.evidence = evidence
                    existing.severity = severity
                    existing.title = title
                existing.save()
                return existing, False

        alert = Alert.objects.create(
            owner=user,
            category=category,
            severity=severity,
            title=title,
            message=message,
            evidence=evidence,
            source_type=source_type,
            dedup_key=dedup_key,
            last_fired_at=now,
            occurrences=1,
        )
        return alert, True

    @staticmethod
    def calculate_performance_score(user: User, dimension: str, target_date: date) -> PerformanceMetric | None:
        """Calculate performance score for a dimension."""
        # This is a placeholder - actual implementation would analyze real data
        # Only return a score if sufficient data exists

        # Check if we have data for this dimension
        has_data = False

        if dimension == "development":
            # Check for GitHub commits
            from github.models import Commit

            commit_count = Commit.objects.filter(owner=user, date__gte=target_date - timedelta(days=7)).count()
            has_data = commit_count > 0

        elif dimension == "productivity":
            # Check for tasks
            from productivity.models import Task

            task_count = Task.objects.filter(owner=user).count()
            has_data = task_count > 0

        if not has_data:
            # Don't create a metric with insufficient data
            return None

        # Create placeholder metric (real implementation would calculate from actual data)
        metric, created = PerformanceMetric.objects.get_or_create(
            owner=user,
            dimension=dimension,
            date=target_date,
            defaults={
                "score": None,  # Would be calculated from real data
                "confidence": "low",
                "metrics": {},
                "evidence": [],
                "insights": "Insufficient data for accurate score",
            },
        )

        return metric


class ReportService:
    """Report generation from real persisted data, with full provenance (§16).

    Returns a dict rather than a Report because a report without data would be
    fabrication: when there is nothing to analyze, `insufficient_data` is True
    and nothing is persisted.
    """

    @staticmethod
    def generate_report(
        user: User,
        report_type: str,
        period_start: date,
        period_end: date,
        title: str | None = None,
    ) -> dict[str, Any]:
        if title is None:
            title = f"{report_type.replace('_', ' ').title()} ({period_start} to {period_end})"

        start_dt = timezone.make_aware(timezone.datetime.combine(period_start, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(
            timezone.datetime.combine(period_end, timezone.datetime.max.time())
        )

        sources = list(DataSource.objects.filter(owner=user))
        from github.models import Commit, Issue, PullRequest, Repository
        from productivity.models import Task

        repos = Repository.objects.filter(owner=user)
        commits = Commit.objects.filter(owner=user, date__gte=start_dt, date__lte=end_dt)
        prs = PullRequest.objects.filter(owner=user, created_at__gte=start_dt, created_at__lte=end_dt)
        issues = Issue.objects.filter(owner=user, created_at__gte=start_dt, created_at__lte=end_dt)
        insights = list(
            Insight.objects.filter(owner=user, created_at__gte=start_dt, created_at__lte=end_dt).order_by(
                "-priority", "-created_at"
            )
        )
        alerts = Alert.objects.filter(owner=user, created_at__gte=start_dt, created_at__lte=end_dt)
        tasks_created = Task.objects.filter(owner=user, created_at__gte=start_dt, created_at__lte=end_dt)
        tasks_done = Task.objects.filter(owner=user, status="done", completed_at__gte=start_dt, completed_at__lte=end_dt)
        goals = Goal.objects.filter(owner=user, status="active")
        overdue_goals = [g for g in goals if g.deadline and g.deadline < period_end and g.progress_pct < 100]

        has_any_data = bool(sources or repos.exists() or insights or tasks_created.exists() or goals.exists())
        if not has_any_data:
            return {
                "insufficient_data": True,
                "report": None,
                "message": "No connected data sources, insights, tasks, or goals in this period — "
                "nothing to analyze yet.",
            }

        # ── Real metrics ────────────────────────────────────────────────
        metrics: dict[str, Any] = {
            "commits": commits.count(),
            "pull_requests_opened": prs.count(),
            "issues_opened": issues.count(),
            "repositories": repos.count(),
            "insights_generated": len(insights),
            "alerts_raised": alerts.count(),
            "tasks_created": tasks_created.count(),
            "tasks_completed": tasks_done.count(),
            "active_goals": goals.count(),
            "overdue_goals": len(overdue_goals),
        }

        findings = [
            {
                "title": i.title,
                "severity": i.severity,
                "priority": i.priority,
                "provenance": i.provenance,
                "source_type": i.source_type,
                "evidence": i.structured_evidence[:5],
            }
            for i in insights[:20]
        ]
        recommendations = [
            {"title": i.title, "action": i.recommended_action}
            for i in insights
            if i.recommended_action
        ][:20]

        data_sources = [
            {
                "source_id": str(s.id),
                "source_type": s.source_type,
                "name": s.name,
                "state": s.state,
            }
            for s in sources
        ]
        freshness = {f["source_type"]: f for f in freshness_summary(sources)}

        stale_sources = [f for f in freshness.values() if f["level"] == "stale"]
        limitations = []
        if not sources:
            limitations.append("No data sources connected; GitHub/task metrics reflect stored rows only.")
        if stale_sources:
            limitations.append(
                "Stale sources: " + ", ".join(f["name"] for f in stale_sources) + " — values may have drifted."
            )
        if not repos.exists():
            limitations.append("No GitHub repositories synced for this account.")

        confidence = "high"
        if stale_sources or not sources:
            confidence = "medium"
        if not sources and not repos.exists():
            confidence = "low"

        # ── Deterministic markdown content ──────────────────────────────
        lines = [
            f"# {title}",
            "",
            f"**Period:** {period_start} to {period_end}",
            f"**Provenance:** {Provenance.DETERMINISTIC_ANALYSIS} — all figures computed from persisted data.",
            "",
            "## Activity",
            "",
            f"- Commits: {metrics['commits']}",
            f"- Pull requests opened: {metrics['pull_requests_opened']}",
            f"- Issues opened: {metrics['issues_opened']}",
            f"- Repositories: {metrics['repositories']}",
            "",
            "## Intelligence",
            "",
            f"- Insights generated: {metrics['insights_generated']}",
            f"- Alerts raised: {metrics['alerts_raised']}",
            f"- Tasks created / completed: {metrics['tasks_created']} / {metrics['tasks_completed']}",
            f"- Goals active / overdue: {metrics['active_goals']} / {metrics['overdue_goals']}",
            "",
            "## Data Sources",
            "",
        ]
        if data_sources:
            for entry in data_sources:
                f = freshness.get(entry["source_type"], {})
                age = f" — {f.get('message')}" if f.get("message") else ""
                lines.append(f"- {entry['name']} ({entry['source_type']}, {f.get('level', 'unknown')}){age}")
        else:
            lines.append("- None connected.")

        if findings:
            lines += ["", "## Findings", ""]
            for finding in findings:
                lines.append(f"- **[{finding['severity']}]** {finding['title']} — {finding['provenance']}")

        if recommendations:
            lines += ["", "## Recommendations", ""]
            for rec in recommendations:
                lines.append(f"- {rec['title']}: {rec['action']}")

        if limitations:
            lines += ["", "## Limitations", ""]
            lines += [f"- {lim}" for lim in limitations]

        summary_text = (
            f"{metrics['commits']} commits, {metrics['pull_requests_opened']} PRs, "
            f"{metrics['insights_generated']} insights, {metrics['tasks_completed']} tasks completed "
            f"between {period_start} and {period_end}."
        )

        report = Report.objects.create(
            owner=user,
            report_type=report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            content="\n".join(lines),
            summary=summary_text,
            data_sources=data_sources,
            data_freshness=freshness,
            provenance=Provenance.DETERMINISTIC_ANALYSIS,
            insufficient_data=False,
            metrics=metrics,
            findings=findings,
            recommendations=recommendations,
            confidence=confidence,
            limitations=" ".join(limitations),
        )
        return {"insufficient_data": False, "report": report, "message": "Report generated."}
