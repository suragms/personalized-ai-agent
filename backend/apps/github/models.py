"""GitHub domain models.

Mirrors the GitHub REST surface the agent consumes: repositories, commits,
pull requests, issues, releases, branches, plus a daily productivity metric
and generated insights.
"""
from datetime import date

from django.conf import settings
from django.db import models

from core.models import MetricModel, TimeStampedModel, UUIDModel


class Repository(UUIDModel, TimeStampedModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("at_risk", "At risk"),
        ("inactive", "Inactive"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="repositories")
    name = models.CharField(max_length=160)
    full_name = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=64, blank=True)
    url = models.URLField(blank=True)
    default_branch = models.CharField(max_length=64, default="main")
    stars = models.PositiveIntegerField(default=0)
    forks = models.PositiveIntegerField(default=0)
    open_issues = models.PositiveIntegerField(default=0)
    open_prs = models.PositiveIntegerField(default=0)
    last_commit_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", db_index=True)

    class Meta:
        ordering = ["-last_commit_at"]
        constraints = [models.UniqueConstraint(fields=["owner", "full_name"], name="unique_repo")]

    def __str__(self) -> str:
        return self.full_name

    @property
    def last_commit_days(self) -> int | None:
        if self.last_commit_at is None:
            return None
        return (date.today() - self.last_commit_at.date()).days

    @property
    def health(self) -> str:
        days = self.last_commit_days
        if days is None:
            return "no_data"
        if days <= 7:
            return "healthy"
        if days <= 21:
            return "stale"
        return "inactive"


class Commit(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="commits")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="commits")
    sha = models.CharField(max_length=40)
    author = models.CharField(max_length=120)
    message = models.TextField()
    date = models.DateTimeField(db_index=True)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    changed_files = models.IntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["owner", "date"])]

    def __str__(self) -> str:
        return f"{self.sha[:7]} {self.message[:40]}"


class PullRequest(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pull_requests")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="pull_requests")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    state = models.CharField(max_length=16, db_index=True)  # open | merged | closed
    author = models.CharField(max_length=120)
    created_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.number} {self.title}"


class Issue(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="issues")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="issues")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    state = models.CharField(max_length=16, db_index=True)  # open | closed
    labels = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.number} {self.title}"


class Release(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="releases")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="releases")
    tag = models.CharField(max_length=64)
    name = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)
    published_at = models.DateTimeField()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return f"{self.repository.full_name}@{self.tag}"


class Branch(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="branches")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=160)
    is_default = models.BooleanField(default=False)
    last_commit_at = models.DateTimeField(null=True, blank=True)
    commit_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.repository.name}/{self.name}"


class DailyMetric(MetricModel):
    """Aggregated daily productivity metric per user."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_metrics")
    commits = models.PositiveIntegerField(default=0)
    additions = models.PositiveIntegerField(default=0)
    deletions = models.PositiveIntegerField(default=0)
    prs_merged = models.PositiveIntegerField(default=0)
    issues_closed = models.PositiveIntegerField(default=0)
    active_repos = models.PositiveIntegerField(default=0)
    productivity_score = models.FloatField(default=0.0)
    coding_hours = models.FloatField(default=0.0)

    class Meta(MetricModel.Meta):
        constraints = [models.UniqueConstraint(fields=["owner", "date"], name="unique_daily_metric")]

    def __str__(self) -> str:
        return f"{self.date} — {self.commits} commits"


class GithubInsight(UUIDModel, TimeStampedModel):
    """Generated recommendation / alert for the user."""

    SEVERITY_CHOICES = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="github_insights")
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, null=True, blank=True, related_name="insights")
    kind = models.CharField(max_length=32, default="recommendation")  # recommendation | alert | insight
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info")
    text = models.TextField()
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.text[:60]}"
