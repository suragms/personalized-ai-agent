"""Unified connectivity vocabulary, status normalization, and error mapping.

Canonical status names (required vocabulary):

    CONNECTED, CONNECTING, DISCONNECTED, NOT_CONFIGURED, AUTHENTICATION_FAILED,
    PERMISSION_DENIED, RATE_LIMITED, TIMEOUT, NETWORK_ERROR, API_ERROR,
    SERVICE_UNAVAILABLE, INVALID_CREDENTIALS, STALE, NO_DATA, DATA_UNAVAILABLE,
    RUNNING, CONFIGURED, UNKNOWN_ERROR

Wire values are lowercase snake_case so that existing API consumers, legacy
rows, and the health endpoint JSON stay consistent. The enum accepts any
case plus legacy aliases (``error``, ``syncing``, ``expired``, ...) so old
database rows never raise.

Nothing in this module performs I/O except the explicit ``check_*`` helpers,
each of which is bounded by a short timeout and returns a status instead of
raising.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("connectivity")


class ConnectivityStatus(StrEnum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    NOT_CONFIGURED = "not_configured"
    AUTHENTICATION_FAILED = "authentication_failed"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_CREDENTIALS = "invalid_credentials"
    STALE = "stale"
    NO_DATA = "no_data"
    DATA_UNAVAILABLE = "data_unavailable"
    RUNNING = "running"
    CONFIGURED = "configured"
    UNKNOWN_ERROR = "unknown_error"

    @classmethod
    def _missing_(cls, value: object):
        # Accept any case and legacy values written by older code.
        if isinstance(value, str):
            lowered = value.strip().lower()
            for member in cls:
                if member.value == lowered:
                    return member
            canonical = _LEGACY_ALIASES.get(lowered)
            if canonical is not None:
                return cls(canonical)
        return None


# Legacy / alternate spellings accepted on read (never written).
_LEGACY_ALIASES: dict[str, str] = {
    "ok": "connected",
    "active": "connected",
    "authorized": "connected",
    "healthy": "connected",
    "success": "connected",
    "running": "running",
    "syncing": "connecting",
    "pending": "connecting",
    "expired": "authentication_failed",
    "revoked": "disconnected",
    "unauthorized": "authentication_failed",
    "error": "api_error",
    "failed": "api_error",
    "unavailable": "service_unavailable",
    "offline": "disconnected",
    "disabled": "disconnected",
    "not_configured": "not_configured",
    "unconfigured": "not_configured",
    "missing": "not_configured",
}


def normalize_status(value: Any, default: ConnectivityStatus = ConnectivityStatus.UNKNOWN_ERROR) -> ConnectivityStatus:
    """Safely coerce a stored/unknown value into a ConnectivityStatus."""
    if isinstance(value, ConnectivityStatus):
        return value
    if value is None or value == "":
        return default
    try:
        return ConnectivityStatus(value)
    except ValueError:
        return default


@dataclass
class IntegrationHealth:
    provider: str
    status: ConnectivityStatus
    last_successful_sync: str | None = None
    last_attempt: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool = False
    data_freshness: str = "no_data"

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "last_successful_sync": self.last_successful_sync,
            "last_attempt": self.last_attempt,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retryable": self.retryable,
            "data_freshness": self.data_freshness,
        }


@dataclass
class ServiceCheck:
    """Result of a single infrastructure/service probe."""

    status: ConnectivityStatus
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.detail:
            payload["detail"] = self.detail
        payload.update(self.extra)
        return payload


# ── Error message sanitisation ────────────────────────────────────────────

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)\b\s*[:=]\s*\S+"),
]

_MAX_ERROR_LEN = 400


def sanitize_error_message(message: Any) -> str:
    """Redact credential-looking material and bound the length of an error."""
    text = str(message)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    if len(text) > _MAX_ERROR_LEN:
        text = text[: _MAX_ERROR_LEN - 3] + "..."
    return text


# ── Exception normalisation ───────────────────────────────────────────────

def normalize_exception(exc: Exception) -> tuple[ConnectivityStatus, bool, str]:
    """Map an arbitrary exception to (status, retryable, error_code).

    Codes are lowercase snake_case and stable; they are safe to persist on
    connection rows and return through API responses (after sanitisation).
    """
    exc_str = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in exc_str or "timed out" in exc_str:
        return ConnectivityStatus.TIMEOUT, True, "timeout"
    if "rate limit" in exc_str or "429" in exc_str:
        return ConnectivityStatus.RATE_LIMITED, True, "rate_limited"
    if "unauthorized" in exc_str or "invalid_grant" in exc_str or "invalid api key" in exc_str or "401" in exc_str:
        return ConnectivityStatus.AUTHENTICATION_FAILED, False, "auth_failed"
    if "forbidden" in exc_str or "permission" in exc_str or "403" in exc_str:
        return ConnectivityStatus.PERMISSION_DENIED, False, "permission_denied"
    if ("model" in exc_str and ("not found" in exc_str or "does not exist" in exc_str or "404" in exc_str)) or "model_not_found" in exc_str:
        return ConnectivityStatus.API_ERROR, False, "model_not_found"
    if "connection" in exc_str or "network" in exc_str or "resolve" in exc_str or "name or service" in exc_str:
        return ConnectivityStatus.NETWORK_ERROR, True, "network_error"
    if "500" in exc_str or "502" in exc_str or "503" in exc_str or "504" in exc_str or "unavailable" in exc_str:
        return ConnectivityStatus.SERVICE_UNAVAILABLE, True, "service_unavailable"
    return ConnectivityStatus.UNKNOWN_ERROR, False, "unknown_error"


# ── AI provider error codes (stable, provider-facing vocabulary) ──────────

AI_PROVIDER_NOT_CONFIGURED = "AI_PROVIDER_NOT_CONFIGURED"
AI_PROVIDER_AUTH_FAILED = "AI_PROVIDER_AUTH_FAILED"
AI_PROVIDER_TIMEOUT = "AI_PROVIDER_TIMEOUT"
AI_PROVIDER_RATE_LIMITED = "AI_PROVIDER_RATE_LIMITED"
AI_PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
AI_MODEL_NOT_FOUND = "AI_MODEL_NOT_FOUND"
AI_PROVIDER_UNKNOWN_ERROR = "AI_PROVIDER_UNKNOWN_ERROR"


def ai_error_code(status: ConnectivityStatus | str, code: str | None = None) -> str:
    """Map a connectivity status/code onto the AI provider error vocabulary."""
    if code == "model_not_found":
        return AI_MODEL_NOT_FOUND
    status = normalize_status(status)
    return {
        ConnectivityStatus.NOT_CONFIGURED: AI_PROVIDER_NOT_CONFIGURED,
        ConnectivityStatus.AUTHENTICATION_FAILED: AI_PROVIDER_AUTH_FAILED,
        ConnectivityStatus.INVALID_CREDENTIALS: AI_PROVIDER_AUTH_FAILED,
        ConnectivityStatus.PERMISSION_DENIED: AI_PROVIDER_AUTH_FAILED,
        ConnectivityStatus.TIMEOUT: AI_PROVIDER_TIMEOUT,
        ConnectivityStatus.RATE_LIMITED: AI_PROVIDER_RATE_LIMITED,
        ConnectivityStatus.NETWORK_ERROR: AI_PROVIDER_UNAVAILABLE,
        ConnectivityStatus.SERVICE_UNAVAILABLE: AI_PROVIDER_UNAVAILABLE,
        ConnectivityStatus.API_ERROR: AI_PROVIDER_UNAVAILABLE,
    }.get(status, AI_PROVIDER_UNKNOWN_ERROR)


# ── Service probes (each bounded by a timeout, never raises) ──────────────

def check_database() -> ServiceCheck:
    """Verify the default database connection is usable (bounded by the
    ``connect_timeout`` database option)."""
    from django.db import connection
    from django.db.utils import Error as DjangoDBError

    try:
        connection.ensure_connection()
        return ServiceCheck(status=ConnectivityStatus.CONNECTED, extra={"vendor": connection.vendor})
    except DjangoDBError as exc:
        return ServiceCheck(status=ConnectivityStatus.NETWORK_ERROR, detail=sanitize_error_message(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Database health check failed: %s", exc)
        return ServiceCheck(status=ConnectivityStatus.UNKNOWN_ERROR, detail=sanitize_error_message(exc))


def check_redis(url: str | None = None, timeout: float = 1.5) -> ServiceCheck:
    """Ping the Redis instance used by Celery / channels."""
    try:
        import redis
    except ImportError:  # pragma: no cover - dependency always present
        return ServiceCheck(status=ConnectivityStatus.NOT_CONFIGURED, detail="redis client not installed")

    from django.conf import settings

    target = url or getattr(settings, "REDIS_URL", None)
    if not target:
        return ServiceCheck(status=ConnectivityStatus.NOT_CONFIGURED)
    try:
        client = redis.Redis.from_url(target, socket_connect_timeout=timeout, socket_timeout=timeout)
        client.ping()
        return ServiceCheck(status=ConnectivityStatus.CONNECTED)
    except Exception as exc:
        status, _, code = normalize_exception(exc)
        if "auth" in str(exc).lower():
            status = ConnectivityStatus.AUTHENTICATION_FAILED
        return ServiceCheck(status=status, detail=sanitize_error_message(exc), extra={"error_code": code})


def check_celery(timeout: float = 1.0) -> ServiceCheck:
    """Report Celery worker availability through the broker."""
    from django.conf import settings

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return ServiceCheck(status=ConnectivityStatus.RUNNING, extra={"mode": "eager"})

    try:
        from config.celery import app as celery_app

        replies = celery_app.control.ping(timeout=timeout)
        if replies:
            workers = sorted({node for reply in replies for node in reply})
            return ServiceCheck(status=ConnectivityStatus.RUNNING, extra={"workers": workers, "worker_count": len(workers)})
        return ServiceCheck(status=ConnectivityStatus.DISCONNECTED, detail="No Celery workers responded.")
    except Exception as exc:
        status, _, code = normalize_exception(exc)
        return ServiceCheck(status=status, detail=sanitize_error_message(exc), extra={"error_code": code})


def check_ai_provider_config() -> ServiceCheck:
    """Cheap, offline check of the active AI provider configuration."""
    from django.conf import settings

    provider_name = (getattr(settings, "AI_PROVIDER", "") or "mock").strip().lower()
    if provider_name == "mock":
        return ServiceCheck(
            status=ConnectivityStatus.CONNECTED,
            extra={"provider": provider_name, "mode": "mock"},
        )

    key_settings = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "grok": "GROK_API_KEY",
        "getunikey": "GETUNIKEY_API_KEY",
        "opencode": "OPENCODE_API_KEY",
        "ollama": "OLLAMA_BASE_URL",
    }
    required = key_settings.get(provider_name)
    if required and not getattr(settings, required, ""):
        return ServiceCheck(
            status=ConnectivityStatus.NOT_CONFIGURED,
            extra={"provider": provider_name, "mode": "real", "missing": required},
        )
    return ServiceCheck(
        status=ConnectivityStatus.CONFIGURED,
        extra={"provider": provider_name, "mode": "real"},
    )


def check_oauth_config(provider: str) -> ServiceCheck:
    """Report whether OAuth credentials are present (never reveals values).

    ALLOW_OAUTH only gates *sign-in* OAuth (accounts.oauth). GitHub's data
    connection flow is gated purely on client id/secret presence, so `status`
    below reflects credential presence, while `sign_in_oauth` reports the
    ALLOW_OAUTH switch separately (documented distinction).
    """
    from django.conf import settings

    if provider == "github":
        configured = bool(getattr(settings, "GITHUB_CLIENT_ID", "") and getattr(settings, "GITHUB_CLIENT_SECRET", ""))
    elif provider == "google":
        configured = bool(getattr(settings, "GOOGLE_CLIENT_ID", "") and getattr(settings, "GOOGLE_CLIENT_SECRET", ""))
    else:
        configured = False

    extra = {
        "provider": provider,
        "sign_in_oauth": "enabled" if getattr(settings, "ALLOW_OAUTH", False) else "disabled",
    }
    if configured:
        return ServiceCheck(status=ConnectivityStatus.CONFIGURED, extra=extra)
    return ServiceCheck(status=ConnectivityStatus.NOT_CONFIGURED, extra=extra)
