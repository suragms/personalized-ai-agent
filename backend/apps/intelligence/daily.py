"""Daily plan generation — deterministic morning brief and evening review.

Everything here is aggregated from persisted rows (insights, alerts, tasks,
goals, sources). No LLM: the plan must be reproducible and auditable (§16).
"""
from __future__ import annotations

import logging
from datetime import date as date_cls
from datetime import timedelta

from django.utils import timezone

from accounts.models import User

from .models import Alert, DailyPlan, DataSource, Goal, Insight, IntegrationConnection
from .provenance import compute_freshness

logger = logging.getLogger("intelligence")

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _plan_for(user: User, target_date: date_cls | None) -> DailyPlan:
    target_date = target_date or timezone.now().date()
    plan, _ = DailyPlan.objects.get_or_create(owner=user, date=target_date)
    return plan


def generate_morning_plan(user: User, target_date: date_cls | None = None) -> DailyPlan:
    """Build/update the morning brief for a date."""
    plan = _plan_for(user, target_date)
    target = plan.date

    top_insights = sorted(
        Insight.objects.filter(owner=user, status__in=("new", "reviewed")),
        key=lambda i: (PRIORITY_RANK.get(i.severity, 9), i.title),
    )[:5]

    active_goals = list(Goal.objects.filter(owner=user, status="active").order_by("-priority")[:3])

    plan.priorities = [
        {"kind": "insight", "id": str(i.id), "title": i.title, "priority": i.priority, "severity": i.severity}
        for i in top_insights
    ] + [
        {"kind": "goal", "id": str(g.id), "title": g.title, "priority": g.priority, "progress": g.progress_pct}
        for g in active_goals
    ][:5]

    plan.important_alerts = [
        str(a) for a in
        Alert.objects.filter(owner=user, status="active").order_by("-severity", "-created_at")
        .values_list("id", flat=True)[:5]
    ]

    plan.upcoming_deadlines = [
        {"goal_id": str(g.id), "title": g.title, "deadline": g.deadline.isoformat()}
        for g in Goal.objects.filter(owner=user, status="active", deadline__gte=target, deadline__lte=target + timedelta(days=7)).order_by("deadline")
    ]

    # Deterministic focus text: the most urgent confirmed findings first.
    focus_lines = []
    for insight in top_insights[:3]:
        action = insight.recommended_action or "Review the evidence and decide."
        focus_lines.append(f"- {insight.title} → {action}")
    plan.recommended_focus = "\n".join(focus_lines) if focus_lines else "No urgent findings — keep up the routine."

    blockers: list[dict] = []
    for source in DataSource.objects.filter(owner=user):
        freshness = compute_freshness(
            source.last_synced_at, source.source_type, sync_frequency_hours=source.sync_frequency_hours
        )
        if freshness.level in ("stale", "unavailable"):
            blockers.append(
                {
                    "kind": "data_source",
                    "name": source.name,
                    "level": freshness.level,
                    "message": freshness.message,
                }
            )
    for conn in IntegrationConnection.objects.filter(owner=user).exclude(
        status__in=("connected", "connecting", "not_configured")
    ):
        blockers.append({"kind": "integration", "platform": conn.platform, "status": conn.status})
    for goal in Goal.objects.filter(owner=user, status="active"):
        if goal.deadline and goal.deadline < target and goal.progress_pct < 100:
            blockers.append(
                {"kind": "goal_overdue", "id": str(goal.id), "title": goal.title, "deadline": goal.deadline.isoformat()}
            )
    plan.potential_blockers = blockers

    from productivity.models import Task

    plan.tasks = [
        str(t) for t in
        Task.objects.filter(owner=user).exclude(status="done").filter(due_date__lte=target)
        .order_by("due_date")
        .values_list("id", flat=True)[:10]
    ]

    plan.save()
    return plan


def generate_evening_review(user: User, target_date: date_cls | None = None) -> DailyPlan:
    """Build/update the evening review for a date."""
    plan = _plan_for(user, target_date)
    target = plan.date

    from productivity.models import Task

    day_start = timezone.make_aware(timezone.datetime.combine(target, timezone.datetime.min.time()))
    day_end = timezone.make_aware(timezone.datetime.combine(target, timezone.datetime.max.time()))

    completed = list(
        Task.objects.filter(owner=user, status="done", completed_at__gte=day_start, completed_at__lte=day_end)
    )
    incomplete = list(
        Task.objects.filter(owner=user).exclude(status="done").filter(due_date__lte=target)
    )

    plan.completed_tasks = [str(t.id) for t in completed]
    plan.incomplete_tasks = [str(t.id) for t in incomplete]

    new_insights = Insight.objects.filter(owner=user, last_confirmed_at__gte=day_start, last_confirmed_at__lte=day_end).count()
    alerts_today = Alert.objects.filter(owner=user, created_at__gte=day_start, created_at__lte=day_end).count()

    plan.evening_insights = (
        f"Completed {len(completed)} task(s); {len(incomplete)} still open. "
        f"{new_insights} insight(s) confirmed from data today; {alerts_today} alert(s) raised."
    )

    plan.tomorrow_priorities = [
        {"id": str(t.id), "title": t.title, "priority": t.priority, "due_date": t.due_date.isoformat() if t.due_date else None}
        for t in sorted(incomplete, key=lambda t: PRIORITY_RANK.get(t.priority, 9))[:5]
    ]

    plan.reviewed_at = timezone.now()
    plan.save()
    return plan
