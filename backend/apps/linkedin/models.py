"""LinkedIn optimization domain models."""
from datetime import date

from django.conf import settings
from django.db import models

from core.models import UUIDModel


class LinkedInProfile(UUIDModel):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="linkedin_profile")
    headline = models.CharField(max_length=220, blank=True)
    about = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    experience = models.JSONField(default=list, blank=True)  # [{title, company, period, bullets}]
    skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.headline or self.owner.username


class ProfileScore(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="linkedin_scores")
    date = models.DateField(default=date.today, db_index=True)
    score = models.FloatField(default=0.0)
    breakdown = models.JSONField(default=dict, blank=True)  # {"headline": 20, ...}
    suggestions = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["owner", "date"], name="unique_linkedin_score")]

    def __str__(self) -> str:
        return f"{self.date}: {self.score}"


class PostIdea(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_ideas")
    topic = models.CharField(max_length=200)
    content = models.TextField()
    hashtags = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=64, default="agent")  # agent | manual
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.topic
