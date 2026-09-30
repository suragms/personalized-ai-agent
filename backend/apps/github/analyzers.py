"""GitHub deterministic analyzers (spec §4/§5).

Every number is computed from rows synced by GitHubSyncService. When the
user has no repositories, analyzers return an empty list — the engine
records ``UNAVAILABLE_DATA`` / no-data state instead of inventing zeros
as findings.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from intelligence.analyzers import AnalysisFinding, BaseAnalyzer

from .models import Commit, Issue, PullRequest, Release, Repository


def _ev(**kwargs) -> dict:
    entry = {"source": "github"}
    entry.update({k: v for k, v in kwargs.items() if v is not None})
    return entry


class GitHubActivityAnalyzer(BaseAnalyzer):
    """Repository activity, trends, and contribution consistency."""

    source = "github"

    def analyze(self, user, *, now=None, **kwargs) -> list[AnalysisFinding]:
        now = now or timezone.now()
        if not Repository.objects.filter(owner=user).exists():
            return []

        commits_30d = Commit.objects.filter(owner=user, date__gte=now - timedelta(days=30)).count()
        commits_prior_30d = Commit.objects.filter(
            owner=user, date__gte=now - timedelta(days=60), date__lt=now - timedelta(days=30)
        ).count()
        active_days = (
            Commit.objects.filter(owner=user, date__gte=now - timedelta(days=30))
            .values_list("date__date", flat=True)
            .distinct()
            .count()
        )
        active_repos = (
            Repository.objects.filter(owner=user, last_commit_at__gte=now - timedelta(days=30)).count()
        )
        findings: list[AnalysisFinding] = []

        # Declining activity: ≥40% drop with a meaningful baseline.
        if commits_prior_30d >= 5 and commits_30d < commits_prior_30d * 0.6:
            drop_pct = round(100 * (1 - commits_30d / commits_prior_30d))
            findings.append(
                AnalysisFinding(
                    metric="declining_activity",
                    value=commits_30d,
                    period="30d",
                    source=self.source,
                    evidence=[
                        _ev(metric="commits_last_30d", value=commits_30d),
                        _ev(metric="commits_prior_30d", value=commits_prior_30d),
                        _ev(metric="drop_pct", value=drop_pct),
                    ],
                    insight_type="trend",
                    severity="medium",
                    title=f"Commit activity dropped {drop_pct}% vs the previous 30 days",
                    description=(
                        f"{commits_30d} commits in the last 30 days versus "
                        f"{commits_prior_30d} in the 30 days before that."
                    ),
                    recommended_action="Review what changed in your workload and whether this project still needs attention.",
                    dedup_key="github:activity:declining_30d",
                    observed_metrics={
                        "commits_last_30d": commits_30d,
                        "commits_prior_30d": commits_prior_30d,
                        "active_repos_30d": active_repos,
                        "active_days_30d": active_days,
                    },
                )
            )

        # No commits in 30 days despite having repositories.
        if commits_30d == 0:
            findings.append(
                AnalysisFinding(
                    metric="no_recent_activity",
                    value=0,
                    period="30d",
                    source=self.source,
                    evidence=[_ev(metric="commits_last_30d", value=0)],
                    insight_type="observation",
                    severity="low",
                    title="No commits in the past 30 days",
                    description="No commits have been recorded across your repositories in the last 30 days.",
                    recommended_action="If you intend to keep working on these projects, schedule a small session this week.",
                    dedup_key="github:activity:none_30d",
                    observed_metrics={"commits_last_30d": 0, "active_repos_30d": active_repos},
                )
            )
        elif active_days and commits_30d >= 5 and active_days <= 3:
            findings.append(
                AnalysisFinding(
                    metric="low_contribution_consistency",
                    value=active_days,
                    period="30d",
                    source=self.source,
                    evidence=[
                        _ev(metric="active_days_30d", value=active_days),
                        _ev(metric="commits_last_30d", value=commits_30d),
                    ],
                    insight_type="observation",
                    severity="info",
                    title=f"{commits_30d} commits concentrated into {active_days} active day(s)",
                    description=(
                        f"Your last-30-day commits landed on only {active_days} distinct day(s) "
                        f"({commits_30d} commits total) — activity is bursty rather than consistent."
                    ),
                    recommended_action="Consider spreading work into smaller, regular sessions to maintain momentum.",
                    dedup_key="github:activity:low_consistency_30d",
                    observed_metrics={"active_days_30d": active_days, "commits_last_30d": commits_30d},
                )
            )

        return findings


class RepositoryHealthAnalyzer(BaseAnalyzer):
    """Per-repository health from last-commit recency."""

    source = "github"

    def analyze(self, user, *, now=None, **kwargs) -> list[AnalysisFinding]:
        now = now or timezone.now()
        findings: list[AnalysisFinding] = []

        repos = Repository.objects.filter(owner=user)
        for repo in repos:
            if repo.last_commit_at is None:
                findings.append(
                    AnalysisFinding(
                        metric="repository_without_commits",
                        value=None,
                        period="all",
                        source=self.source,
                        evidence=[_ev(repository=repo.full_name, metric="last_commit", value="never")],
                        insight_type="observation",
                        severity="info",
                        title=f"{repo.name} has no recorded commits",
                        description=f"Repository '{repo.full_name}' has never received a synced commit.",
                        recommended_action=f"Sync {repo.name} or push initial code to establish activity history.",
                        dedup_key=f"github:repo:no_commits:{repo.full_name}",
                        observed_metrics={"repository": repo.full_name},
                    )
                )
                continue

            days = (now.date() - repo.last_commit_at.date()).days
            last_commit = repo.last_commit_at.date().isoformat()

            if days > 90:
                findings.append(
                    AnalysisFinding(
                        metric="inactive_repository",
                        value=days,
                        period="90d",
                        source=self.source,
                        evidence=[
                            _ev(repository=repo.full_name, metric="last_commit", value=last_commit),
                            _ev(repository=repo.full_name, metric="days_since_last_commit", value=days),
                        ],
                        insight_type="risk",
                        severity="medium",
                        title=f"{repo.name} has been inactive for {days} days",
                        description=f"Repository '{repo.full_name}' has not received a commit in over 90 days.",
                        recommended_action=f"Review {repo.name}: archive it if it is finished, or plan updates to keep it maintained.",
                        dedup_key=f"github:repo:inactive:{repo.full_name}",
                        observed_metrics={"days_since_last_commit": days, "last_commit": last_commit},
                    )
                )
            elif days > 30:
                findings.append(
                    AnalysisFinding(
                        metric="slowing_repository",
                        value=days,
                        period="30d",
                        source=self.source,
                        evidence=[
                            _ev(repository=repo.full_name, metric="last_commit", value=last_commit),
                            _ev(repository=repo.full_name, metric="days_since_last_commit", value=days),
                        ],
                        insight_type="observation",
                        severity="low",
                        title=f"{repo.name} activity has slowed",
                        description=f"Repository '{repo.full_name}' last received a commit {days} days ago.",
                        recommended_action=f"Consider scheduling time on {repo.name} to maintain momentum.",
                        dedup_key=f"github:repo:slowing:{repo.full_name}",
                        observed_metrics={"days_since_last_commit": days, "last_commit": last_commit},
                    )
                )

        return findings


class PullRequestAnalyzer(BaseAnalyzer):
    """Open and stale pull requests."""

    source = "github"

    def analyze(self, user, *, now=None, **kwargs) -> list[AnalysisFinding]:
        now = now or timezone.now()
        if not Repository.objects.filter(owner=user).exists():
            return []

        findings: list[AnalysisFinding] = []
        stale_cutoff = now - timedelta(days=14)
        open_prs = PullRequest.objects.filter(owner=user, state="open")
        open_count = open_prs.count()
        stale_prs = list(open_prs.filter(created_at__lt=stale_cutoff).order_by("created_at"))

        if stale_prs:
            oldest_days = (now - stale_prs[0].created_at).days
            evidence = [
                _ev(
                    repository=pr.repository.full_name,
                    metric="open_pr_age_days",
                    value=(now - pr.created_at).days,
                    pr=f"#{pr.number}",
                    title=pr.title,
                )
                for pr in stale_prs[:10]
            ]
            findings.append(
                AnalysisFinding(
                    metric="stale_pull_requests",
                    value=len(stale_prs),
                    period="14d",
                    source=self.source,
                    evidence=evidence,
                    insight_type="blocker",
                    severity="medium",
                    title=f"{len(stale_prs)} pull request(s) open for 14+ days",
                    description=(
                        f"{len(stale_prs)} pull request(s) have been open for more than 14 days; "
                        f"the oldest has been open {oldest_days} days."
                    ),
                    recommended_action="Review these PRs and decide for each: merge, update, or close.",
                    dedup_key="github:prs:stale_14d",
                    observed_metrics={
                        "stale_pr_count": len(stale_prs),
                        "open_pr_count": open_count,
                        "oldest_open_pr_days": oldest_days,
                    },
                )
            )

        if open_count > 10:
            findings.append(
                AnalysisFinding(
                    metric="open_pull_request_backlog",
                    value=open_count,
                    period="current",
                    source=self.source,
                    evidence=[_ev(metric="open_pr_count", value=open_count)],
                    insight_type="observation",
                    severity="low",
                    title=f"{open_count} pull requests currently open",
                    description=f"You have {open_count} open pull requests across your repositories.",
                    recommended_action="Work down the backlog or close PRs that are no longer relevant.",
                    dedup_key="github:prs:open_backlog",
                    observed_metrics={"open_pr_count": open_count},
                )
            )

        return findings


class IssueAnalyzer(BaseAnalyzer):
    """Open and stale issues."""

    source = "github"

    def analyze(self, user, *, now=None, **kwargs) -> list[AnalysisFinding]:
        now = now or timezone.now()
        if not Repository.objects.filter(owner=user).exists():
            return []

        findings: list[AnalysisFinding] = []
        stale_cutoff = now - timedelta(days=30)
        open_issues = Issue.objects.filter(owner=user, state="open")
        open_count = open_issues.count()
        stale_issues = list(open_issues.filter(created_at__lt=stale_cutoff).order_by("created_at")[:10])

        if stale_issues:
            evidence = [
                _ev(
                    repository=iss.repository.full_name,
                    metric="open_issue_age_days",
                    value=(now - iss.created_at).days,
                    issue=f"#{iss.number}",
                    title=iss.title,
                )
                for iss in stale_issues
            ]
            findings.append(
                AnalysisFinding(
                    metric="stale_issues",
                    value=len(stale_issues),
                    period="30d",
                    source=self.source,
                    evidence=evidence,
                    insight_type="observation",
                    severity="low",
                    title=f"{len(stale_issues)} issue(s) open for 30+ days",
                    description=f"{len(stale_issues)} issue(s) have been open for more than 30 days.",
                    recommended_action="Triage these issues: fix, schedule, label as wontfix, or close.",
                    dedup_key="github:issues:stale_30d",
                    observed_metrics={"stale_issue_count": len(stale_issues), "open_issue_count": open_count},
                )
            )

        if open_count > 20:
            findings.append(
                AnalysisFinding(
                    metric="open_issue_backlog",
                    value=open_count,
                    period="current",
                    source=self.source,
                    evidence=[_ev(metric="open_issue_count", value=open_count)],
                    insight_type="observation",
                    severity="low",
                    title=f"{open_count} open issues across repositories",
                    description=f"You have {open_count} open issues across your repositories.",
                    recommended_action="Consider triaging issues by priority and closing stale ones.",
                    dedup_key="github:issues:open_backlog",
                    observed_metrics={"open_issue_count": open_count},
                )
            )

        return findings


class ReleaseAnalyzer(BaseAnalyzer):
    """Release cadence and gaps for actively used repositories."""

    source = "github"

    def analyze(self, user, *, now=None, **kwargs) -> list[AnalysisFinding]:
        now = now or timezone.now()
        findings: list[AnalysisFinding] = []

        active_repos = Repository.objects.filter(
            owner=user, last_commit_at__gte=now - timedelta(days=30)
        )
        for repo in active_repos:
            latest_release = Release.objects.filter(repository=repo).order_by("-published_at").first()

            if latest_release is None:
                repo_age_days = (now.date() - repo.created_at.date()).days
                if repo_age_days < 60:
                    continue  # too new to call missing releases a problem
                findings.append(
                    AnalysisFinding(
                        metric="missing_release",
                        value=0,
                        period="30d",
                        source=self.source,
                        evidence=[
                            _ev(repository=repo.full_name, metric="release_count", value=0),
                            _ev(repository=repo.full_name, metric="last_commit", value=repo.last_commit_at.date().isoformat()),
                        ],
                        insight_type="opportunity",
                        severity="low",
                        title=f"{repo.name} is active but has no releases",
                        description=(
                            f"'{repo.full_name}' received commits in the last 30 days but has "
                            "never published a release."
                        ),
                        recommended_action=f"Consider publishing a release for {repo.name} so consumers can pin a version.",
                        dedup_key=f"github:release:missing:{repo.full_name}",
                        observed_metrics={"release_count": 0, "repository": repo.full_name},
                    )
                )
                continue

            days_since_release = (now - latest_release.published_at).days
            commits_since_release = Commit.objects.filter(
                repository=repo, date__gt=latest_release.published_at
            ).count()

            if days_since_release > 180 and commits_since_release >= 10:
                findings.append(
                    AnalysisFinding(
                        metric="release_gap",
                        value=days_since_release,
                        period="180d",
                        source=self.source,
                        evidence=[
                            _ev(repository=repo.full_name, metric="last_release", value=latest_release.tag),
                            _ev(repository=repo.full_name, metric="days_since_release", value=days_since_release),
                            _ev(repository=repo.full_name, metric="commits_since_release", value=commits_since_release),
                        ],
                        insight_type="opportunity",
                        severity="low",
                        title=f"{repo.name} has {commits_since_release} commits since its last release",
                        description=(
                            f"Last release '{latest_release.tag}' was {days_since_release} days ago; "
                            f"{commits_since_release} commits have landed since."
                        ),
                        recommended_action=f"Consider cutting a new release for {repo.name} to document recent changes.",
                        dedup_key=f"github:release:gap:{repo.full_name}",
                        observed_metrics={
                            "days_since_release": days_since_release,
                            "commits_since_release": commits_since_release,
                        },
                    )
                )

        return findings


GITHUB_ANALYZERS: list[type[BaseAnalyzer]] = [
    GitHubActivityAnalyzer,
    RepositoryHealthAnalyzer,
    PullRequestAnalyzer,
    IssueAnalyzer,
    ReleaseAnalyzer,
]


def run_github_analyzers(user, *, now=None) -> list[AnalysisFinding]:
    """Run every GitHub analyzer and concatenate findings."""
    findings: list[AnalysisFinding] = []
    for cls in GITHUB_ANALYZERS:
        findings.extend(cls().analyze(user, now=now))
    return findings
