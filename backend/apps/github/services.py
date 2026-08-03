"""GitHub analytics services.

Pure computation over the seeded/synced repository data. These power the
dashboard, the reports, the command router, and the agent's analysis node.
"""
import logging
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from core.utils import daterange, start_of_week

from .models import Commit, DailyMetric, GithubInsight, Issue, PullRequest, Repository

logger = logging.getLogger("agents")

ACTIVE_DAYS = 7
STALE_DAYS = 21


# ── Productivity score ─────────────────────────────────────────────────────
def compute_productivity_score(owner, start: date | None = None, end: date | None = None) -> float:
    """Heuristic 0-100 score for a period:
    commits (40) + code volume (30) + consistency (20) + pull-through (10).
    """
    end = end or date.today()
    start = start or (end - timedelta(days=6))

    commits = Commit.objects.filter(owner=owner, date__date__gte=start, date__date__lte=end)
    total = commits.count()
    additions = commits.aggregate(s=Sum("additions"))["s"] or 0
    prs = PullRequest.objects.filter(owner=owner, state="merged", closed_at__date__gte=start, closed_at__date__lte=end).count()
    issues_closed = Issue.objects.filter(owner=owner, state="closed", closed_at__date__gte=start, closed_at__date__lte=end).count()

    active_days = commits.dates("date", "day").count()
    span_days = max((end - start).days, 1)

    score = 0.0
    score += min(40, total * 2.2)  # up to 40 at ~18+ commits
    score += min(30, additions / 80.0 * 30)  # up to 30 at ~2400 lines
    score += min(20, active_days / span_days * 20)  # consistency
    score += min(10, (prs * 2 + issues_closed) * 1.2)  # pull-through
    return round(min(100.0, score), 1)


def update_daily_metrics(owner) -> None:
    """Refresh DailyMetric rows from raw commits/PRs for the last N days."""
    today = date.today()
    for day in daterange(today - timedelta(days=60), today):
        commits = Commit.objects.filter(owner=owner, date__date=day)
        daily = commits.aggregate(add=Sum("additions"), dele=Sum("deletions")) or {}
        prs = PullRequest.objects.filter(owner=owner, state="merged", closed_at__date=day).count()
        issues = Issue.objects.filter(owner=owner, state="closed", closed_at__date=day).count()
        active_repos = commits.values("repository").distinct().count()
        metric, _ = DailyMetric.objects.update_or_create(
            owner=owner,
            date=day,
            defaults={
                "commits": commits.count(),
                "additions": daily["add"] or 0,
                "deletions": daily["dele"] or 0,
                "prs_merged": prs,
                "issues_closed": issues,
                "active_repos": active_repos,
                "coding_hours": round(commits.count() * 0.25, 1),  # ~15 min per commit
                "productivity_score": compute_productivity_score(owner, day, day),
            },
        )


# ── Repository health ──────────────────────────────────────────────────────
def refresh_repo_status(owner) -> None:
    """Recompute each repository's status from its last commit date."""
    for repo in Repository.objects.filter(owner=owner):
        days = repo.last_commit_days
        if days is None:
            repo.status = "at_risk"
        elif days <= ACTIVE_DAYS:
            repo.status = "active"
        elif days <= STALE_DAYS:
            repo.status = "at_risk"
        else:
            repo.status = "inactive"
        repo.save(update_fields=["status"])


def at_risk_repositories(owner) -> list[dict]:
    """Repositories that need attention: stale or inactive, or bloated PR backlog."""
    refresh_repo_status(owner)
    repos = []
    for repo in Repository.objects.filter(owner=owner):
        days = repo.last_commit_days
        status = repo.status
        if status in ("at_risk", "inactive") or repo.open_prs > 3:
            repos.append(
                {
                    "id": str(repo.id),
                    "name": repo.full_name,
                    "status": status,
                    "last_commit_days": days,
                    "open_prs": repo.open_prs,
                    "open_issues": repo.open_issues,
                    "language": repo.language,
                }
            )
    repos.sort(key=lambda r: (r["status"] != "inactive", -(r["last_commit_days"] or 0)))
    return repos


# ── Weekly analytics ───────────────────────────────────────────────────────
def _repo_weekly(owner, start: date, end: date) -> list[dict]:
    """Per-repo weekly summary. Every repository is included (zero-filled), so
    the dashboard shows health for inactive repos even when they had no commits
    during the window."""
    repos = {r: 0 for r in Repository.objects.filter(owner=owner)}
    commit_rows = (
        Commit.objects.filter(owner=owner, date__date__gte=start, date__date__lte=end)
        .values("repository__name")
        .annotate(commits=Count("id"), additions=Sum("additions"))
    )
    prs = (
        PullRequest.objects.filter(owner=owner, state="merged", closed_at__date__gte=start, closed_at__date__lte=end)
        .values("repository__name")
        .annotate(merged=Count("id"))
    )
    prs_by_repo = {row["repository__name"]: row["merged"] for row in prs}
    commit_by_repo = {row["repository__name"]: row for row in commit_rows}

    result = []
    for repo in repos:
        row = commit_by_repo.get(repo.name, {})
        result.append(
            {
                "name": repo.full_name,
                "language": repo.language,
                "commits": row.get("commits", 0),
                "additions": row.get("additions") or 0,
                "prs_merged": prs_by_repo.get(repo.name, 0),
                "status": repo.status,
                "last_commit_days": repo.last_commit_days,
            }
        )
    result.sort(key=lambda r: r["commits"], reverse=True)
    return result


