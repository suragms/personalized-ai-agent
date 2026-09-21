"""Notification services — rule-based sweep that surfaces actionable alerts."""
import logging
from datetime import date, timedelta

from django.utils import timezone

from ai.types import AgentResult

from .models import Notification, NotificationRule

logger = logging.getLogger("agents")


def _broadcast(notification: Notification) -> None:
    """Push a notification to the user's WebSocket group (fire-and-forget)."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        group_name = f"notifications_{notification.owner_id}"
        payload = {
            "id": str(notification.id),
            "kind": notification.kind,
            "title": notification.title,
            "body": notification.body,
            "severity": notification.severity,
            "link": notification.link,
            "read": notification.read,
            "created_at": notification.created_at.isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "notification.new", "notification": payload},
        )
    except Exception:
        logger.debug("WebSocket broadcast skipped (channel layer unavailable)")


def _create(owner, kind, title, body="", severity="info", link="", dedup_hours=24) -> bool:
    """Create a notification unless a very similar one exists recently. Returns True if created."""
    cutoff = timezone.now() - timedelta(hours=dedup_hours)
    if Notification.objects.filter(owner=owner, kind=kind, title=title, created_at__gte=cutoff).exists():
        return False
    notification = Notification.objects.create(owner=owner, kind=kind, title=title, body=body, severity=severity, link=link)
    _broadcast(notification)
    return True


def _rule(owner, rule_type) -> bool:
    rule = NotificationRule.objects.filter(owner=owner, rule_type=rule_type).first()
    return rule.enabled if rule else True


def sweep_for(owner) -> int:
    """Evaluate all notification rules for a user, creating alerts. Returns count added."""
    created = 0
    from github.models import Commit, Repository
    from productivity.models import Task
    from projects.models import Project

    # Deadline reminders
    if _rule(owner, "deadline_reminder"):
        today = date.today()
        for task in Task.objects.filter(owner=owner, due_date__lte=today).exclude(status="done"):
            created += int(_create(owner, "deadline", f"Overdue: {task.title}", severity="critical", link="/tasks"))
        due_tomorrow = Task.objects.filter(owner=owner, due_date=today + timedelta(days=1)).exclude(status="done")
        for task in due_tomorrow:
            created += int(_create(owner, "deadline", f"Due tomorrow: {task.title}", link="/tasks"))

    # Inactive repositories
    if _rule(owner, "inactive_repo"):
        for repo in Repository.objects.filter(owner=owner, status="inactive"):
            created += int(
                _create(owner, "inactive_repo", f"{repo.full_name} is inactive", f"No commits in {repo.last_commit_days} days.", link="/github")
            )

    # Low productivity
    if _rule(owner, "low_productivity"):
        week_commits = Commit.objects.filter(owner=owner, date__gte=timezone.now() - timedelta(days=7)).count()
        if week_commits == 0:
            created += int(_create(owner, "productivity", "No commits this week", "Kick off with a small PR to protect your streak.", severity="warning", link="/github"))

    # Project delays
    if _rule(owner, "project_delay"):
        for project in Project.objects.filter(owner=owner).exclude(status="completed"):
            if project.end_date and project.end_date < date.today():
                created += int(
                    _create(owner, "project_delay", f"{project.name} is past its deadline", f"Ended {project.end_date}", severity="warning", link="/projects")
                )

    return created


def recent_notifications(owner, limit: int = 20) -> list[Notification]:
    return list(Notification.objects.filter(owner=owner)[:limit])


def unread_count(owner) -> int:
    return Notification.objects.filter(owner=owner, read=False).count()


def mark_read(owner, notification_id: str | None = None) -> int:
    """Mark one notification (or all, when no id) as read. Returns rows updated."""
    qs = Notification.objects.filter(owner=owner)
    if notification_id:
        qs = qs.filter(id=notification_id)
    return qs.update(read=True)


def run_agent(owner) -> AgentResult:
    count = sweep_for(owner)
    return AgentResult(
        agent="notifications",
        status="ok",
        summary=f"{count} notification(s) created",
        output=f"Swept notification rules — {count} new alert(s).",
        data={"created": count, "unread": unread_count(owner)},
    )
