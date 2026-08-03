"""Manual OAuth code-exchange flows for GitHub and Google.

These implement the Authorization Code flow server-side: the frontend redirects
the user to the provider, receives a `code`, and POSTs it here. The backend
exchanges the code for a token, fetches the profile, and mints a JWT pair.

Providers are enabled individually by setting their client id/secret and
ALLOW_OAUTH=True in the environment.
"""
import logging

import httpx
from django.conf import settings

logger = logging.getLogger("accounts")


class OAuthDisabledError(Exception):
    pass


def _guard_enabled(provider: str):
    if not settings.ALLOW_OAUTH:
        raise OAuthDisabledError("OAuth is disabled. Set ALLOW_OAUTH=True in the environment.")


def github_exchange(code: str, redirect_uri: str) -> dict:
    """Exchange a GitHub OAuth code for a profile dict."""
    _guard_enabled("github")
    if not (settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET):
        raise OAuthDisabledError("GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET are not configured.")

    token_resp = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
        timeout=15,
    )
    token_resp.raise_for_status()
    token = token_resp.json().get("access_token")
    if not token:
        raise OAuthDisabledError(f"GitHub token exchange failed: {token_resp.json()}")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    user = httpx.get("https://api.github.com/user", headers=headers, timeout=15).json()
    emails = httpx.get("https://api.github.com/user/emails", headers=headers, timeout=15).json()
    primary_email = next((e["email"] for e in emails if e.get("primary")), None)
    return {
        "provider": "github",
        "provider_id": str(user.get("id", "")),
        "username": user.get("login", ""),
        "email": primary_email or user.get("email") or "",
        "name": user.get("name") or "",
        "avatar_url": user.get("avatar_url", ""),
    }


def google_exchange(code: str, redirect_uri: str) -> dict:
    """Exchange a Google OAuth code for a profile dict."""
    _guard_enabled("google")
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise OAuthDisabledError("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not configured.")

    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    token = token_resp.json().get("access_token")
    if not token:
        raise OAuthDisabledError("Google token exchange failed.")

    info = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    ).json()
    return {
        "provider": "google",
        "provider_id": info.get("sub", ""),
        "username": (info.get("email") or "user").split("@")[0],
        "email": info.get("email", ""),
        "name": info.get("name", ""),
        "avatar_url": info.get("picture", ""),
    }
