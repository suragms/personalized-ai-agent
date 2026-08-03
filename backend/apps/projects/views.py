from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Milestone, Project
from .serializers import MilestoneSerializer, ProgressSnapshotSerializer, ProjectSerializer
from .services import burndown, project_metrics, record_snapshot


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = Project.objects.filter(owner=self.request.user).select_related("owner")
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        record_snapshot(instance)

    @action(detail=True, methods=["post"])
    def snapshot(self, request, pk=None):
        project = self.get_object()
        snap = record_snapshot(project)
        return Response(ProgressSnapshotSerializer(snap).data)

    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        project = self.get_object()
        return Response(project_metrics(project))


class MilestoneViewSet(viewsets.ModelViewSet):
    serializer_class = MilestoneSerializer

    def get_queryset(self):
        return Milestone.objects.filter(project__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


@api_view(["GET"])
def burndown_overview(request):
    """Burndown series for every project (dashboard chart)."""
    projects = Project.objects.filter(owner=request.user)
    return Response(
        [
            {"id": str(p.id), "name": p.name, "series": burndown(p)}
            for p in projects
        ]
    )
