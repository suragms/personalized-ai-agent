from django.urls import path

from .views import AnalyticsView, SnapshotHistoryView

urlpatterns = [
    path("<str:module>/", AnalyticsView.as_view(), name="analytics-module"),
    path("<str:module>/history/", SnapshotHistoryView.as_view(), name="analytics-history"),
]
