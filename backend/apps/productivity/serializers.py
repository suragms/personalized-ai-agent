from django.utils import timezone
from rest_framework import serializers

from .models import Briefing, CalendarEvent, FocusSession, Task


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, default=None)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "estimated_hours",
            "completed_at",
            "project",
            "project_name",
            "created_at",
        )
        read_only_fields = ("id", "completed_at", "created_at")

    def update(self, instance, validated_data):
        if validated_data.get("status") == "done" and instance.status != "done":
            validated_data["completed_at"] = timezone.now()
        return super().update(instance, validated_data)


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ("id", "title", "start", "end", "location", "url")
        read_only_fields = ("id",)


class FocusSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FocusSession
        fields = ("id", "task", "started_at", "ended_at", "duration_minutes", "focus_score")
        read_only_fields = ("id",)


class BriefingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Briefing
        fields = ("id", "kind", "date", "content", "data", "provenance", "created_at")
        read_only_fields = ("id", "created_at", "provenance")
