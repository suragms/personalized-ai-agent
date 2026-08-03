"""Long-term memory store (pgvector).

`MemoryEntry` holds facts, decisions, and context with an embedding vector for
semantic search. `ConversationLog` records AI interactions. `UserPreference`
persists user choices so the platform "remembers previous decisions".
"""
from datetime import date

from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from core.models import UUIDModel


class MemoryEntry(UUIDModel):
    KIND_CHOICES = [
        ("fact", "Fact"),
        ("decision", "Decision"),
        ("preference", "Preference"),
        ("project", "Project context"),
        ("note", "Note"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memories")
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default="note", db_index=True)
    content = models.TextField()
    embedding = VectorField(dimensions=settings.AI_EMBEDDING_DIM, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    date = models.DateField(default=date.today, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "kind"])]

    def __str__(self) -> str:
        return f"{self.kind}: {self.content[:60]}"


class ConversationLog(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    role = models.CharField(max_length=16)  # user | assistant
    content = models.TextField()
    intent = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class UserPreference(UUIDModel):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")
    key = models.CharField(max_length=64)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("owner", "key")

    def __str__(self) -> str:
        return f"{self.key} → {self.value}"
