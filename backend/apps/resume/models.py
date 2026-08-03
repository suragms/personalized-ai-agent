"""Resume domain model — versioned resumes with ATS scoring."""
from django.conf import settings
from django.db import models

from core.models import UUIDModel


class ResumeVersion(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    version_number = models.PositiveIntegerField(default=1)
    full_name = models.CharField(max_length=160, blank=True)
    title = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    contact = models.JSONField(default=dict, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    ats_score = models.FloatField(default=0.0)
    keywords_missing = models.JSONField(default=list, blank=True)
    content = models.TextField(blank=True)  # markdown representation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [models.UniqueConstraint(fields=["owner", "version_number"], name="unique_resume_version")]

    def __str__(self) -> str:
        return f"{self.full_name} v{self.version_number}"
