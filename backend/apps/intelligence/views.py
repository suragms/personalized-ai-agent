"""Intelligence Engine views."""
from datetime import date

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Alert,
    DailyPlan,
    DataSnapshot,
    DataSource,
    Decision,
    Goal,
    Insight,
    IntegrationConnection,
    PerformanceMetric,
    Report,
    UserProfile,
)
from .serializers import (
    AlertSerializer,
    DailyPlanSerializer,
    DataSnapshotSerializer,
    DataSourceSerializer,
    DecisionSerializer,
    GoalSerializer,
    InsightSerializer,
    IntegrationConnectionSerializer,
    PerformanceMetricSerializer,
    ReportSerializer,
    UserProfileSerializer,
)


class DataSourceViewSet(viewsets.ModelViewSet):
    """Manage data sources."""

    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DataSource.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Trigger a sync for this data source."""
        source = self.get_object()
        # TODO: Implement actual sync logic
        source.last_synced_at = timezone.now()
        source.state = "connected"
        source.save()
        return Response({"status": "sync_started"})


class DataSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """View data snapshots."""

    serializer_class = DataSnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DataSnapshot.objects.filter(owner=self.request.user)


class InsightViewSet(viewsets.ModelViewSet):
    """Manage insights."""

    serializer_class = InsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Insight.objects.filter(owner=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        insight_type = self.request.query_params.get("type")
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_helpful(self, request, pk=None):
        """Mark an insight as helpful or not."""
        insight = self.get_object()
        is_helpful = request.data.get("helpful", True)
        insight.helpful = is_helpful
        insight.status = "reviewed"
        insight.save()
        return Response({"status": "updated"})

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        """Dismiss an insight."""
        insight = self.get_object()
        insight.status = "dismissed"
        insight.save()
        return Response({"status": "dismissed"})


class AlertViewSet(viewsets.ModelViewSet):
    """Manage alerts."""

    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Alert.objects.filter(owner=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark alert as read."""
        alert = self.get_object()
        alert.status = "read"
        alert.read_at = timezone.now()
        alert.save()
        return Response({"status": "read"})

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        alert.status = "resolved"
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({"status": "resolved"})


class GoalViewSet(viewsets.ModelViewSet):
    """Manage goals."""

    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Goal.objects.filter(owner=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DecisionViewSet(viewsets.ModelViewSet):
    """Manage decisions."""

    serializer_class = DecisionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Decision.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    """Manage reports."""

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Report.objects.filter(owner=self.request.user)
        report_type = self.request.query_params.get("type")
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PerformanceMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """View performance metrics."""

    serializer_class = PerformanceMetricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PerformanceMetric.objects.filter(owner=self.request.user)
        dimension = self.request.query_params.get("dimension")
        if dimension:
            queryset = queryset.filter(dimension=dimension)
        return queryset


class DailyPlanViewSet(viewsets.ModelViewSet):
    """Manage daily plans."""

    serializer_class = DailyPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyPlan.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Get today's plan."""
        today = date.today()
        plan, created = DailyPlan.objects.get_or_create(
            owner=request.user,
            date=today,
        )
        serializer = self.get_serializer(plan)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """Manage user profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get or update current user's profile."""
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method == "PATCH":
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class IntegrationConnectionViewSet(viewsets.ModelViewSet):
    """Manage integration connections."""

    serializer_class = IntegrationConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IntegrationConnection.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        """Disconnect an integration."""
        connection = self.get_object()
        connection.status = "disconnected"
        connection.access_token = ""
        connection.refresh_token = ""
        connection.save()
        return Response({"status": "disconnected"})
