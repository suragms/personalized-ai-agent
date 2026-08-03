"""Deterministic demo data — seeds every platform module so the dashboard is
fully populated on first run.

Run with:  python manage.py seed_demo
The dataset is reproducible (fixed random seed) and spans ~6 weeks.
"""
import random
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from accounts.models import User
from core.utils import daterange

rng = random.Random(42)

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"

REPO_SPECS = [
    {"name": "agent-platform", "full_name": "hexastack/agent-platform", "language": "Python", "description": "Multi-agent platform backend (Django, Celery, pgvector).", "active": True},
    {"name": "ai-copilot", "full_name": "hexastack/ai-copilot", "language": "TypeScript", "description": "React dashboard for the AI copilot suite.", "active": True},
    {"name": "legacy-dashboard", "full_name": "hexastack/legacy-dashboard", "language": "JavaScript", "description": "Legacy admin dashboard awaiting migration.", "active": False},
    {"name": "personal-site", "full_name": "suragdev/personal-site", "language": "TypeScript", "description": "Personal portfolio and blog.", "active": True},
]

COMMIT_MESSAGES = [
    "fix: resolve nullable serializer edge case",
    "feat: add weekly analytics endpoint",
    "refactor: extract service layer for reports",
    "test: cover productivity scoring paths",
    "feat: pgvector memory search",
    "fix: handle empty briefing gracefully",
    "perf: index daily metric lookups",
    "docs: update API reference",
    "feat: oauth github code exchange",
    "chore: bump dependencies",
    "feat: burndown chart data",
    "fix: timezone handling in EOD wrap-up",
    "refactor: command router intents",
    "test: agent registry smoke test",
    "feat: report PDF export",
    "fix: resume ATS keyword scoring",
    "feat: notification sweep dedup",
    "chore: lint and format",
    "feat: contribution heatmap",
    "fix: portfolio release signal",
]

ISSUE_TITLES = [
    "Incorrect metric on weekly chart", "Add dark mode support", "Slow query on commits list",
    "Migration fails on fresh DB", "Improve empty states", "Accessibility: keyboard nav",
    "Cache analytics responses", "Fix flaky test", "Add CSV export", "Handle offline provider gracefully",
]

PR_TITLES = [
    "feat: weekly digest endpoint", "fix: pagination on issues", "refactor: extract scoring",
    "feat: markdown reports", "chore: update CI matrix", "fix: oauth redirect handling",
    "perf: index commits by date", "feat: resume exporter", "test: snapshot assertions",
]


def _aware(day: date, hour: int = 10, minute: int = 0) -> datetime:
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


