"""Intelligence Engine URL routing."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.connectivity_views import DataHealthView

from .views import (
    AlertViewSet,
    DailyPlanViewSet,
    DataSnapshotViewSet,
    DataSourceViewSet,
    DecisionViewSet,
    GoalViewSet,
    InsightViewSet,
    IntegrationConnectionViewSet,
    IntelligenceSummaryView,
    PerformanceMetricViewSet,
    ReportViewSet,
    UserProfileViewSet,
)

router = DefaultRouter()
router.register(r"data-sources", DataSourceViewSet, basename="datasource")
router.register(r"data-snapshots", DataSnapshotViewSet, basename="datasnapshot")
router.register(r"insights", InsightViewSet, basename="insight")
router.register(r"alerts", AlertViewSet, basename="alert")
router.register(r"goals", GoalViewSet, basename="goal")
router.register(r"decisions", DecisionViewSet, basename="decision")
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"performance", PerformanceMetricViewSet, basename="performance")
router.register(r"daily-plans", DailyPlanViewSet, basename="dailyplan")
router.register(r"profile", UserProfileViewSet, basename="profile")
router.register(r"integrations", IntegrationConnectionViewSet, basename="integration")

urlpatterns = [
    path("data-health/", DataHealthView.as_view(), name="data-health"),
    path("summary/", IntelligenceSummaryView.as_view(), name="intelligence-summary"),
    path("", include(router.urls)),
]
