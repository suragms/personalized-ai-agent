"""Project Performance domain models."""
from django.conf import settings
from django.db import models

from core.models import MetricModel, TimeStampedModel, UUIDModel


class Project(UUIDModel, TimeStampedModel):
    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("active", "Active"),
        ("on_hold", "On hold"),
        ("completed", "Completed"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    client = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Progress by phase (weighted into an overall completion %).
    backend_pct = models.PositiveIntegerField(default=0)
    frontend_pct = models.PositiveIntegerField(default=0)
    testing_pct = models.PositiveIntegerField(default=0)
    deployment_pct = models.PositiveIntegerField(default=0)
    pending_bugs = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def completion_pct(self) -> float:
        return round(self.backend_pct * 0.35 + self.frontend_pct * 0.35 + self.testing_pct * 0.15 + self.deployment_pct * 0.15, 1)


class Milestone(UUIDModel, TimeStampedModel):
    STATUS_CHOICES = [("pending", "Pending"), ("in_progress", "In progress"), ("completed", "Completed")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    completed_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self) -> str:
        return f"{self.project.name}: {self.title}"


class ProgressSnapshot(MetricModel):
    """A point-in-time record of a project's progress (burndown source)."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="snapshots")
    backend_pct = models.PositiveIntegerField(default=0)
    frontend_pct = models.PositiveIntegerField(default=0)
    testing_pct = models.PositiveIntegerField(default=0)
    deployment_pct = models.PositiveIntegerField(default=0)
    pending_bugs = models.PositiveIntegerField(default=0)
    risk_score = models.FloatField(default=0.0)

    class Meta(MetricModel.Meta):
        constraints = [models.UniqueConstraint(fields=["project", "date"], name="unique_snapshot")]

    def __str__(self) -> str:
        return f"{self.project.name} @ {self.date}"
