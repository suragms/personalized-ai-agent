"""Intelligence Engine serializers."""
from rest_framework import serializers

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


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            "id",
            "source_type",
            "name",
            "url",
            "state",
            "last_synced_at",
            "last_error",
            "sync_frequency_hours",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DataSnapshotSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = DataSnapshot
        fields = [
            "id",
            "source",
            "source_name",
            "snapshot_date",
            "raw_data",
            "content_hash",
            "metrics",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = [
            "id",
            "insight_type",
            "severity",
            "confidence",
            "title",
            "description",
            "evidence",
            "source_references",
            "recommended_action",
            "status",
            "expires_at",
            "helpful",
            "user_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id",
            "category",
            "severity",
            "title",
            "message",
            "evidence",
            "source_type",
            "action_url",
            "status",
            "read_at",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GoalSerializer(serializers.ModelSerializer):
    related_project_names = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "description",
            "category",
            "target",
            "deadline",
            "status",
            "priority",
            "progress_pct",
            "related_projects",
            "related_project_names",
            "milestones",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_related_project_names(self, obj):
        return [p.name for p in obj.related_projects.all()]


class DecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Decision
        fields = [
            "id",
            "title",
            "context",
            "options",
            "evidence",
            "pros_cons",
            "risks",
            "unknowns",
            "ai_recommendation",
            "ai_reasoning",
            "user_decision",
            "decision_date",
            "status",
            "review_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "report_type",
            "title",
            "period_start",
            "period_end",
            "content",
            "summary",
            "data_sources",
            "data_freshness",
            "metrics",
            "findings",
            "recommendations",
            "confidence",
            "limitations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = [
            "id",
            "dimension",
            "date",
            "score",
            "confidence",
            "metrics",
            "evidence",
            "insights",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DailyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPlan
        fields = [
            "id",
            "date",
            "priorities",
            "important_alerts",
            "upcoming_deadlines",
            "recommended_focus",
            "potential_blockers",
            "tasks",
            "time_blocks",
            "completed_tasks",
            "incomplete_tasks",
            "evening_insights",
            "tomorrow_priorities",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "onboarding_completed",
            "onboarding_step",
            "professional_title",
            "bio",
            "github_url",
            "portfolio_url",
            "linkedin_url",
            "instagram_url",
            "facebook_url",
            "twitter_url",
            "other_urls",
            "timezone",
            "working_hours_start",
            "working_hours_end",
            "working_days",
            "primary_goals",
            "current_priorities",
            "preferred_ai_behavior",
            "notification_preferences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "username", "email", "created_at", "updated_at"]


class IntegrationConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConnection
        fields = [
            "id",
            "platform",
            "status",
            "connected_account",
            "scopes",
            "last_synced_at",
            "last_error",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "access_token", "refresh_token"]
