"""Intelligence Engine models — insights, recommendations, alerts, goals, decisions, reports."""
from django.db import models

from core.fields import EncryptedCharField, SafeArrayField
from core.models import OwnedModel


# ── Data Provenance ────────────────────────────────────────────────────────
class DataSource(OwnedModel):
    """Tracks where data comes from and its freshness."""

    SOURCE_TYPE_CHOICES = [
        ("github", "GitHub"),
        ("website", "Website/Portfolio"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("twitter", "Twitter/X"),
        ("analytics", "Analytics"),
        ("calendar", "Calendar"),
        ("manual", "User-Provided"),
        ("derived", "AI-Derived"),
    ]

    # Unified connectivity vocabulary (see core.connectivity.ConnectivityStatus).
    # Values are lowercase on the wire; labels are display text.
    STATE_CHOICES = [
        ("connected", "Connected"),
        ("connecting", "Connecting"),
        ("disconnected", "Disconnected"),
        ("not_configured", "Not Configured"),
        ("authentication_failed", "Authentication Failed"),
        ("permission_denied", "Permission Denied"),
        ("rate_limited", "Rate Limited"),
        ("timeout", "Timeout"),
        ("network_error", "Network Error"),
        ("api_error", "API Error"),
        ("service_unavailable", "Service Unavailable"),
        ("invalid_credentials", "Invalid Credentials"),
        ("stale", "Stale"),
        ("no_data", "No Data"),
        ("unknown_error", "Unknown Error"),
    ]

    source_type = models.CharField(max_length=32, choices=SOURCE_TYPE_CHOICES, db_index=True)
    name = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default="disconnected", db_index=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    sync_frequency_hours = models.PositiveIntegerField(default=24)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta(OwnedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["owner", "source_type", "url"], name="unique_datasource")
        ]

    def __str__(self):
        return f"{self.source_type}: {self.name}"


