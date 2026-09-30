"""GitHub OAuth and sync views."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from intelligence.serializers import IntegrationConnectionSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.connectivity import ConnectivityStatus, normalize_status, sanitize_error_message

from .models import Commit, GithubInsight, Issue, PullRequest, Release, Repository
from .oauth import (
    GitHubOAuthError,
    create_or_update_connection,
    disconnect,
    exchange_code,
    get_authorization_url,
    get_connection,
    verify_connection,
)
from .serializers import (
    CommitSerializer,
    GithubInsightSerializer,
    IssueSerializer,
    PullRequestSerializer,
    ReleaseSerializer,
    RepositorySerializer,
)
from .services import at_risk_repositories, contribution_graph, weekly_analytics
from .sync import GitHubSyncService


class RepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repository.objects.filter(owner=self.request.user).select_related("owner")


class CommitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Commit.objects.filter(owner=self.request.user).select_related("repository")
        repo = self.request.query_params.get("repository")
        if repo:
            qs = qs.filter(repository__full_name=repo)
        return qs


class PullRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PullRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PullRequest.objects.filter(owner=self.request.user).select_related("repository")
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        return qs


class IssueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Issue.objects.filter(owner=self.request.user).select_related("repository")
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        return qs


class ReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReleaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Release.objects.filter(owner=self.request.user).select_related("repository")


def _int_param(request, name: str, default: int, maximum: int) -> int:
    """Parse an integer query param safely (never raises 500)."""
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(value, maximum))


@api_view(["GET"])
def analytics(request):
    """Get GitHub analytics."""
    weeks = _int_param(request, "weeks", 8, 26)
    return Response(weekly_analytics(request.user, weeks=weeks))


@api_view(["GET"])
def health(request):
    """Get repository health status."""
    return Response({"repositories": at_risk_repositories(request.user)})


@api_view(["GET"])
def insights(request):
    """Get GitHub insights."""
    data = list(GithubInsight.objects.filter(owner=request.user)[:20])
    return Response(GithubInsightSerializer(data, many=True).data)


@api_view(["GET"])
def contributions(request):
    """Get contribution graph data."""
    days = _int_param(request, "days", 90, 365)
    return Response(contribution_graph(request.user, days=days))


# ── OAuth Integration ──────────────────────────────────────────────────────

# OAuth `state` values are single-use and short-lived (CSRF protection).
OAUTH_STATE_MAX_AGE = timedelta(minutes=10)


def _oauth_configured() -> bool:
    return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)


@api_view(["GET"])
def oauth_status(request):
    """Get GitHub OAuth connection status.

    Status values come from the unified connectivity vocabulary and are
    derived from the stored connection row (never guessed).
    """
    connection = None
    try:
        from intelligence.models import IntegrationConnection

        connection = IntegrationConnection.objects.filter(owner=request.user, platform="github").first()
    except Exception:  # pragma: no cover - DB failures handled by health endpoint
        connection = None

    if connection is None:
        connection_status = ConnectivityStatus.NOT_CONFIGURED if not _oauth_configured() else ConnectivityStatus.DISCONNECTED
        return Response(
            {
                "connected": False,
                "status": connection_status.value,
                "configured": _oauth_configured(),
                "account": None,
                "last_synced_at": None,
                "last_error": None,
                "error_code": None,
                "retryable": False,
                "scopes": [],
            }
        )

    normalized = normalize_status(connection.status)
    return Response(
        {
            "connected": normalized == ConnectivityStatus.CONNECTED,
            "status": normalized.value,
            "configured": _oauth_configured(),
            "account": connection.connected_account,
            "last_synced_at": connection.last_synced_at,
            "last_error": connection.last_error or None,
            "error_code": connection.error_code or None,
            "retryable": bool(connection.retryable),
            "scopes": connection.scopes,
        }
    )


@api_view(["POST"])
def oauth_initiate(request):
    """Initiate GitHub OAuth flow.

    Returns authorization URL for frontend to redirect to.
    """
    redirect_uri = request.data.get("redirect_uri")
    if not redirect_uri:
        return Response(
            {"detail": "redirect_uri is required.", "code": "validation_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not _oauth_configured():
        return Response(
            {
                "detail": "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
                "code": "not_configured",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate and store state for CSRF protection (single use, expires).
    state = secrets.token_urlsafe(32)
    request.session[f"github_oauth_state_{state}"] = {
        "redirect_uri": redirect_uri,
        "created_at": timezone.now().timestamp(),
    }

    try:
        auth_url = get_authorization_url(state, redirect_uri)
        return Response({"authorization_url": auth_url, "state": state})

    except GitHubOAuthError as e:
        return Response(
            {"detail": sanitize_error_message(e), "code": "not_configured"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
def oauth_callback(request):
    """Handle GitHub OAuth callback.

    Frontend receives code and state from GitHub, sends them here.
    Backend exchanges code for token and creates connection.
    """
    code = request.data.get("code")
    state = request.data.get("state")
    redirect_uri = request.data.get("redirect_uri")

    if not all([code, state, redirect_uri]):
        return Response(
            {"detail": "code, state, and redirect_uri are required.", "code": "validation_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate state (CSRF protection): must exist, be fresh, and single-use.
    state_key = f"github_oauth_state_{state}"
    stored_state = request.session.get(state_key)
    if not stored_state:
        return Response(
            {"detail": "Invalid or expired state. Please restart the connection flow.", "code": "invalid_state"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_at = stored_state.get("created_at")
    try:
        age_seconds = timezone.now().timestamp() - float(created_at)
    except (TypeError, ValueError):
        age_seconds = None
    if age_seconds is None or age_seconds > OAUTH_STATE_MAX_AGE.total_seconds():
        del request.session[state_key]
        return Response(
            {"detail": "OAuth state expired. Please restart the connection flow.", "code": "invalid_state"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Clean up state (single use)
    del request.session[state_key]

    # Prefer the redirect_uri stored at initiate time over a client-supplied one.
    redirect_uri = stored_state.get("redirect_uri") or redirect_uri

    if not _oauth_configured():
        return Response(
            {
                "detail": "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
                "code": "not_configured",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Exchange code for token
        token_data = exchange_code(code, redirect_uri)

        # Create/update connection
        connection = create_or_update_connection(
            user=request.user,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
        )

        # Verify connection works
        if not verify_connection(connection):
            return Response(
                {"detail": "GitHub accepted the code but the connection could not be verified.", "code": "verification_failed"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "success": True,
                "connection": IntegrationConnectionSerializer(connection).data,
            }
        )

    except GitHubOAuthError as e:
        message = str(e)
        code_name = "not_configured" if "not configured" in message.lower() else "oauth_failed"
        return Response(
            {"detail": sanitize_error_message(e), "code": code_name},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
def oauth_disconnect(request):
    """Disconnect GitHub integration."""
    disconnect(request.user)
    return Response({"success": True, "message": "GitHub disconnected"})


@api_view(["POST"])
def sync_now(request):
    """Trigger immediate GitHub sync."""
    connection = get_connection(request.user)

    if not connection:
        return Response(
            {"detail": "GitHub is not connected.", "code": "not_connected"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        sync_service = GitHubSyncService(request.user)
        results = sync_service.sync_all()
        return Response(results)
    except Exception as e:
        return Response(
            {"detail": f"GitHub sync failed: {sanitize_error_message(e)}", "code": "sync_failed"},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["GET"])
def sync_status(request):
    """Get sync status."""
    from intelligence.models import DataSource

    try:
        source = DataSource.objects.get(owner=request.user, source_type="github")
        return Response(
            {
                "state": normalize_status(source.state).value,
                "last_synced_at": source.last_synced_at,
                "last_error": source.last_error or None,
                "sync_frequency_hours": source.sync_frequency_hours,
            }
        )
    except DataSource.DoesNotExist:
        return Response(
            {
                "state": ConnectivityStatus.NOT_CONFIGURED.value,
                "last_synced_at": None,
                "last_error": None,
                "sync_frequency_hours": None,
            }
        )
