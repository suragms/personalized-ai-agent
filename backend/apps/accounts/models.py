from django.contrib.auth.models import AbstractUser
from django.db import models

from core.permissions import RoleMixin

from .managers import UserManager


class User(AbstractUser, RoleMixin):
    """Platform user with a role for role-based access control."""

    role = models.CharField(
        max_length=16,
        choices=RoleMixin.ROLES,
        default=RoleMixin.VIEWER,
        db_index=True,
    )
    github_username = models.CharField(max_length=64, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)

    objects = UserManager()

    def __str__(self) -> str:
        return self.username

    @property
    def is_owner(self) -> bool:
        return self.role == RoleMixin.OWNER
