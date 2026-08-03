from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "id",
            "period",
            "title",
            "period_start",
            "period_end",
            "content",
            "html",
            "data",
            "generated_by",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ReportGenerateSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=Report.PERIOD_CHOICES, default="daily")
