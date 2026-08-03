"""Learning domain models: tracked items, suggestions, roadmaps."""
from django.conf import settings
from django.db import models

from core.models import UUIDModel


class LearningItem(UUIDModel):
    KIND_CHOICES = [("course", "Course"), ("docs", "Documentation"), ("trend", "Trend"), ("tool", "Tool"), ("book", "Book")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_items")
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    title = models.CharField(max_length=300)
    url = models.URLField(blank=True)
    reason = models.TextField(blank=True)
    priority = models.CharField(max_length=16, default="medium")
    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class LearningSuggestion(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_suggestions")
    date = models.DateField(db_index=True)
    kind = models.CharField(max_length=16, choices=LearningItem.KIND_CHOICES, default="trend")
    title = models.CharField(max_length=300)
    reason = models.TextField(blank=True)
    source = models.CharField(max_length=64, default="agent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["owner", "date", "title"], name="unique_suggestion")]

    def __str__(self) -> str:
        return f"{self.date}: {self.title}"


class LearningRoadmap(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_roadmaps")
    title = models.CharField(max_length=200)
    level = models.CharField(max_length=32, default="intermediate")
    items = models.JSONField(default=list, blank=True)  # [{topic, resource, why}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
