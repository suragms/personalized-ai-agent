"""Per-user integration & AI provider health (data health) endpoint."""
from datetime import timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .connectivity import ConnectivityStatus, IntegrationHealth, normalize_status

FRESH_WINDOW = timedelta(hours=24)

# Platforms with a real integration surface in this application. Rows are
# always reported; platforms without a row are reported as NOT_CONFIGURED so
# the dashboard never shows an empty (or invented) status.
KNOWN_PLATFORMS = ("github", "linkedin")


def _freshness(last_synced_at) -> str:
    if last_synced_at is None:
        return "no_data"
    if timezone.now() - last_synced_at <= FRESH_WINDOW:
        return "fresh"
    return "stale"


def _integration_health(user):
    from intelligence.models import IntegrationConnection

    rows = {row.platform: row for row in IntegrationConnection.objects.filter(owner=user)}
    health = []
    for platform in KNOWN_PLATFORMS:
        row = rows.get(platform)
        if row is None:
            health.append(
                IntegrationHealth(
                    provider=platform,
                    status=ConnectivityStatus.NOT_CONFIGURED,
                    data_freshness="no_data",
                ).as_dict()
            )
            continue
        health.append(
            IntegrationHealth(
                provider=platform,
                status=normalize_status(row.status),
                last_successful_sync=row.last_synced_at.isoformat() if row.last_synced_at else None,
                last_attempt=row.last_synced_at.isoformat() if row.last_synced_at else None,
                error_code=row.error_code or None,
                error_message=row.last_error or None,
                retryable=bool(row.retryable),
                data_freshness=_freshness(row.last_synced_at),
            ).as_dict()
        )
    for platform, row in rows.items():
        if platform in KNOWN_PLATFORMS:
            continue
        health.append(
            IntegrationHealth(
                provider=platform,
                status=normalize_status(row.status),
                last_successful_sync=row.last_synced_at.isoformat() if row.last_synced_at else None,
                last_attempt=row.last_synced_at.isoformat() if row.last_synced_at else None,
                error_code=row.error_code or None,
                error_message=row.last_error or None,
                retryable=bool(row.retryable),
                data_freshness=_freshness(row.last_synced_at),
            ).as_dict()
        )
    return health


def _provider_health(user):
    from ai.models import ProviderConnection

    health = []
    for prov in ProviderConnection.objects.filter(owner=user):
        tested = prov.last_tested_at
        health.append(
            IntegrationHealth(
                provider=prov.provider_id,
                status=normalize_status(prov.status),
                last_successful_sync=tested.isoformat() if tested and normalize_status(prov.status) == ConnectivityStatus.CONNECTED else None,
                last_attempt=tested.isoformat() if tested else None,
                error_code=prov.last_error_code or None,
                error_message=prov.last_error_message or None,
                retryable=bool(prov.retryable),
                data_freshness=_freshness(tested) if tested else "no_data",
            ).as_dict()
        )
    return health


class DataHealthView(APIView):
    """GET /api/intelligence/data-health/

    Reports per-user integration and AI provider connectivity derived from
    stored connection state (written by the code paths that actually talk to
    those services). Never returns credentials.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = _integration_health(request.user) + _provider_health(request.user)
        return Response({"count": len(results), "results": results})