# ── GitHub ─────────────────────────────────────────────────────────────────
def _seed_github(owner) -> None:
    from github.models import Branch, Commit, Issue, PullRequest, Release, Repository

    today = date.today()
    start = today - timedelta(days=42)

    repos = {}
    for spec in REPO_SPECS:
        repo = Repository.objects.create(
            owner=owner,
            name=spec["name"],
            full_name=spec["full_name"],
            description=spec["description"],
            language=spec["language"],
            url=f"https://github.com/{spec['full_name']}",
            stars=rng.randint(2, 120),
            forks=rng.randint(1, 30),
        )
        repos[spec["name"]] = repo
        Branch.objects.create(owner=owner, repository=repo, name="main", is_default=True, commit_count=0)

    for day in daterange(start, today):
        for name, repo in repos.items():
            spec = next(s for s in REPO_SPECS if s["name"] == name)
            weekday = day.weekday()
            base = 3 if spec["active"] else 0
            # Inactive repo only committed during the first two weeks.
            if not spec["active"] and (day - start).days > 14:
                continue
            count = base if weekday < 5 else rng.randint(0, 1)
            if not spec["active"]:
                count = rng.randint(1, 2)
            for _ in range(count):
                message = rng.choice(COMMIT_MESSAGES)
                Commit.objects.create(
                    owner=owner,
                    repository=repo,
                    sha=hashlib_sha(day.isoformat() + name + message),
                    author="surag",
                    message=message,
                    date=_aware(day, rng.randint(8, 19), rng.randint(0, 59)),
                    additions=rng.randint(5, 220),
                    deletions=rng.randint(0, 120),
                    changed_files=rng.randint(1, 9),
                )
            # Track latest commit for health signals.
            last = Commit.objects.filter(repository=repo).order_by("-date").first()
            if last:
                repo.last_commit_at = last.date
                repo.save(update_fields=["last_commit_at"])

    # PRs, issues, releases sprinkled over the window.
    for i in range(26):
        repo = repos[rng.choice(["agent-platform", "ai-copilot"])]
        day = start + timedelta(days=rng.randint(0, 40))
        state = "merged" if i % 3 else "closed"
        PullRequest.objects.create(
            owner=owner, repository=repo, number=i + 1, title=rng.choice(PR_TITLES), state=state,
            author="surag", created_at=_aware(day), closed_at=_aware(day) if state == "merged" else None,
            additions=rng.randint(40, 800), deletions=rng.randint(5, 300),
        )
    for i in range(30):
        repo = repos[rng.choice(list(repos))]
        day = start + timedelta(days=rng.randint(0, 41))
        closed = i % 3 != 0
        Issue.objects.create(
            owner=owner, repository=repo, number=i + 1, title=rng.choice(ISSUE_TITLES),
            state="closed" if closed else "open",
            labels=rng.sample(["bug", "enhancement", "docs", "good first issue"], rng.randint(0, 2)),
            created_at=_aware(day), closed_at=_aware(day + timedelta(days=rng.randint(0, 5))) if closed else None,
        )
    for i in range(6):
        repo = repos[rng.choice(["agent-platform", "ai-copilot"])]
        day = start + timedelta(days=7 + i * 6)
        Release.objects.create(
            owner=owner, repository=repo, tag=f"v0.{i + 1}.0",
            name=f"Release v0.{i + 1}.0", body="Bug fixes and dashboard polish.",
            published_at=_aware(day, 16),
        )

    # Aggregate daily metrics from the raw commits.
    from github.services import update_daily_metrics

    update_daily_metrics(owner)

    # Refresh repo statuses.
    for repo in Repository.objects.filter(owner=owner):
        days = repo.last_commit_days
        repo.status = "active" if days is not None and days <= 7 else ("at_risk" if days <= 21 else "inactive")
        repo.save(update_fields=["status"])


def hashlib_sha(text: str) -> str:
    import hashlib

    return hashlib.sha1(text.encode("utf-8")).hexdigest()  # noqa: S324 (demo data only)


# ── Productivity ───────────────────────────────────────────────────────────
def _seed_productivity(owner) -> None:
    from productivity.models import Briefing, CalendarEvent, FocusSession, Task

    today = date.today()
    tasks = [
        ("Ship pgvector memory search", "done", "high", today - timedelta(days=1), 3.0),
        ("Review open PRs on agent-platform", "done", "high", today, 1.5),
        ("Prepare weekly client report", "in_progress", "high", today, 2.0),
        ("Fix burndown chart timezone bug", "todo", "medium", today + timedelta(days=1), 2.0),
        ("Draft LinkedIn post on AI agents", "todo", "medium", today + timedelta(days=2), 1.0),
        ("Update resume with new release", "todo", "low", today + timedelta(days=3), 0.5),
        ("Migrate legacy-dashboard module", "blocked", "high", today + timedelta(days=5), 6.0),
        ("Research RAG evaluation metrics", "todo", "low", today + timedelta(days=6), 2.0),
        ("Deploy agent-platform to staging", "done", "urgent", today - timedelta(days=2), 1.0),
        ("Clean up notification dedup logic", "todo", "medium", today + timedelta(days=4), 1.5),
        ("Inbox + weekly planning", "done", "low", today - timedelta(days=3), 0.5),
        ("Fix CORS for OAuth redirect", "in_progress", "urgent", today, 1.0),
    ]
    for title, status, priority, due, hours in tasks:
        completed_at = _aware(due, 17) if status == "done" else None
        Task.objects.create(
            owner=owner, title=title, status=status, priority=priority,
            due_date=due, estimated_hours=hours, completed_at=completed_at,
        )

    # Two meetings today to drive the calendar + schedule blocks.
    CalendarEvent.objects.create(owner=owner, title="Client sync — HexaStack", start=_aware(today, 9), end=_aware(today, 9, 30))
    CalendarEvent.objects.create(owner=owner, title="Sprint planning", start=_aware(today, 14), end=_aware(today, 14, 45))

    # Focus sessions over the past week.
    for i in range(7):
        day = today - timedelta(days=6 - i)
        FocusSession.objects.create(
            owner=owner, started_at=_aware(day, 9), ended_at=_aware(day, 10, 30),
            duration_minutes=90, focus_score=rng.randint(65, 95),
        )

    Briefing.objects.all().delete()


