"""Portfolio domain models — projects auto-synced from GitHub activity."""
from django.conf import settings
from django.db import models

from core.models import UUIDModel


class PortfolioProject(UUIDModel):
    DEPLOYMENT_CHOICES = [
        ("live", "Live"),
        ("staging", "Staging"),
        ("not_deployed", "Not deployed"),
        ("archived", "Archived"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio_projects")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    repository = models.OneToOneField(
        "github.Repository",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portfolio_project",
    )
    skills = models.JSONField(default=list, blank=True)
    screenshots = models.JSONField(default=list, blank=True)
    readme = models.TextField(blank=True)
    deployment_status = models.CharField(max_length=16, choices=DEPLOYMENT_CHOICES, default="not_deployed")
    live_url = models.URLField(blank=True)
    last_release_tag = models.CharField(max_length=64, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name


class PortfolioSettings(UUIDModel):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio_settings")
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    theme = models.CharField(max_length=32, default="dark")
    sections_order = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Portfolio settings for {self.owner.username}"