class DataSnapshot(OwnedModel):
    """Point-in-time snapshot of data from a source."""

    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="snapshots")
    snapshot_date = models.DateTimeField(db_index=True)

    # Raw data and metadata
    raw_data = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)

    metrics = models.JSONField(default=dict, blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-snapshot_date"]

    def __str__(self):
        return f"{self.source} @ {self.snapshot_date:%Y-%m-%d %H:%M}"


# ── Insights & Recommendations ─────────────────────────────────────────────
class Insight(OwnedModel):
    """An observation, pattern, opportunity, or risk identified from data."""

    TYPE_CHOICES = [
        ("observation", "Observation"),
        ("trend", "Trend"),
        ("opportunity", "Opportunity"),
        ("risk", "Risk"),
        ("blocker", "Blocker"),
        ("improvement", "Improvement Suggestion"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    CONFIDENCE_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("accepted", "Accepted"),
        ("dismissed", "Dismissed"),
        ("converted_to_task", "Converted to Task"),
        ("completed", "Completed"),
    ]

    insight_type = models.CharField(max_length=32, choices=TYPE_CHOICES, db_index=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info", db_index=True)
    confidence = models.CharField(max_length=16, choices=CONFIDENCE_CHOICES, default="medium")

    title = models.CharField(max_length=300)
    description = models.TextField()
    evidence = models.TextField()  # What data supports this

    source_references = models.JSONField(default=list, blank=True)  # Links to data sources
    recommended_action = models.TextField(blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="new", db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # User feedback
    helpful = models.BooleanField(null=True, blank=True)
    user_notes = models.TextField(blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.insight_type}: {self.title}"


# ── Alerts ─────────────────────────────────────────────────────────────────
class Alert(OwnedModel):
    """Actionable alerts for user attention."""

    CATEGORY_CHOICES = [
        ("security", "Security"),
        ("deadline", "Deadline"),
        ("project", "Project"),
        ("github", "GitHub"),
        ("website", "Website"),
        ("content", "Content"),
        ("performance", "Performance"),
        ("integration", "Integration"),
        ("system", "System"),
        ("ai", "AI"),
        ("goal", "Goal"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("read", "Read"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, db_index=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info", db_index=True)

    title = models.CharField(max_length=300)
    message = models.TextField()
    evidence = models.TextField(blank=True)

    source_type = models.CharField(max_length=64, blank=True)
    action_url = models.URLField(blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active", db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.category}: {self.title}"


# ── Goals & Projects ───────────────────────────────────────────────────────
class Goal(OwnedModel):
    """User goals with progress tracking."""

    CATEGORY_CHOICES = [
        ("career", "Career"),
        ("project", "Project"),
        ("learning", "Learning"),
        ("content", "Content"),
        ("business", "Business"),
        ("personal", "Personal"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, db_index=True)

    target = models.TextField(blank=True)  # What success looks like
    deadline = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active", db_index=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default="medium")
    progress_pct = models.PositiveIntegerField(default=0)

    # Connection to other models
    related_projects = models.ManyToManyField("projects.Project", blank=True, related_name="goals")

    milestones = models.JSONField(default=list, blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return self.title


# ── Decisions ──────────────────────────────────────────────────────────────
class Decision(OwnedModel):
    """Structured decision-making framework."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("decided", "Decided"),
        ("implemented", "Implemented"),
        ("revisit", "Revisit"),
    ]

    title = models.CharField(max_length=300)
    context = models.TextField()

    options = models.JSONField(default=list, blank=True)  # List of options considered
    evidence = models.JSONField(default=dict, blank=True)
    pros_cons = models.JSONField(default=dict, blank=True)
    risks = models.JSONField(default=list, blank=True)
    unknowns = models.TextField(blank=True)

    ai_recommendation = models.TextField(blank=True)
    ai_reasoning = models.TextField(blank=True)

    user_decision = models.TextField(blank=True)
    decision_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending", db_index=True)
    review_date = models.DateField(null=True, blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# ── Reports ────────────────────────────────────────────────────────────────
class Report(OwnedModel):
    """Generated reports with full provenance."""

    TYPE_CHOICES = [
        ("daily_intelligence", "Daily Intelligence"),
        ("weekly_review", "Weekly Review"),
        ("monthly_review", "Monthly Review"),
        ("project_report", "Project Report"),
        ("github_report", "GitHub Report"),
        ("website_report", "Website Report"),
        ("content_report", "Content Report"),
        ("performance_report", "Performance Report"),
        ("goal_review", "Goal Review"),
        ("integration_health", "Integration Health"),
        ("security_report", "Security Report"),
    ]

    report_type = models.CharField(max_length=64, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=300)

    # Analysis period
    period_start = models.DateField()
    period_end = models.DateField()

    # Content
    content = models.TextField()  # Markdown
    summary = models.TextField()

    # Provenance
    data_sources = models.JSONField(default=list, blank=True)  # Which sources were used
    data_freshness = models.JSONField(default=dict, blank=True)  # Timestamp per source

    # Findings
    metrics = models.JSONField(default=dict, blank=True)
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    confidence = models.CharField(max_length=16, choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium")
    limitations = models.TextField(blank=True)  # What data was unavailable

    class Meta(OwnedModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "report_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.report_type}: {self.title}"


# ── Performance Metrics ────────────────────────────────────────────────────
class PerformanceMetric(OwnedModel):
    """Multi-dimensional performance tracking."""

    DIMENSION_CHOICES = [
        ("development", "Development"),
        ("portfolio", "Portfolio"),
        ("content", "Content"),
        ("professional_presence", "Professional Presence"),
        ("project_activity", "Project Activity"),
        ("learning", "Learning"),
        ("productivity", "Productivity"),
        ("goals", "Goals"),
        ("technical_growth", "Technical Growth"),
    ]

    dimension = models.CharField(max_length=64, choices=DIMENSION_CHOICES, db_index=True)
    date = models.DateField(db_index=True)

    score = models.FloatField(null=True, blank=True)  # 0-100, or null if insufficient data
    confidence = models.CharField(max_length=16, choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium")

    metrics = models.JSONField(default=dict, blank=True)
    evidence = models.JSONField(default=list, blank=True)

    insights = models.TextField(blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "dimension", "date"], name="unique_performance_metric")
        ]

    def __str__(self):
        return f"{self.dimension} @ {self.date}"


# ── Daily Plans ────────────────────────────────────────────────────────────
class DailyPlan(OwnedModel):
    """Generated daily workflow plan."""

    date = models.DateField(db_index=True)

    # Morning brief
    priorities = models.JSONField(default=list, blank=True)
    important_alerts = SafeArrayField(models.UUIDField(), blank=True, default=list)
    upcoming_deadlines = models.JSONField(default=list, blank=True)
    recommended_focus = models.TextField(blank=True)
    potential_blockers = models.JSONField(default=list, blank=True)

    # Tasks
    tasks = SafeArrayField(models.UUIDField(), blank=True, default=list)
    time_blocks = models.JSONField(default=list, blank=True)

    # Evening review
    completed_tasks = SafeArrayField(models.UUIDField(), blank=True, default=list)
    incomplete_tasks = SafeArrayField(models.UUIDField(), blank=True, default=list)
    evening_insights = models.TextField(blank=True)
    tomorrow_priorities = models.JSONField(default=list, blank=True)

    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "date"], name="unique_daily_plan")
        ]

    def __str__(self):
        return f"Daily Plan {self.date}"


# ── User Profile Extensions ────────────────────────────────────────────────
class UserProfile(models.Model):
    """Extended user profile with onboarding and preferences."""

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="intelligence_profile")

    # Onboarding
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.CharField(max_length=64, blank=True)

    # Professional identity
    professional_title = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    # External profiles (just URLs, not connections)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    other_urls = models.JSONField(default=list, blank=True)

    # Preferences
    timezone = models.CharField(max_length=64, default="UTC")
    working_hours_start = models.TimeField(null=True, blank=True)
    working_hours_end = models.TimeField(null=True, blank=True)
    working_days = SafeArrayField(models.IntegerField(), blank=True, default=list)  # 0=Monday

    # Goals and priorities
    primary_goals = models.JSONField(default=list, blank=True)
    current_priorities = models.JSONField(default=list, blank=True)

    # AI preferences
    preferred_ai_behavior = models.TextField(blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


# ── Integration Connections ────────────────────────────────────────────────
class IntegrationConnection(OwnedModel):
    """Tracks actual API/OAuth connections separate from profile URLs."""

    PLATFORM_CHOICES = [
        ("github", "GitHub"),
        ("google", "Google"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("twitter", "Twitter/X"),
        ("analytics", "Google Analytics"),
        ("search_console", "Google Search Console"),
        ("youtube", "YouTube"),
    ]

    STATUS_CHOICES = [
        ("connected", "Connected"),
        ("connecting", "Connecting"),
        ("disconnected", "Disconnected"),
        ("not_configured", "Not Configured"),
        ("authentication_failed", "Authentication Failed"),
        ("permission_denied", "Permission Denied"),
        ("rate_limited", "Rate Limited"),
        ("timeout", "Timeout"),
        ("network_error", "Network Error"),
        ("api_error", "API Error"),
        ("service_unavailable", "Service Unavailable"),
        ("invalid_credentials", "Invalid Credentials"),
        ("stale", "Stale"),
        ("no_data", "No Data"),
        ("unknown_error", "Unknown Error"),
    ]

    platform = models.CharField(max_length=64, choices=PLATFORM_CHOICES, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="disconnected", db_index=True)

    # OAuth tokens (encrypted)
    access_token = EncryptedCharField(max_length=4096, blank=True)
    refresh_token = EncryptedCharField(max_length=4096, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Connection metadata
    connected_account = models.CharField(max_length=255, blank=True)
    scopes = SafeArrayField(models.CharField(max_length=128), blank=True, default=list)

    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    retryable = models.BooleanField(default=False)

    class Meta(OwnedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["owner", "platform"], name="unique_integration_connection")
        ]

    def __str__(self):
        return f"{self.platform} - {self.status}"
