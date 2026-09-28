"""GitHub data synchronization service.

Fetches data from GitHub API and creates DataSource/DataSnapshot records.
Implements incremental sync, rate limit handling, and error recovery.
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from accounts.models import User
from intelligence.models import DataSnapshot, DataSource
from intelligence.services import IntelligenceService

from .models import Branch, Commit, Issue, PullRequest, Release, Repository
from .oauth import get_connection, make_api_request

logger = logging.getLogger("github")


class GitHubSyncService:
    """Synchronize GitHub data for a user."""

    def __init__(self, user: User):
        self.user = user
        self.connection = get_connection(user)

        if not self.connection:
            raise ValueError("No active GitHub connection found")

    def sync_all(self) -> dict[str, Any]:
        """Perform full synchronization."""
        results = {
            "started_at": timezone.now().isoformat(),
            "user": self.user.username,
            "repositories": 0,
            "commits": 0,
            "pull_requests": 0,
            "issues": 0,
            "releases": 0,
            "errors": [],
        }

        try:
            # Create or get data source
            data_source = self._get_or_create_data_source()
            data_source.state = "syncing"
            data_source.save()

            # Sync repositories first
            repos = self._sync_repositories()
            results["repositories"] = len(repos)

            # Sync data for each repository
            for repo in repos:
                try:
                    # Commits
                    commits = self._sync_commits(repo)
                    results["commits"] += len(commits)

                    # Pull requests
                    prs = self._sync_pull_requests(repo)
                    results["pull_requests"] += len(prs)

                    # Issues
                    issues = self._sync_issues(repo)
                    results["issues"] += len(issues)

                    # Releases
                    releases = self._sync_releases(repo)
                    results["releases"] += len(releases)

                except Exception as e:
                    error_msg = f"Error syncing {repo.full_name}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Create snapshot
            self._create_snapshot(data_source, results)

            # Update data source state
            data_source.state = "connected"
            data_source.last_synced_at = timezone.now()
            data_source.last_error = ""
            data_source.save()

            # Update connection
            self.connection.last_synced_at = timezone.now()
            self.connection.last_error = ""
            self.connection.save()

            # Generate insights after successful sync
            IntelligenceService.generate_insights(self.user, source_type="github")

            results["completed_at"] = timezone.now().isoformat()
            results["status"] = "success"

        except Exception as e:
            error_msg = f"GitHub sync failed: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["status"] = "error"

            # Update data source error state
            if data_source:
                data_source.state = "error"
                data_source.last_error = error_msg
                data_source.save()

        return results

    def _get_or_create_data_source(self) -> DataSource:
        """Get or create data source for GitHub."""
        github_username = self.connection.connected_account or self.user.github_username or "unknown"

        source, created = DataSource.objects.get_or_create(
            owner=self.user,
            source_type="github",
            url=f"https://github.com/{github_username}",
            defaults={
                "name": f"GitHub ({github_username})",
                "state": "disconnected",
                "sync_frequency_hours": 24,
            },
        )

        return source

    def _sync_repositories(self) -> list[Repository]:
        """Sync user's repositories."""
        repos_data = make_api_request(self.connection, "/user/repos", {"per_page": 100, "sort": "updated"})

        repositories = []

        for repo_data in repos_data:
            # Skip forks unless user explicitly contributed
            if repo_data.get("fork") and repo_data.get("size", 0) == 0:
                continue

            repo, created = Repository.objects.update_or_create(
                owner=self.user,
                full_name=repo_data["full_name"],
                defaults={
                    "name": repo_data["name"],
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language", ""),
                    "url": repo_data["html_url"],
                    "default_branch": repo_data.get("default_branch", "main"),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                },
            )

            repositories.append(repo)

            if created:
                logger.info(f"Created repository: {repo.full_name}")

        return repositories

    def _sync_commits(self, repo: Repository, days: int = 90) -> list[Commit]:
        """Sync commits for a repository (incremental)."""
        since = timezone.now() - timedelta(days=days)

        # Check if we have commits already
        latest_commit = Commit.objects.filter(repository=repo).order_by("-date").first()
        if latest_commit:
            since = latest_commit.date

        try:
            commits_data = make_api_request(
                self.connection,
                f"/repos/{repo.full_name}/commits",
                {"since": since.isoformat(), "per_page": 100},
            )

            commits = []

            for commit_data in commits_data:
                commit_info = commit_data.get("commit", {})
                author_info = commit_info.get("author", {})
                stats = commit_data.get("stats", {})

                # Skip if not by the authenticated user
                commit_author = commit_data.get("author", {})
                if commit_author and commit_author.get("login") != self.connection.connected_account:
                    continue

                commit, created = Commit.objects.update_or_create(
                    owner=self.user,
                    repository=repo,
                    sha=commit_data["sha"],
                    defaults={
                        "author": author_info.get("name", ""),
                        "message": commit_info.get("message", ""),
                        "date": datetime.fromisoformat(author_info["date"].replace("Z", "+00:00")),
                        "additions": stats.get("additions", 0),
                        "deletions": stats.get("deletions", 0),
                        "changed_files": len(commit_data.get("files", [])),
                    },
                )

                commits.append(commit)

            # Update repository last commit
            if commits:
                latest = max(commits, key=lambda c: c.date)
                repo.last_commit_at = latest.date
                repo.save()

            return commits

        except Exception as e:
            logger.warning(f"Failed to sync commits for {repo.full_name}: {e}")
            return []

    def _sync_pull_requests(self, repo: Repository) -> list[PullRequest]:
        """Sync pull requests for a repository."""
        try:
            # Get all PRs (open and closed)
            prs_data = make_api_request(
                self.connection,
                f"/repos/{repo.full_name}/pulls",
                {"state": "all", "per_page": 100},
            )

            prs = []

            for pr_data in prs_data:
                # Skip if not by the authenticated user
                if pr_data.get("user", {}).get("login") != self.connection.connected_account:
                    continue

                closed_at = None
                if pr_data.get("closed_at"):
                    closed_at = datetime.fromisoformat(pr_data["closed_at"].replace("Z", "+00:00"))

                pr, created = PullRequest.objects.update_or_create(
                    owner=self.user,
                    repository=repo,
                    number=pr_data["number"],
                    defaults={
                        "title": pr_data["title"],
                        "state": pr_data["state"],
                        "author": pr_data["user"]["login"],
                        "created_at": datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
                        "closed_at": closed_at,
                        "additions": pr_data.get("additions", 0),
                        "deletions": pr_data.get("deletions", 0),
                    },
                )

                prs.append(pr)

            return prs

        except Exception as e:
            logger.warning(f"Failed to sync PRs for {repo.full_name}: {e}")
            return []

    def _sync_issues(self, repo: Repository) -> list[Issue]:
        """Sync issues for a repository."""
        try:
            issues_data = make_api_request(
                self.connection,
                f"/repos/{repo.full_name}/issues",
                {"state": "all", "per_page": 100},
            )

            issues = []

            for issue_data in issues_data:
                # Skip pull requests (they appear in issues API too)
                if "pull_request" in issue_data:
                    continue

                closed_at = None
                if issue_data.get("closed_at"):
                    closed_at = datetime.fromisoformat(issue_data["closed_at"].replace("Z", "+00:00"))

                labels = [label["name"] for label in issue_data.get("labels", [])]

                issue, created = Issue.objects.update_or_create(
                    owner=self.user,
                    repository=repo,
                    number=issue_data["number"],
                    defaults={
                        "title": issue_data["title"],
                        "state": issue_data["state"],
                        "labels": labels,
                        "created_at": datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        "closed_at": closed_at,
                    },
                )

                issues.append(issue)

            # Update repository open issues count
            repo.open_issues = len([i for i in issues if i.state == "open"])
            repo.save()

            return issues

        except Exception as e:
            logger.warning(f"Failed to sync issues for {repo.full_name}: {e}")
            return []

    def _sync_releases(self, repo: Repository) -> list[Release]:
        """Sync releases for a repository."""
        try:
            releases_data = make_api_request(
                self.connection,
                f"/repos/{repo.full_name}/releases",
                {"per_page": 50},
            )

            releases = []

            for release_data in releases_data:
                release, created = Release.objects.update_or_create(
                    owner=self.user,
                    repository=repo,
                    tag=release_data["tag_name"],
                    defaults={
                        "name": release_data.get("name", ""),
                        "body": release_data.get("body", ""),
                        "published_at": datetime.fromisoformat(release_data["published_at"].replace("Z", "+00:00")),
                    },
                )

                releases.append(release)

            return releases

        except Exception as e:
            logger.warning(f"Failed to sync releases for {repo.full_name}: {e}")
            return []

    def _create_snapshot(self, data_source: DataSource, results: dict[str, Any]) -> DataSnapshot:
        """Create a data snapshot record."""
        # Create content hash
        content = json.dumps(results, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:64]

        snapshot = DataSnapshot.objects.create(
            owner=self.user,
            source=data_source,
            snapshot_date=timezone.now(),
            raw_data=results,
            content_hash=content_hash,
            metrics={
                "repositories": results["repositories"],
                "commits": results["commits"],
                "pull_requests": results["pull_requests"],
                "issues": results["issues"],
                "releases": results["releases"],
                "error_count": len(results.get("errors", [])),
            },
        )

        logger.info(f"Created GitHub snapshot for {self.user.username}")

        return snapshot
