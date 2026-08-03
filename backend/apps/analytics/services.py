"""Analytics services — chart-ready aggregations across all modules."""
import logging
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from ai.types import AgentResult

from .models import AnalyticsSnapshot

logger = logging.getLogger("agents")

MODULES = ["coding", "projects", "time", "learning", "linkedin", "resume", "business"]


def overview(owner) -> dict:
    """Top-level KPI summary for the dashboard Overview page."""
    from github.models import Commit, Repository
    from github.services import compute_productivity_score
    from learning.models import LearningItem
    from linkedin.models import ProfileScore
    from productivity.models import Task
    from projects.models import Project
    from projects.services import risk_score
    from resume.models import ResumeVersion

    today = date.today()
    week_start = today - timedelta(days=6)

    commits_week = Commit.objects.filter(owner=owner, date__date__gte=week_start).count()
    productivity = compute_productivity_score(owner, week_start, today)
    tasks_pending = Task.objects.filter(owner=owner).exclude(status__in=["done", "blocked"]).count()
    projects = list(Project.objects.filter(owner=owner))
    project_avg = round(sum(p.completion_pct for p in projects) / len(projects), 1) if projects else 0.0
    at_risk = sum(1 for p in projects if risk_score(p) >= 50)
    latest_linkedin = ProfileScore.objects.filter(owner=owner).order_by("-date").first()
    latest_resume = ResumeVersion.objects.filter(owner=owner).order_by("-version_number").first()
    learning_open = LearningItem.objects.filter(owner=owner, completed=False).count()

    return {
        "commits_week": commits_week,
        "productivity_score": productivity,
        "active_repos": Repository.objects.filter(owner=owner, status="active").count(),
        "tasks_pending": tasks_pending,
        "projects": len(projects),
        "project_avg_completion": project_avg,
        "projects_at_risk": at_risk,
        "linkedin_score": latest_linkedin.score if latest_linkedin else None,
        "resume_ats": latest_resume.ats_score if latest_resume else None,
        "learning_open": learning_open,
    }


def coding_analytics(owner) -> dict:
    from github.services import contribution_graph, weekly_analytics

    return {"weekly": weekly_analytics(owner), "contributions": contribution_graph(owner)}


def projects_analytics(owner) -> dict:
    from projects.models import Project
    from projects.services import project_metrics

    return {"projects": [project_metrics(p) for p in Project.objects.filter(owner=owner)]}


def time_analytics(owner) -> dict:
    from productivity.models import FocusSession

    last_14 = timezone.localdate() - timedelta(days=13)
    rows = (
        FocusSession.objects.filter(owner=owner, started_at__date__gte=last_14)
        .extra(select={"day": "date(started_at)"})
        .values("day")
        .annotate(minutes=Sum("duration_minutes"), sessions=Count("id"))
        .order_by("day")
    )
    return {"daily_focus": [dict(r) for r in rows]}


def learning_analytics(owner) -> dict:
    from learning.models import LearningItem, LearningRoadmap, LearningSuggestion

    return {
        "total": LearningItem.objects.filter(owner=owner).count(),
        "completed": LearningItem.objects.filter(owner=owner, completed=True).count(),
        "open": LearningItem.objects.filter(owner=owner, completed=False).count(),
        "recent_suggestions": LearningSuggestion.objects.filter(owner=owner)[:10].count(),
        "roadmaps": LearningRoadmap.objects.filter(owner=owner).count(),
    }


def linkedin_analytics(owner) -> dict:
    from linkedin.models import PostIdea, ProfileScore

    scores = list(ProfileScore.objects.filter(owner=owner)[:30])
    return {
        "score_history": [{"date": s.date.isoformat(), "score": s.score} for s in scores],
        "posts_generated": PostIdea.objects.filter(owner=owner).count(),
    }


def resume_analytics(owner) -> dict:
    from resume.models import ResumeVersion

    versions = list(ResumeVersion.objects.filter(owner=owner)[:10])
    return {
        "versions": [{"version": v.version_number, "ats_score": v.ats_score, "created_at": v.created_at.isoformat()} for v in versions],
        "latest_ats": versions[0].ats_score if versions else None,
    }


def business_analytics(owner) -> dict:
    """HexaStack client-business summary: projects by client and status."""
    from projects.models import Project

    projects = list(Project.objects.filter(owner=owner))
    by_client = {}
    for p in projects:
        by_client.setdefault(p.client or "Internal", []).append({"name": p.name, "completion": p.completion_pct, "status": p.status})
    return {
        "clients": by_client,
        "total_projects": len(projects),
        "active": sum(1 for p in projects if p.status == "active"),
        "completed": sum(1 for p in projects if p.status == "completed"),
    }


_ANALYZERS = {
    "coding": coding_analytics,
    "projects": projects_analytics,
    "time": time_analytics,
    "learning": learning_analytics,
    "linkedin": linkedin_analytics,
    "resume": resume_analytics,
    "business": business_analytics,
}


def module_analytics(owner, module: str) -> dict:
    if module == "overview":
        return overview(owner)
    if module not in _ANALYZERS:
        raise KeyError(f"Unknown analytics module '{module}'. Available: overview, {', '.join(MODULES)}")
    return _ANALYZERS[module](owner)


def snapshot_all(owner) -> dict:
    """Compute + cache a snapshot per module."""
    results = {}
    for module in MODULES:
        try:
            data = _ANALYZERS[module](owner)
            AnalyticsSnapshot.objects.update_or_create(
                owner=owner, module=module, date=date.today(), defaults={"data": data}
            )
            results[module] = data
        except Exception as exc:  # pragma: no cover - one failing module shouldn't sink the run
            logger.warning("Analytics module %s failed: %s", module, exc)
            results[module] = {"error": str(exc)}
    return results


def run_agent(owner) -> AgentResult:
    data = snapshot_all(owner)
    return AgentResult(
        agent="analytics",
        status="ok",
        summary=f"{len(data)} analytics modules computed",
        output="\n".join(f"- {k}: computed" for k in data),
        data=data,
    )
