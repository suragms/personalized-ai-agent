"""Intelligence Engine service layer — core business logic."""
import logging
from datetime import date, datetime, timedelta
from typing import Any

from django.db.models import Q
from django.utils import timezone

from accounts.models import User

from .models import (
    Alert,
    DailyPlan,
    DataSnapshot,
    DataSource,
    Decision,
    Goal,
    Insight,
    IntegrationConnection,
    PerformanceMetric,
    Report,
    UserProfile,
)

logger = logging.getLogger("intelligence")


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
            freshness = "unavailable"
            if source.last_synced_at:
                hours_ago = (timezone.now() - source.last_synced_at).total_seconds() / 3600
                if hours_ago < source.sync_frequency_hours:
                    freshness = "fresh"
                elif hours_ago < source.sync_frequency_hours * 2:
                    freshness = "stale"
                else:
                    freshness = "very_stale"

            health["sources"].append(
                {
                    "type": source.source_type,
                    "name": source.name,
                    "state": source.state,
                    "freshness": freshness,
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
        elif any(s["freshness"] == "very_stale" for s in health["sources"]):
            health["overall_status"] = "stale"
        elif not health["sources"] and not health["integrations"]:
            health["overall_status"] = "no_data"

        return health

    @staticmethod
    def generate_insights(user: User, source_type: str | None = None) -> list[Insight]:
        """Generate insights from available data sources."""
        insights = []

        # Get data sources
        sources = DataSource.objects.filter(owner=user)
        if source_type:
            sources = sources.filter(source_type=source_type)

        # Generate GitHub insights if GitHub is connected
        if source_type == "github" or source_type is None:
            try:
                from github.insights import GitHubInsightsGenerator

                github_generator = GitHubInsightsGenerator(user)
                github_insights = github_generator.generate_all()
                insights.extend(github_insights)
            except Exception as e:
                logger.warning(f"Failed to generate GitHub insights: {e}")

        # Check for stale data sources
        for source in sources:
            if source.last_synced_at:
                days_since_sync = (timezone.now() - source.last_synced_at).days
                if days_since_sync > 7:
                    insight = Insight.objects.create(
                        owner=user,
                        insight_type="risk",
                        severity="medium",
                        confidence="high",
                        title=f"{source.name} data is stale",
                        description=f"Your {source.source_type} data hasn't been updated in {days_since_sync} days.",
                        evidence=f"Last sync: {source.last_synced_at.isoformat()}",
                        source_references=[{"source_id": str(source.id), "source_type": source.source_type}],
                        recommended_action=f"Reconnect {source.source_type} integration or trigger manual sync.",
                    )
                    insights.append(insight)

        # Check for incomplete goals
        goals = Goal.objects.filter(owner=user, status="active")
        for goal in goals:
            if goal.deadline and goal.deadline < date.today() and goal.progress_pct < 100:
                insight = Insight.objects.create(
                    owner=user,
                    insight_type="blocker",
                    severity="high",
                    confidence="high",
                    title=f"Goal deadline passed: {goal.title}",
                    description=f"This goal was due on {goal.deadline} but is only {goal.progress_pct}% complete.",
                    evidence=f"Goal: {goal.title}, Progress: {goal.progress_pct}%, Deadline: {goal.deadline}",
                    source_references=[{"goal_id": str(goal.id)}],
                    recommended_action="Review and update goal status or adjust deadline.",
                )
                insights.append(insight)

        return insights

    @staticmethod
    def generate_daily_plan(user: User, target_date: date | None = None) -> DailyPlan:
        """Generate or update daily plan."""
        if target_date is None:
            target_date = date.today()

        plan, created = DailyPlan.objects.get_or_create(owner=user, date=target_date)

        # Get priorities from active goals
        active_goals = Goal.objects.filter(owner=user, status="active").order_by("-priority")[:3]
        plan.priorities = [{"goal_id": str(g.id), "title": g.title, "priority": g.priority} for g in active_goals]

        # Get active alerts
        active_alerts = Alert.objects.filter(owner=user, status="active").order_by("-severity")[:5]
        plan.important_alerts = [alert.id for alert in active_alerts]

        # Get upcoming deadlines
        upcoming = Goal.objects.filter(
            owner=user, status="active", deadline__gte=target_date, deadline__lte=target_date + timedelta(days=7)
        ).order_by("deadline")
        plan.upcoming_deadlines = [{"goal_id": str(g.id), "title": g.title, "deadline": g.deadline.isoformat()} for g in upcoming]

        plan.save()
        return plan

    @staticmethod
    def create_alert(
        user: User,
        category: str,
        severity: str,
        title: str,
        message: str,
        evidence: str = "",
        source_type: str = "",
    ) -> Alert:
        """Create a new alert."""
        return Alert.objects.create(
            owner=user,
            category=category,
            severity=severity,
            title=title,
            message=message,
            evidence=evidence,
            source_type=source_type,
        )

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
    """Report generation with full provenance."""

    @staticmethod
    def generate_report(
        user: User,
        report_type: str,
        period_start: date,
        period_end: date,
        title: str | None = None,
    ) -> Report:
        """Generate a report with data provenance."""
        if title is None:
            title = f"{report_type.replace('_', ' ').title()} ({period_start} to {period_end})"

        # Collect data sources used
        data_sources = []
        data_freshness = {}

        sources = DataSource.objects.filter(owner=user)
        for source in sources:
            data_sources.append(
                {
                    "source_id": str(source.id),
                    "source_type": source.source_type,
                    "name": source.name,
                }
            )
            if source.last_synced_at:
                data_freshness[source.source_type] = source.last_synced_at.isoformat()

        # Generate content (placeholder - real implementation would analyze data)
        content = f"# {title}\n\n"
        content += f"**Period:** {period_start} to {period_end}\n\n"
        content += "## Data Sources\n\n"

        if not data_sources:
            content += "⚠️ No data sources connected. Connect your accounts to generate meaningful reports.\n\n"
        else:
            for source in data_sources:
                content += f"- {source['name']} ({source['source_type']})\n"

        content += "\n## Summary\n\n"
        content += "This report requires connected data sources to generate insights.\n"

        summary = "Report generated but awaiting connected data sources."
        limitations = ""

        if not data_sources:
            limitations = "No data sources connected. This report cannot provide meaningful analysis."

        report = Report.objects.create(
            owner=user,
            report_type=report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            content=content,
            summary=summary,
            data_sources=data_sources,
            data_freshness=data_freshness,
            metrics={},
            findings=[],
            recommendations=[],
            confidence="low" if not data_sources else "medium",
            limitations=limitations,
        )

        return report