# ── Projects ───────────────────────────────────────────────────────────────
def _seed_projects(owner) -> None:
    from projects.models import Milestone, ProgressSnapshot, Project

    specs = [
        {"name": "HexaStack Agent Platform", "client": "HexaStack Solutions", "status": "active", "start": date.today() - timedelta(days=90), "end": date.today() + timedelta(days=30)},
        {"name": "Retail Analytics Suite", "client": "BrightMart", "status": "active", "start": date.today() - timedelta(days=60), "end": date.today() + timedelta(days=15)},
        {"name": "Legacy Portal Migration", "client": "NorthBank", "status": "active", "start": date.today() - timedelta(days=120), "end": date.today() - timedelta(days=5)},
        {"name": "AI Support Copilot", "client": "CloudDesk", "status": "planning", "start": date.today(), "end": date.today() + timedelta(days=60)},
    ]
    projects = []
    for i, spec in enumerate(specs):
        progress = (95, 30, 25, 85) if spec["status"] == "planning" else (75, 55, 40, 60) if i == 0 else (45, 40, 30, 50) if i == 1 else (90, 85, 70, 60)
        project = Project.objects.create(
            owner=owner, name=spec["name"], client=spec["client"], status=spec["status"],
            start_date=spec["start"], end_date=spec["end"],
            backend_pct=progress[0], frontend_pct=progress[1], testing_pct=progress[2], deployment_pct=progress[3],
            pending_bugs=rng.randint(2, 18),
        )
        projects.append(project)
        Milestone.objects.create(project=project, title="Backend complete", due_date=spec["start"] + timedelta(days=40), status="completed" if i != 2 else "pending")
        Milestone.objects.create(project=project, title="UAT sign-off", due_date=spec["end"] - timedelta(days=5), status="pending")

    # Weekly snapshots per project for burndown + velocity.
    for project in projects:
        for week in range(12):
            day = date.today() - timedelta(days=(11 - week) * 7)
            if day < project.start_date:
                continue
            base = min(project.backend_pct, project.frontend_pct)
            total = min(95, (week + 1) * (base / 12.0) + rng.randint(-3, 6))
            # Rough per-phase backfill from total progress.
            share = total / 100.0
            ProgressSnapshot.objects.create(
                project=project, date=day,
                backend_pct=int(project.backend_pct * share), frontend_pct=int(project.frontend_pct * share),
                testing_pct=int(project.testing_pct * share), deployment_pct=int(project.deployment_pct * share),
                pending_bugs=project.pending_bugs, risk_score=float(rng.randint(10, 70)),
            )


