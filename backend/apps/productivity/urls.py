from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BriefingViewSet,
    CalendarEventViewSet,
    FocusSessionViewSet,
    TaskViewSet,
    briefing_generate,
    score,
)

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")
router.register("calendar", CalendarEventViewSet, basename="calendar")
router.register("focus-sessions", FocusSessionViewSet, basename="focus-sessions")
router.register("briefings", BriefingViewSet, basename="briefings")

urlpatterns = [
    path("briefings/generate/", briefing_generate, name="briefing-generate"),
    path("productivity/score/", score, name="productivity-score"),
] + router.urls
