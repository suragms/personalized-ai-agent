"""Analytics snapshot model — cached cross-module aggregations."""
from datetime import date

from django.conf import settings
from django.db import models

from core.models import UUIDModel


class AnalyticsSnapshot(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analytics_snapshots")
    module = models.CharField(max_length=32, db_index=True)  # coding | projects | time | learning | linkedin | resume | business
    date = models.DateField(default=date.today, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["owner", "module", "date"], name="unique_analytics_snapshot")]

    def __str__(self) -> str:
        return f"{self.module} @ {self.date}"
