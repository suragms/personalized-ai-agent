"""Admin interface for intelligence models."""
from django.contrib import admin

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


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ["source_type", "name", "owner", "state", "last_synced_at"]
    list_filter = ["source_type", "state"]
    search_fields = ["name", "url", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DataSnapshot)
class DataSnapshotAdmin(admin.ModelAdmin):
    list_display = ["source", "snapshot_date", "owner"]
    list_filter = ["source__source_type"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ["title", "insight_type", "severity", "confidence", "status", "owner", "created_at"]
    list_filter = ["insight_type", "severity", "confidence", "status"]
    search_fields = ["title", "description", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "severity", "status", "owner", "created_at"]
    list_filter = ["category", "severity", "status"]
    search_fields = ["title", "message", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "priority", "progress_pct", "owner", "deadline"]
    list_filter = ["category", "status", "priority"]
    search_fields = ["title", "description", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "decision_date", "owner", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "context", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["title", "report_type", "period_start", "period_end", "confidence", "owner", "created_at"]
    list_filter = ["report_type", "confidence"]
    search_fields = ["title", "summary", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ["dimension", "date", "score", "confidence", "owner"]
    list_filter = ["dimension", "confidence"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ["date", "owner", "reviewed_at", "created_at"]
    search_fields = ["owner__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "professional_title", "onboarding_completed", "timezone"]
    list_filter = ["onboarding_completed"]
    search_fields = ["user__username", "professional_title"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(IntegrationConnection)
class IntegrationConnectionAdmin(admin.ModelAdmin):
    list_display = ["platform", "owner", "status", "connected_account", "last_synced_at"]
    list_filter = ["platform", "status"]
    search_fields = ["owner__username", "connected_account"]
    readonly_fields = ["created_at", "updated_at"]
    # Never expose decrypted OAuth tokens to the admin UI.
    exclude = ("access_token", "refresh_token")
