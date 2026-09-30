"""GitHub insights generation from real data.

Generates Intelligence.Insight records from GitHub activity.
Evidence-based only - no fabricated metrics.
"""
import logging
from datetime import date, timedelta

from django.utils import timezone
from intelligence.models import Insight
from intelligence.services import IntelligenceService

from accounts.models import User

from .models import Commit, Issue, PullRequest, Repository

logger = logging.getLogger("github")


class GitHubInsightsGenerator:
    """Generate insights from GitHub data."""

    def __init__(self, user: User):
        self.user = user

    def generate_all(self) -> list[Insight]:
        """Generate all insights."""
        insights = []

        insights.extend(self._check_inactive_repositories())
        insights.extend(self._check_stale_prs())
        insights.extend(self._check_open_issues())
        insights.extend(self._check_recent_activity())
        insights.extend(self._check_release_opportunities())

        return insights

    def _check_inactive_repositories(self) -> list[Insight]:
        """Check for inactive repositories."""
        insights = []

        repos = Repository.objects.filter(owner=self.user)

        for repo in repos:
            days_since_commit = repo.last_commit_days

            if days_since_commit is None:
                continue

            if days_since_commit > 90:
                insight = Insight.objects.create(
                    owner=self.user,
                    insight_type="risk",
                    severity="medium",
                    confidence="high",
                    title=f"{repo.name} has been inactive for {days_since_commit} days",
                    description=f"Repository '{repo.full_name}' has not received any commits in over 90 days.",
                    evidence=f"Last commit: {repo.last_commit_at.date() if repo.last_commit_at else 'never'}\n"
                    f"Days since last commit: {days_since_commit}\n"
                    f"Repository URL: {repo.url}",
                    source_references=[{"repository_id": str(repo.id), "repository": repo.full_name, "source": "github"}],
                    recommended_action=f"Review {repo.name} and decide: archive if no longer maintained, or plan updates to keep it active.",
                )
                insights.append(insight)

            elif days_since_commit > 30:
                insight = Insight.objects.create(
                    owner=self.user,
                    insight_type="observation",
                    severity="low",
                    confidence="high",
                    title=f"{repo.name} activity has slowed",
                    description=f"Repository '{repo.full_name}' last received a commit {days_since_commit} days ago.",
                    evidence=f"Last commit: {repo.last_commit_at.date() if repo.last_commit_at else 'never'}\n"
                    f"Days since last commit: {days_since_commit}\n"
                    f"Repository URL: {repo.url}",
                    source_references=[{"repository_id": str(repo.id), "repository": repo.full_name, "source": "github"}],
                    recommended_action=f"Consider scheduling time to work on {repo.name} to maintain momentum.",
                )
                insights.append(insight)

        return insights

    def _check_stale_prs(self) -> list[Insight]:
        """Check for stale pull requests."""
        insights = []

        cutoff = timezone.now() - timedelta(days=14)
        stale_prs = PullRequest.objects.filter(owner=self.user, state="open", created_at__lt=cutoff)

        if stale_prs.exists():
            pr_list = "\n".join([f"- #{pr.number}: {pr.title} ({pr.repository.name})" for pr in stale_prs[:5]])

            insight = Insight.objects.create(
                owner=self.user,
                insight_type="blocker",
                severity="medium",
                confidence="high",
                title=f"{stale_prs.count()} pull requests have been open for 14+ days",
                description=f"You have {stale_prs.count()} pull requests that have been open for more than 2 weeks.",
                evidence=f"Stale PRs:\n{pr_list}",
                source_references=[
                    {"pr_id": str(pr.id), "pr_number": pr.number, "repository": pr.repository.full_name, "source": "github"}
                    for pr in stale_prs[:10]
                ],
                recommended_action="Review these PRs and either merge, close, or update them to keep development moving.",
            )
            insights.append(insight)

            # Create alert for critical stale PRs
            if stale_prs.count() > 5:
                IntelligenceService.create_alert(
                    user=self.user,
                    category="github",
                    severity="medium",
                    title=f"{stale_prs.count()} stale pull requests need attention",
                    message=f"You have {stale_prs.count()} PRs open for 14+ days across your repositories.",
                    evidence=pr_list,
                    source_type="github",
                )

        return insights

    def _check_open_issues(self) -> list[Insight]:
        """Check open issues."""
        insights = []

        open_issues = Issue.objects.filter(owner=self.user, state="open")
        total_issues = Issue.objects.filter(owner=self.user).count()

        if total_issues == 0:
            return insights

        open_count = open_issues.count()

        if open_count > 20:
            insight = Insight.objects.create(
                owner=self.user,
                insight_type="observation",
                severity="low",
                confidence="high",
                title=f"{open_count} open issues across repositories",
                description=f"You have {open_count} open issues across your repositories.",
                evidence=f"Open issues: {open_count}\nTotal issues: {total_issues}",
                source_references=[{"issue_count": open_count, "source": "github"}],
                recommended_action="Consider triaging issues by priority and closing stale ones.",
            )
            insights.append(insight)

        return insights

    def _check_recent_activity(self) -> list[Insight]:
        """Check recent commit activity."""
        insights = []

        today = date.today()
        week_ago = today - timedelta(days=7)

        recent_commits = Commit.objects.filter(owner=self.user, date__date__gte=week_ago).count()

        if recent_commits == 0:
            insight = Insight.objects.create(
                owner=self.user,
                insight_type="observation",
                severity="low",
                confidence="high",
                title="No commits in the past week",
                description="You haven't made any commits to your repositories in the last 7 days.",
                evidence=f"Commit count (last 7 days): 0\nPeriod: {week_ago} to {today}",
                source_references=[{"source": "github", "period": "7_days"}],
                recommended_action="Consider making a small contribution to maintain development momentum.",
            )
            insights.append(insight)

        elif recent_commits > 20:
            insight = Insight.objects.create(
                owner=self.user,
                insight_type="trend",
                severity="info",
                confidence="high",
                title=f"High activity: {recent_commits} commits this week",
                description=f"You've been very active with {recent_commits} commits in the past 7 days.",
                evidence=f"Commit count (last 7 days): {recent_commits}\nPeriod: {week_ago} to {today}",
                source_references=[{"source": "github", "period": "7_days", "commit_count": recent_commits}],
                recommended_action="Great momentum! Consider writing documentation or tests alongside development.",
            )
            insights.append(insight)

        return insights

    def _check_release_opportunities(self) -> list[Insight]:
        """Check for repositories that could use a release."""
        insights = []

        from .models import Release

        repos_with_recent_commits = Repository.objects.filter(
            owner=self.user, last_commit_at__gte=timezone.now() - timedelta(days=30)
        )

        for repo in repos_with_recent_commits:
            # Check if there's been activity since last release
            latest_release = Release.objects.filter(repository=repo).order_by("-published_at").first()

            if latest_release:
                commits_since_release = Commit.objects.filter(
                    repository=repo, date__gt=latest_release.published_at
                ).count()

                if commits_since_release >= 10:
                    insight = Insight.objects.create(
                        owner=self.user,
                        insight_type="opportunity",
                        severity="low",
                        confidence="medium",
                        title=f"{repo.name} has {commits_since_release} commits since last release",
                        description=f"Repository '{repo.full_name}' has accumulated {commits_since_release} commits since its last release.",
                        evidence=f"Last release: {latest_release.tag} on {latest_release.published_at.date()}\n"
                        f"Commits since then: {commits_since_release}\n"
                        f"Repository URL: {repo.url}",
                        source_references=[
                            {
                                "repository_id": str(repo.id),
                                "repository": repo.full_name,
                                "last_release": latest_release.tag,
                                "source": "github",
                            }
                        ],
                        recommended_action=f"Consider creating a new release for {repo.name} to document recent changes.",
                    )
                    insights.append(insight)

        return insights
