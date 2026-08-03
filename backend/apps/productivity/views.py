from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Briefing, CalendarEvent, FocusSession, Task
from .serializers import BriefingSerializer, CalendarEventSerializer, FocusSessionSerializer, TaskSerializer
from .services import generate_eod, generate_morning, productivity_score


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = Task.objects.filter(owner=self.request.user).select_related("project")
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        return CalendarEvent.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FocusSessionViewSet(viewsets.ModelViewSet):
    serializer_class = FocusSessionSerializer

    def get_queryset(self):
        return FocusSession.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BriefingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BriefingSerializer

    def get_queryset(self):
        qs = Briefing.objects.filter(owner=self.request.user)
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs


@api_view(["POST"])
def briefing_generate(request):
    kind = request.data.get("kind", "morning")
    if kind == "eod":
        briefing = generate_eod(request.user)
    else:
        briefing = generate_morning(request.user)
    return Response(BriefingSerializer(briefing).data)


@api_view(["GET"])
def score(request):
    from django.utils import timezone

    day = timezone.localdate()
    return Response({"date": day.isoformat(), "productivity_score": productivity_score(request.user, day)})
