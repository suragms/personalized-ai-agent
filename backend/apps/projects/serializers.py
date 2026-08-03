from rest_framework import serializers

from .models import Milestone, ProgressSnapshot, Project
from .services import burndown, delivery_prediction, risk_score, velocity


class ProjectSerializer(serializers.ModelSerializer):
    completion_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "client",
            "description",
            "status",
            "start_date",
            "end_date",
            "backend_pct",
            "frontend_pct",
            "testing_pct",
            "deployment_pct",
            "pending_bugs",
            "completion_pct",
        )
        read_only_fields = ("id", "completion_pct")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["risk_score"] = risk_score(instance)
        data["velocity"] = velocity(instance)
        data["delivery"] = delivery_prediction(instance)
        data["burndown"] = burndown(instance)
        return data


class MilestoneSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Milestone
        fields = ("id", "project", "project_name", "title", "due_date", "status", "completed_at", "created_at")
        read_only_fields = ("id", "created_at")


class ProgressSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressSnapshot
        fields = ("id", "date", "backend_pct", "frontend_pct", "testing_pct", "deployment_pct", "pending_bugs", "risk_score")
