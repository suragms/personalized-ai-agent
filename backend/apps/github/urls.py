from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CommitViewSet,
    IssueViewSet,
    PullRequestViewSet,
    ReleaseViewSet,
    RepositoryViewSet,
    analytics,
    contributions,
    health,
    insights,
    oauth_callback,
    oauth_disconnect,
    oauth_initiate,
    oauth_status,
    sync_now,
    sync_status,
)

router = DefaultRouter()
router.register("repos", RepositoryViewSet, basename="github-repos")
router.register("commits", CommitViewSet, basename="github-commits")
router.register("pull-requests", PullRequestViewSet, basename="github-prs")
router.register("issues", IssueViewSet, basename="github-issues")
router.register("releases", ReleaseViewSet, basename="github-releases")

urlpatterns = [
    # Analytics
    path("analytics/", analytics, name="github-analytics"),
    path("health/", health, name="github-health"),
    path("insights/", insights, name="github-insights"),
    path("contributions/", contributions, name="github-contributions"),
    # OAuth integration
    path("oauth/status/", oauth_status, name="github-oauth-status"),
    path("oauth/initiate/", oauth_initiate, name="github-oauth-initiate"),
    path("oauth/callback/", oauth_callback, name="github-oauth-callback"),
    path("oauth/disconnect/", oauth_disconnect, name="github-oauth-disconnect"),
    # Sync
    path("sync/now/", sync_now, name="github-sync-now"),
    path("sync/status/", sync_status, name="github-sync-status"),
] + router.urls
