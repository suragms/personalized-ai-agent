"""Report domain model — a generated report with export formats."""
from django.conf import settings
from django.db import models

from core.models import UUIDModel


class Report(UUIDModel):
    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
        ("internship", "Internship"),
        ("client", "Client"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    period = models.CharField(max_length=16, choices=PERIOD_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    period_start = models.DateField()
    period_end = models.DateField()
    content = models.TextField()  # markdown
    html = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    generated_by = models.CharField(max_length=64, default="reports-agent")
    # What actually produced `content`: REAL_AI_PROVIDER | MOCK_PROVIDER |
    # DETERMINISTIC_TEMPLATE. Never presented as AI output when it was not.
    provenance = models.CharField(max_length=32, blank=True, default="DETERMINISTIC_TEMPLATE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start", "-created_at"]
        indexes = [models.Index(fields=["owner", "period", "period_start"])]
        constraints = [models.UniqueConstraint(fields=["owner", "period", "period_start"], name="unique_report")]

    def __str__(self) -> str:
        return f"{self.title} ({self.period})"
