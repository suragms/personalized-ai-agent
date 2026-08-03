from rest_framework import serializers

from .models import Commit, GithubInsight, Issue, PullRequest, Release, Repository


class RepositorySerializer(serializers.ModelSerializer):
    last_commit_days = serializers.IntegerField(read_only=True)
    health = serializers.CharField(read_only=True)

    class Meta:
        model = Repository
        fields = (
            "id",
            "name",
            "full_name",
            "description",
            "language",
            "url",
            "stars",
            "forks",
            "open_issues",
            "open_prs",
            "last_commit_at",
            "last_commit_days",
            "status",
            "health",
        )


class CommitSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True)

    class Meta:
        model = Commit
        fields = ("id", "sha", "author", "message", "date", "additions", "deletions", "changed_files", "repository")


class PullRequestSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True)

    class Meta:
        model = PullRequest
        fields = ("id", "repository", "number", "title", "state", "author", "created_at", "closed_at", "additions")


class IssueSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True)

    class Meta:
        model = Issue
        fields = ("id", "repository", "number", "title", "state", "labels", "created_at", "closed_at")


class ReleaseSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True)

    class Meta:
        model = Release
        fields = ("id", "repository", "tag", "name", "body", "published_at")


class GithubInsightSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True, allow_null=True)

    class Meta:
        model = GithubInsight
        fields = ("id", "repository", "kind", "severity", "text", "data", "created_at")
