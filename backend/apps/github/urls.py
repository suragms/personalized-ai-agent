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
)

router = DefaultRouter()
router.register("repos", RepositoryViewSet, basename="github-repos")
router.register("commits", CommitViewSet, basename="github-commits")
router.register("pull-requests", PullRequestViewSet, basename="github-prs")
router.register("issues", IssueViewSet, basename="github-issues")
router.register("releases", ReleaseViewSet, basename="github-releases")

urlpatterns = [
    path("analytics/", analytics, name="github-analytics"),
    path("health/", health, name="github-health"),
    path("insights/", insights, name="github-insights"),
    path("contributions/", contributions, name="github-contributions"),
] + router.urls
