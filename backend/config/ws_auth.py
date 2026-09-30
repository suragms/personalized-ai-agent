"""JWT authentication for WebSocket handshakes.

Browsers cannot attach an ``Authorization`` header to a WebSocket upgrade
request, so the SPA passes the access token as ``?token=...`` (non-browser
clients may use the ``Authorization: Bearer`` header instead). Tokens are
validated with the same simplejwt authenticator the HTTP layer uses.

An invalid/expired token (or no token) leaves the user anonymous — consumers
reject anonymous connections with close code 4001.
"""
from __future__ import annotations

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger("connectivity")


def _extract_token(scope: dict) -> str | None:
    """Pull the raw access token from the query string or Authorization header."""
    raw_query = scope.get("query_string", b"") or b""
    try:
        query = parse_qs(raw_query.decode("utf-8", errors="ignore"))
    except Exception:  # pragma: no cover - decode is error-safe already
        query = {}
    for key in ("token", "access"):
        values = query.get(key)
        if values and values[0]:
            return values[0]

    for name, value in scope.get("headers", []):
        if name == b"authorization":
            header = value.decode("utf-8", errors="ignore")
            if header.lower().startswith("bearer ") and header[7:].strip():
                return header[7:].strip()
    return None


def authenticate_token(raw_token: str):
    """Validate a raw JWT and return the user, or None if it is not usable."""
    from rest_framework.exceptions import AuthenticationFailed
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

    try:
        auth = JWTAuthentication()
        validated = auth.get_validated_token(raw_token)
        return auth.get_user(validated)
    except (InvalidToken, TokenError, AuthenticationFailed) as exc:
        logger.info("WebSocket JWT rejected: %s", exc)
        return None
    except Exception:  # pragma: no cover - never let auth crash the handshake
        logger.exception("WebSocket JWT authentication failed")
        return None


authenticate_token_async = database_sync_to_async(authenticate_token)


class JWTAuthMiddleware:
    """Set ``scope["user"]`` from the JWT when the handshake carries a token.

    Runs inside ``AuthMiddlewareStack``: session auth populates the user first,
    then an explicitly supplied token wins (invalid token => anonymous).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "websocket":
            token = _extract_token(scope)
            if token:
                user = await authenticate_token_async(token)
                scope["user"] = user if user is not None else AnonymousUser()
        return await self.app(scope, receive, send)
