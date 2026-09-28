"""GitHub OAuth and sync views."""
import secrets
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from intelligence.serializers import IntegrationConnectionSerializer

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


@api_view(["GET"])
def analytics(request):
    """Get GitHub analytics."""
    weeks = int(request.query_params.get("weeks", 8))
    return Response(weekly_analytics(request.user, weeks=min(weeks, 26)))


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
    days = int(request.query_params.get("days", 90))
    return Response(contribution_graph(request.user, days=min(days, 365)))


# ── OAuth Integration ──────────────────────────────────────────────────────


@api_view(["GET"])
def oauth_status(request):
    """Get GitHub OAuth connection status."""
    connection = get_connection(request.user)

    if not connection:
        return Response(
            {
                "connected": False,
                "status": "disconnected",
                "account": None,
                "last_synced_at": None,
            }
        )

    return Response(
        {
            "connected": connection.status == "connected",
            "status": connection.status,
            "account": connection.connected_account,
            "last_synced_at": connection.last_synced_at,
            "last_error": connection.last_error,
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
        return Response({"error": "redirect_uri required"}, status=status.HTTP_400_BAD_REQUEST)

    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session[f"github_oauth_state_{state}"] = {
        "redirect_uri": redirect_uri,
        "created_at": str(timezone.now()),
    }

    try:
        auth_url = get_authorization_url(state, redirect_uri)
        return Response({"authorization_url": auth_url, "state": state})

    except GitHubOAuthError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return Response({"error": "code, state, and redirect_uri required"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate state (CSRF protection)
    stored_state = request.session.get(f"github_oauth_state_{state}")
    if not stored_state:
        return Response({"error": "Invalid or expired state"}, status=status.HTTP_400_BAD_REQUEST)

    # Clean up state
    del request.session[f"github_oauth_state_{state}"]

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
            return Response({"error": "Connection verification failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "success": True,
                "connection": IntegrationConnectionSerializer(connection).data,
            }
        )

    except GitHubOAuthError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({"error": "GitHub not connected"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sync_service = GitHubSyncService(request.user)
        results = sync_service.sync_all()

        return Response(results)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def sync_status(request):
    """Get sync status."""
    from intelligence.models import DataSource

    try:
        source = DataSource.objects.get(owner=request.user, source_type="github")
        return Response(
            {
                "state": source.state,
                "last_synced_at": source.last_synced_at,
                "last_error": source.last_error,
                "sync_frequency_hours": source.sync_frequency_hours,
            }
        )
    except DataSource.DoesNotExist:
        return Response({"state": "not_configured", "last_synced_at": None})
