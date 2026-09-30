"""Intelligence Engine views."""
from datetime import date, timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .services import IntelligenceService, ReportService


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
        """Trigger a real sync for this data source.

        GitHub sources run the full fetch → snapshot → insight pipeline.
        Sources without a live integration report an honest error instead of
        pretending a sync happened.
        """
        source = self.get_object()

        if source.source_type != "github":
            return Response(
                {"status": "error", "code": "sync_unsupported", "detail": f"No live integration for '{source.source_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from github.sync import GitHubSyncService

        try:
            results = GitHubSyncService(request.user).sync_all()
        except ValueError as exc:
            return Response(
                {"status": "error", "code": "not_connected", "detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if results.get("status") == "error":
            return Response(
                {"status": "error", "code": "sync_failed", "detail": results.get("errors", ["unknown"])},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"status": "sync_complete", "results": results})


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
        if status_filter == "active":
            # "active" = still actionable (not dismissed/completed/expired)
            queryset = queryset.exclude(status__in=("dismissed", "completed", "expired"))
        elif status_filter:
            queryset = queryset.filter(status=status_filter)
        insight_type = self.request.query_params.get("type")
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Run the Insight Engine for the current user (synchronous, idempotent)."""
        from .engine import InsightEngine

        summary = InsightEngine(request.user).run()
        return Response(summary)

    @action(detail=True, methods=["post"])
    def convert_to_task(self, request, pk=None):
        """Explicitly turn a recommendation into a task (deduplicated)."""
        from .engine import InsightEngine

        insight = self.get_object()
        task = InsightEngine(request.user).convert_to_task(insight)
        if task is None:
            return Response(
                {"status": "error", "code": "not_convertible", "detail": "No actionable recommendation on this insight."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from productivity.serializers import TaskSerializer

        return Response({"status": "ok", "task": TaskSerializer(task).data})

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

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate a report from real data; refuses to fabricate empty ones.

        Body: {report_type?, period_start?, period_end?}. Defaults to a daily
        intelligence report covering yesterday→today. When there is no data to
        analyze the response says so and nothing is persisted.
        """
        today = date.today()
        report_type = request.data.get("report_type", "daily_intelligence")
        try:
            period_start = date.fromisoformat(request.data["period_start"]) if request.data.get("period_start") else today - timedelta(days=1)
            period_end = date.fromisoformat(request.data["period_end"]) if request.data.get("period_end") else today
        except ValueError:
            return Response(
                {"status": "error", "code": "invalid_period", "detail": "Dates must be ISO (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = ReportService.generate_report(request.user, report_type, period_start, period_end)
        if result["insufficient_data"]:
            return Response(
                {"insufficient_data": True, "report": None, "message": result["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"insufficient_data": False, "report": ReportSerializer(result["report"]).data, "message": result["message"]}
        )


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

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Build today's morning plan from current insights/alerts/tasks/goals."""
        from .daily import generate_morning_plan

        raw = request.data.get("date")
        try:
            target = date.fromisoformat(raw) if raw else None
        except ValueError:
            return Response(
                {"status": "error", "code": "invalid_date", "detail": "Date must be ISO (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan = generate_morning_plan(request.user, target)
        return Response(self.get_serializer(plan).data)


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


class IntelligenceSummaryView(APIView):
    """Dashboard summary: counts and data health in one authenticated call."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        def count(queryset):
            return queryset.count()

        insights = Insight.objects.filter(owner=user)
        alerts = Alert.objects.filter(owner=user)
        from productivity.models import Task

        tasks = Task.objects.filter(owner=user)
        goals = Goal.objects.filter(owner=user, status="active")
        today = timezone.now().date()
        overdue_goals = [g for g in goals if g.deadline and g.deadline < today and g.progress_pct < 100]

        return Response(
            {
                "insights": {
                    "total": count(insights),
                    "new": count(insights.filter(status="new")),
                    "reviewed": count(insights.filter(status="reviewed")),
                    "expired": count(insights.filter(status="expired")),
                    "critical": count(insights.filter(severity="critical")),
                    "high": count(insights.filter(severity="high")),
                },
                "alerts": {
                    "total": count(alerts),
                    "active": count(alerts.filter(status="active")),
                },
                "tasks": {
                    "open": count(tasks.exclude(status="done")),
                    "done_today": count(
                        tasks.filter(status="done", completed_at__date=today)
                    ),
                },
                "goals": {"active": count(goals), "overdue": len(overdue_goals)},
                "data": IntelligenceService.get_data_health(user),
                "generated_at": timezone.now().isoformat(),
            }
        )
