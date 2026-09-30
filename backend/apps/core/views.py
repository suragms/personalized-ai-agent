"""Unified system health endpoint for probes and the dashboard.

Reports real service state only: every status is the result of an actual
check (database connection, Redis ping, Celery worker ping, OAuth/AI
configuration). No credentials are ever included in the response.

HTTP semantics:
- ``200`` when the platform is usable (``ok`` or ``degraded``)
- ``503`` only when the database itself is unreachable (``error``)
"""
import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.connectivity import (
    ConnectivityStatus,
    check_ai_provider_config,
    check_celery,
    check_database,
    check_oauth_config,
    check_redis,
    normalize_status,
)

logger = logging.getLogger("connectivity")

# Statuses that count as healthy for the overall roll-up.
_HEALTHY = {
    ConnectivityStatus.CONNECTED.value,
    ConnectivityStatus.RUNNING.value,
    ConnectivityStatus.CONFIGURED.value,
}


def _user_integrations(user):
    """Per-user integration state from the database (no external calls)."""
    from intelligence.models import IntegrationConnection

    integrations = {}
    rows = IntegrationConnection.objects.filter(owner=user)
    known = {row.platform: row for row in rows}
    for platform in ("github", "linkedin"):
        row = known.get(platform)
        if row is None:
            integrations[platform] = {"status": ConnectivityStatus.NOT_CONFIGURED.value}
        else:
            integrations[platform] = {
                "status": normalize_status(row.status).value,
                "last_synced_at": row.last_synced_at.isoformat() if row.last_synced_at else None,
                "error_code": row.error_code or None,
                "retryable": bool(row.retryable),
            }
    return integrations


class HealthView(APIView):
    """GET /api/health/ — safe, credential-free system health report."""

    permission_classes = [AllowAny]
    throttle_classes = []  # probes must never be rate-limited into failure

    def get(self, request):
        services = {
            "database": check_database(),
            "redis": check_redis(),
            "celery": check_celery(),
            "ai_provider": check_ai_provider_config(),
            "github": check_oauth_config("github"),
            "google": check_oauth_config("google"),
        }

        payload_services = {name: check.as_dict() for name, check in services.items()}

        integrations = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            try:
                integrations = _user_integrations(request.user)
            except Exception as exc:  # pragma: no cover - DB read failures only
                logger.warning("Health integrations lookup failed: %s", exc)
                integrations = {"error": {"status": ConnectivityStatus.DATA_UNAVAILABLE.value}}

        # Overall roll-up: database failure is critical; anything else not
        # healthy is a degradation.
        if services["database"].status != ConnectivityStatus.CONNECTED:
            overall = "error"
        else:
            degraded = any(
                check.status.value not in _HEALTHY
                for check in services.values()
            )
            if integrations:
                degraded = degraded or any(
                    entry["status"] not in _HEALTHY for entry in integrations.values()
                )
            overall = "degraded" if degraded else "ok"

        body = {
            "status": overall,
            "services": payload_services,
        }
        if integrations is not None:
            body["integrations"] = integrations

        return Response(body, status=503 if overall == "error" else 200)
