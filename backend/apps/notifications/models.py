"""Notifications domain models — in-app alerts and their rules."""
from django.conf import settings
from django.db import models

from core.models import UUIDModel


class Notification(UUIDModel):
    KIND_CHOICES = [
        ("morning", "Morning briefing"),
        ("deadline", "Deadline reminder"),
        ("productivity", "Low productivity"),
        ("inactive_repo", "Inactive repository"),
        ("project_delay", "Project delay"),
        ("learning", "Learning reminder"),
        ("github", "GitHub reminder"),
        ("deployment", "Deployment reminder"),
        ("info", "Info"),
    ]
    SEVERITY_CHOICES = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info")
    link = models.CharField(max_length=300, blank=True)
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "read"])]

    def __str__(self) -> str:
        return self.title


class NotificationRule(UUIDModel):
    RULE_CHOICES = [
        ("deadline_reminder", "Deadline reminder"),
        ("inactive_repo", "Inactive repository"),
        ("low_productivity", "Low productivity"),
        ("project_delay", "Project delay"),
        ("github_streak", "GitHub streak"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_rules")
    rule_type = models.CharField(max_length=32, choices=RULE_CHOICES, db_index=True)
    enabled = models.BooleanField(default=True)
    threshold = models.IntegerField(default=0)  # e.g. days of inactivity, productivity cutoff
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "rule_type"], name="unique_notification_rule")]

    def __str__(self) -> str:
        return f"{self.rule_type} ({'on' if self.enabled else 'off'})"
