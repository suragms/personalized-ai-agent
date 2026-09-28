"""GitHub OAuth integration for data access (separate from auth OAuth).

This implements OAuth specifically for accessing GitHub data:
- Repository access
- Commit history
- Issues and PRs
- User profile data

Separate from accounts.oauth which is for authentication only.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from django.conf import settings
from django.utils import timezone

from accounts.models import User
from intelligence.models import IntegrationConnection

logger = logging.getLogger("github")

GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

# Minimal scopes needed for data access
REQUIRED_SCOPES = ["read:user", "repo", "read:org"]


class GitHubOAuthError(Exception):
    """GitHub OAuth error."""

    pass


def get_authorization_url(state: str, redirect_uri: str) -> str:
    """Generate GitHub OAuth authorization URL."""
    if not settings.GITHUB_CLIENT_ID:
        raise GitHubOAuthError("GITHUB_CLIENT_ID not configured")

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": " ".join(REQUIRED_SCOPES),
        "state": state,
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GITHUB_OAUTH_URL}?{query}"


def exchange_code(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange OAuth code for access token."""
    if not (settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET):
        raise GitHubOAuthError("GitHub OAuth not configured")

    try:
        response = httpx.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise GitHubOAuthError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

        access_token = data.get("access_token")
        if not access_token:
            raise GitHubOAuthError("No access token in response")

        return {
            "access_token": access_token,
            "token_type": data.get("token_type", "bearer"),
            "scope": data.get("scope", ""),
        }

    except httpx.HTTPError as e:
        logger.error(f"GitHub OAuth exchange failed: {e}")
        raise GitHubOAuthError(f"Network error during OAuth: {e}")


def get_user_info(access_token: str) -> dict[str, Any]:
    """Fetch GitHub user info with access token."""
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = httpx.get(f"{GITHUB_API_BASE}/user", headers=headers, timeout=15)
        response.raise_for_status()

        return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch GitHub user info: {e}")
        raise GitHubOAuthError(f"Failed to fetch user info: {e}")


def create_or_update_connection(
    user: User, access_token: str, refresh_token: str | None = None, expires_in: int | None = None
) -> IntegrationConnection:
    """Create or update GitHub integration connection."""
    # Get user info to verify token and get username
    user_info = get_user_info(access_token)
    github_username = user_info.get("login")
    github_id = user_info.get("id")

    # Calculate expiration (GitHub tokens typically don't expire, but handle if they do)
    expires_at = None
    if expires_in:
        expires_at = timezone.now() + timedelta(seconds=expires_in)

    # Create or update connection
    connection, created = IntegrationConnection.objects.update_or_create(
        owner=user,
        platform="github",
        defaults={
            "status": "connected",
            "access_token": access_token,  # Will be encrypted by model
            "refresh_token": refresh_token or "",
            "expires_at": expires_at,
            "connected_account": github_username,
            "scopes": REQUIRED_SCOPES,
            "last_synced_at": None,  # Will be set on first sync
            "last_error": "",
        },
    )

    # Update user's GitHub username if not set
    if not user.github_username and github_username:
        user.github_username = github_username
        user.save(update_fields=["github_username"])

    logger.info(f"GitHub connection {'created' if created else 'updated'} for {user.username} (GitHub: {github_username})")

    return connection


def disconnect(user: User) -> None:
    """Disconnect GitHub integration."""
    try:
        connection = IntegrationConnection.objects.get(owner=user, platform="github")
        connection.status = "disconnected"
        connection.access_token = ""
        connection.refresh_token = ""
        connection.save()
        logger.info(f"GitHub disconnected for {user.username}")
    except IntegrationConnection.DoesNotExist:
        logger.warning(f"No GitHub connection found for {user.username}")


def get_connection(user: User) -> IntegrationConnection | None:
    """Get user's GitHub connection if it exists and is valid."""
    try:
        connection = IntegrationConnection.objects.get(owner=user, platform="github")

        if connection.status != "connected":
            return None

        # Check if token is expired
        if connection.expires_at and connection.expires_at < timezone.now():
            connection.status = "expired"
            connection.save()
            return None

        return connection

    except IntegrationConnection.DoesNotExist:
        return None


def verify_connection(connection: IntegrationConnection) -> bool:
    """Verify that the GitHub connection is still valid."""
    try:
        get_user_info(connection.access_token)
        return True
    except GitHubOAuthError:
        connection.status = "error"
        connection.last_error = "Token verification failed"
        connection.save()
        return False


def make_api_request(connection: IntegrationConnection, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    """Make authenticated GitHub API request."""
    if connection.status != "connected":
        raise GitHubOAuthError(f"Connection not active: {connection.status}")

    headers = {
        "Authorization": f"Bearer {connection.access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"{GITHUB_API_BASE}{endpoint}"

    try:
        response = httpx.get(url, headers=headers, params=params or {}, timeout=30)

        # Handle rate limiting
        if response.status_code == 403:
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
            if rate_limit_remaining == "0":
                reset_time = response.headers.get("X-RateLimit-Reset")
                error_msg = f"Rate limit exceeded. Resets at {reset_time}"
                logger.warning(error_msg)
                connection.last_error = error_msg
                connection.save()
                raise GitHubOAuthError(error_msg)

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as e:
        error_msg = f"GitHub API request failed: {e}"
        logger.error(error_msg)
        connection.last_error = error_msg
        connection.save()
        raise GitHubOAuthError(error_msg)
