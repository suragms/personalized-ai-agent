from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisView,
    LinkedInProfileView,
    PostIdeaViewSet,
    PostingTimeView,
    ScoreHistoryView,
)

router = DefaultRouter()
router.register("posts", PostIdeaViewSet, basename="linkedin-posts")

urlpatterns = [
    path("profile/", LinkedInProfileView.as_view(), name="linkedin-profile"),
    path("analyze/", AnalysisView.as_view(), name="linkedin-analyze"),
    path("posting-time/", PostingTimeView.as_view(), name="linkedin-posting-time"),
    path("score-history/", ScoreHistoryView.as_view(), name="linkedin-score-history"),
] + router.urls