def weekly_analytics(owner, weeks: int = 8) -> dict:
    """Time-series + per-repo summary for the dashboard charts."""
    today = date.today()
    start = start_of_week(today) - timedelta(days=7 * max(weeks - 1, 1))
    end = today

    daily = (
        DailyMetric.objects.filter(owner=owner, date__gte=start, date__lte=end)
        .order_by("date")
        .values("date", "commits", "additions", "prs_merged", "issues_closed", "productivity_score", "coding_hours")
    )
    daily_series = [dict(row) for row in daily]
    # Fill gaps with zero rows so charts render continuous axes.
    by_date = {row["date"]: row for row in daily_series}
    padded = []
    for day in daterange(start, end):
        row = by_date.get(day, {"date": day.isoformat(), "commits": 0, "additions": 0, "prs_merged": 0, "issues_closed": 0, "productivity_score": 0, "coding_hours": 0})
        if not isinstance(row.get("date"), str):
            row = dict(row)
            row["date"] = day.isoformat()
        padded.append(row)

    period_start = start
    period_end = end
    totals = {
        "commits": sum(r["commits"] for r in daily_series),
        "additions": sum(r["additions"] for r in daily_series),
        "prs_merged": sum(r["prs_merged"] for r in daily_series),
        "issues_closed": sum(r["issues_closed"] for r in daily_series),
        "active_repos": Repository.objects.filter(owner=owner, status="active").count(),
    }
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "totals": totals,
        "productivity_score": compute_productivity_score(owner, period_start, period_end),
        "daily": padded,
        "repos": _repo_weekly(owner, period_start, period_end),
    }


def weekly_analytics_summary(owner) -> dict:
    """The GitHub agent's summary used by reports and the command router."""
    data = weekly_analytics(owner)
    insights = generate_recommendations(owner)
    data["insights"] = insights
    return data


# ── Recommendations ───────────────────────────────────────────────────────
def generate_recommendations(owner) -> list[str]:
    """Rule-based insights — the deterministic core of the agent's analysis."""
    insights: list[str] = []
    for repo in at_risk_repositories(owner):
        if repo["status"] == "inactive":
            insights.append(
                f"**{repo['name']}** has been inactive for {repo['last_commit_days']} days — "
                "archive it or schedule a maintenance pass."
            )
        elif repo["status"] == "at_risk":
            insights.append(
                f"**{repo['name']}** hasn't seen a commit in {repo['last_commit_days']} days — "
                "consider a small follow-up commit to keep momentum."
            )
        if repo["open_prs"] > 3:
            insights.append(f"**{repo['name']}** has {repo['open_prs']} open PRs — review and merge the oldest first.")

    stale_prs = PullRequest.objects.filter(owner=owner, state="open", created_at__lte=timezone.now() - timedelta(days=14)).count()
    if stale_prs:
        insights.append(f"{stale_prs} PR(s) have been open for 14+ days — block time to review them today.")

    open_issues = Issue.objects.filter(owner=owner, state="open").count()
    closed_ratio = _issue_closure_rate(owner)
    if open_issues > 20:
        insights.append(f"{open_issues} open issues across your repos — triage by label to avoid backlog growth.")
    if closed_ratio is not None and closed_ratio < 0.5:
        insights.append("Issue closure rate is under 50% — focus on closing older issues before opening new ones.")

    recent = Commit.objects.filter(owner=owner, date__gte=timezone.now() - timedelta(days=7)).count()
    if recent == 0:
        insights.append("No commits this week. Even a small refactor keeps your streak and productivity score healthy.")

    return insights or ["Solid week — no repos need attention."]


def _issue_closure_rate(owner) -> float | None:
    closed = Issue.objects.filter(owner=owner, state="closed").count()
    total = closed + Issue.objects.filter(owner=owner, state="open").count()
    return closed / total if total else None


def save_insights(owner, texts: list[str]) -> None:
    """Persist generated insights (idempotent-ish: clears then re-adds)."""
    GithubInsight.objects.filter(owner=owner).delete()
    for text in texts:
        severity = "critical" if "inactive" in text or "no commits" in text else "warning" if "14+" in text or "under 50%" in text else "info"
        GithubInsight.objects.create(owner=owner, kind="recommendation", severity=severity, text=text)


# ── Contribution graph ─────────────────────────────────────────────────────
def contribution_graph(owner, days: int = 90) -> list[dict]:
    """Per-day commit counts for the contribution heatmap."""
    start = date.today() - timedelta(days=days)
    rows = (
        Commit.objects.filter(owner=owner, date__date__gte=start)
        .extra(select={"day": "date(date)"})
        .values("day")
        .annotate(count=Count("id"))
    )
    by_day = {row["day"]: row["count"] for row in rows}
    return [{"date": d.isoformat(), "commits": by_day.get(d, 0)} for d in daterange(start, date.today())]
