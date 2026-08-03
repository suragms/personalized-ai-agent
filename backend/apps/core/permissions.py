"""Role-based access control helpers.

Roles: OWNER (full control) > ADMIN (manage data) > VIEWER (read-only).
"""
from rest_framework.permissions import BasePermission


class RoleMixin:
    """Constants + helpers shared by models carrying a `role` field."""

    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"

    ROLES = ((OWNER, "Owner"), (ADMIN, "Admin"), (VIEWER, "Viewer"))

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


class IsOwner(BasePermission):
    """Only the OWNER may perform the request."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == "owner")


class IsOwnerOrAdmin(BasePermission):
    """OWNER and ADMIN may write; VIEWER is read-only."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return user.role in {"owner", "admin"}


class IsReadOnly(BasePermission):
    """Any authenticated user may read; writes require OWNER/ADMIN."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return request.user.role in {"owner", "admin"}
