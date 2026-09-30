"""Daily productivity domain models: tasks, calendar, focus sessions, briefings."""
from django.db import models

from core.models import OwnedModel


class Task(OwnedModel):
    STATUS_CHOICES = [
        ("todo", "To do"),
        ("in_progress", "In progress"),
        ("done", "Done"),
        ("blocked", "Blocked"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="todo", db_index=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default="medium", db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    estimated_hours = models.FloatField(default=1.0)
    completed_at = models.DateTimeField(null=True, blank=True)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )

    # Provenance when a task was generated from an insight (spec §14).
    source_insight = models.ForeignKey(
        "intelligence.Insight", on_delete=models.SET_NULL, null=True, blank=True, related_name="derived_tasks"
    )
    provenance = models.CharField(max_length=32, blank=True, default="")
    evidence = models.JSONField(default=list, blank=True)
    dedup_key = models.CharField(max_length=200, blank=True, default="", db_index=True)

    class Meta(OwnedModel.Meta):
        indexes = [models.Index(fields=["owner", "status"])]

    def __str__(self) -> str:
        return self.title


class CalendarEvent(OwnedModel):
    title = models.CharField(max_length=300)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=True)

    class Meta:
        ordering = ["start"]

    def __str__(self) -> str:
        return self.title


class FocusSession(OwnedModel):
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    focus_score = models.FloatField(default=0.0)  # 0-100

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.duration_minutes}min @ {self.started_at:%d %b}"


class Briefing(OwnedModel):
    KIND_CHOICES = [("morning", "Morning briefing"), ("eod", "End of day wrap-up")]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    date = models.DateField(db_index=True)
    content = models.TextField()  # markdown
    data = models.JSONField(default=dict, blank=True)
    # What actually produced `content`: REAL_AI_PROVIDER | MOCK_PROVIDER |
    # DETERMINISTIC_TEMPLATE.
    provenance = models.CharField(max_length=32, blank=True, default="DETERMINISTIC_TEMPLATE")

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["owner", "kind", "date"], name="unique_briefing")]

    def __str__(self) -> str:
        return f"{self.kind} {self.date}"
