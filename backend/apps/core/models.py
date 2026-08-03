"""Base models and mixins shared across the platform.

Every domain model extends these to get UUID primary keys, automatic
created/updated timestamps, and an `owner` reference for scoping.
"""
import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """Abstract model with a UUID primary key (non-enumerable)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OwnedModel(UUIDModel, TimeStampedModel):
    """Base model owned by a platform user; forms the spine of most entities."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class MetricModel(UUIDModel, TimeStampedModel):
    """Base model for point-in-time metric snapshots (time series)."""

    date = models.DateField(db_index=True)

    class Meta:
        abstract = True
        ordering = ["date"]