# ── LinkedIn / Resume / Learning ───────────────────────────────────────────
def _seed_linkedin(owner) -> None:
    from linkedin.models import LinkedInProfile

    LinkedInProfile.objects.update_or_create(
        owner=owner,
        defaults={
            "headline": "Full-Stack Developer & AI Engineer | Django · React · LangGraph",
            "about": "I build AI-powered platforms end-to-end — Django backends with pgvector memory, React dashboards, and LangGraph agent orchestration. Currently shipping HexaStack's multi-agent chief-of-staff platform. Passionate about developer productivity, clean architecture, and production LLM systems.",
            "location": "Remote",
            "experience": [
                {"title": "Full-Stack Developer & AI Engineer", "company": "HexaStack Solutions", "period": "2023 – Present", "bullets": ["Built a multi-agent platform serving 4 product lines", "Cut report generation time 80% with automated pipelines"]},
                {"title": "Software Engineer", "company": "Freelance", "period": "2021 – 2023", "bullets": ["Delivered 6 client projects across fintech and retail", "Reduced average API latency 40% through query tuning"]},
            ],
            "skills": ["Python", "Django", "React", "TypeScript", "PostgreSQL", "pgvector", "Docker", "Celery", "Redis", "LangGraph", "LangChain", "OpenAI", "Git", "CI/CD"],
            "education": [{"school": "B.E. Computer Science", "degree": "Bachelor's", "period": "2017 – 2021"}],
        },
    )


def _seed_resume(owner) -> None:
    from resume.models import ResumeVersion

    ResumeVersion.objects.create(
        owner=owner, version_number=1, full_name="Surag", title="Full-Stack Developer & AI Engineer",
        summary="Full-stack developer focused on AI-powered products with Django, React, and modern DevOps.",
        contact={"email": owner.email, "github": "https://github.com/suragdev"},
        experience=[
            {"title": "Full-Stack Developer & AI Engineer", "company": "HexaStack Solutions", "period": "2023 – Present",
             "bullets": ["Built a multi-agent AI platform with Django, React, and LangGraph", "Automated daily/weekly reporting, cutting report time 80%"]},
        ],
        projects=[
            {"name": "agent-platform", "description": "Multi-agent platform backend with pgvector memory"},
            {"name": "ai-copilot", "description": "React dashboard for AI copilot suite"},
        ],
        education=[{"school": "B.E. Computer Science", "degree": "Bachelor's"}],
        skills=["Python", "Django", "React", "TypeScript", "PostgreSQL", "pgvector", "Docker", "LangGraph", "OpenAI"],
        ats_score=82.0, keywords_missing=["aws", "ci/cd"],
        content="# Surag\n\nFull-Stack Developer & AI Engineer",
    )


def _seed_learning(owner) -> None:
    from learning.models import LearningItem, LearningRoadmap

    for title, kind, url in [
        ("LangGraph for Production", "course", "https://langchain-ai.github.io/langgraph/"),
        ("pgvector RAG patterns", "docs", "https://github.com/pgvector/pgvector"),
        ("React Server Components", "docs", "https://react.dev/"),
        ("Django performance tuning", "docs", "https://docs.djangoproject.com/"),
    ]:
        LearningItem.objects.create(owner=owner, kind=kind, title=title, url=url, reason="Directly improves your daily stack.", priority="high")

    LearningRoadmap.objects.create(
        owner=owner, title="Full-Stack + AI Engineer Roadmap", level="intermediate",
        items=[
            {"topic": "System design for AI apps", "resource": "agents, RAG, evals", "why": "Core skill for production AI"},
            {"topic": "Observability", "resource": "logging, tracing, metrics", "why": "You ship services; measure them"},
        ],
    )


# ── Entrypoint ─────────────────────────────────────────────────────────────
def seed_demo(owner: User | None = None) -> User:
    owner = owner or User.objects.filter(username=DEMO_USERNAME).first()
    if owner is None:
        owner = User.objects.create_user(
            username=DEMO_USERNAME, email="demo@hexastack.dev",
            password=DEMO_PASSWORD, role=User.OWNER, github_username="suragdev",
        )
    _seed_github(owner)
    _seed_productivity(owner)
    _seed_projects(owner)
    _seed_linkedin(owner)
    _seed_resume(owner)
    _seed_learning(owner)
    return owner
