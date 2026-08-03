from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationRule
from .serializers import NotificationRuleSerializer, NotificationSerializer
from .services import mark_read, sweep_for, unread_count


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(owner=self.request.user)
        unread_only = self.request.query_params.get("unread")
        if unread_only in ("1", "true"):
            qs = qs.filter(read=False)
        return qs

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = mark_read(request.user)
        return Response({"updated": count})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save(update_fields=["read"])
        return Response(NotificationSerializer(notification).data)


class NotificationRuleViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationRuleSerializer

    def get_queryset(self):
        return NotificationRule.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SweepView(APIView):
    """POST → run the notification sweep now."""

    def post(self, request):
        count = sweep_for(request.user)
        return Response({"created": count})


class UnreadView(APIView):
    def get(self, request):
        return Response({"unread": unread_count(request.user)})
