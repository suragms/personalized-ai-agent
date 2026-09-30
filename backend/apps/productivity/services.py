"""Daily productivity services: morning briefing, EOD wrap-up, scoring."""
from datetime import date, timedelta

from django.db.models import Sum
from django.utils import timezone

from ai.services import generate_prose_detailed
from ai.types import AgentResult

from .models import Briefing, CalendarEvent, FocusSession, Task

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


# ── Helpers ────────────────────────────────────────────────────────────────
def _open_tasks(owner):
    return Task.objects.filter(owner=owner).exclude(status__in=["done", "blocked"])


def _completed_today(owner):
    today = timezone.localdate()
    return Task.objects.filter(owner=owner, status="done", completed_at__date=today)


def productivity_score(owner, day: date | None = None) -> float:
    """0-100: task completion vs. scheduled work + focus time."""
    day = day or timezone.localdate()
    completed = Task.objects.filter(owner=owner, status="done", completed_at__date=day).count()
    due = Task.objects.filter(owner=owner, due_date=day).exclude(status="done").count()
    focus_minutes = FocusSession.objects.filter(owner=owner, started_at__date=day).aggregate(s=Sum("duration_minutes"))["s"] or 0

    score = 0.0
    score += min(50, completed * 12)  # up to 50 at ~4 tasks
    score += min(25, max(0, 25 - due * 6))  # missed due dates reduce score
    score += min(25, focus_minutes / 150 * 25)  # up to 25 at ~2.5h focus
    return round(min(100.0, score), 1)


def _workload_hours(owner) -> float:
    agg = _open_tasks(owner).aggregate(s=Sum("estimated_hours"))
    return round(agg["s"] or 0.0, 1)


# ── Morning briefing ───────────────────────────────────────────────────────
def build_morning(owner) -> dict:
    """Compute the structured data behind the morning briefing."""
    today = timezone.localdate()
    week_end = today + timedelta(days=7)

    open_tasks = _open_tasks(owner)
    # Order by due date, deduplicate, and cap at 6 priorities.
    seen, top = set(), []
    for t in open_tasks.order_by("due_date"):
        if t.id not in seen:
            seen.add(t.id)
            top.append(t)
        if len(top) >= 6:
            break

    overdue = open_tasks.filter(due_date__lt=today).count()
    deadlines = list(open_tasks.filter(due_date__gte=today, due_date__lte=week_end).order_by("due_date")[:8])
    events = list(CalendarEvent.objects.filter(owner=owner, start__date=today).order_by("start"))

    risks = []
    if overdue:
        risks.append({"level": "high", "text": f"{overdue} task(s) are past due — clear these first."})
    high_priority = open_tasks.filter(priority__in=["urgent", "high"]).count()
    if high_priority >= 3:
        risks.append({"level": "medium", "text": f"{high_priority} high-priority items are open."})
    workload = _workload_hours(owner)
    if workload > 12:
        risks.append({"level": "medium", "text": f"Estimated workload is {workload}h — consider trimming scope."})
    if not risks:
        risks.append({"level": "low", "text": "No major blockers detected."})

    return {
        "date": today.isoformat(),
        "priorities": [
            {
                "id": str(t.id),
                "title": t.title,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project": t.project.name if t.project else None,
            }
            for t in top
        ],
        "deadlines": [
            {"id": str(t.id), "title": t.title, "due_date": t.due_date.isoformat(), "days_left": (t.due_date - today).days}
            for t in deadlines
        ],
        "events": [
            {"id": str(e.id), "title": e.title, "start": e.start.isoformat(), "end": e.end.isoformat(), "location": e.location}
            for e in events
        ],
        "workload_hours": workload,
        "overdue": overdue,
        "risks": risks,
        "suggested_schedule": _suggested_schedule(events),
        "focus_recommendations": ["Deep-work block 9–11am", "Review PRs after lunch", "Wrap up with a 30-min planning session"],
    }


def _suggested_schedule(events) -> list[dict]:
    """Default time-blocked schedule adjusted around today's meetings."""
    blocks = [
        {"time": "08:30–09:00", "task": "Inbox zero + daily plan"},
        {"time": "09:00–11:00", "task": "Deep work: highest priority task"},
        {"time": "11:00–11:30", "task": "Check-in / standup"},
        {"time": "11:30–13:00", "task": "Deep work #2"},
        {"time": "14:00–15:00", "task": "Code review / collaboration"},
        {"time": "15:00–16:30", "task": "Deep work #3"},
        {"time": "16:30–17:00", "task": "Email + wrap-up"},
    ]
    if events:
        blocks.insert(1, {"time": f"{events[0].start:%H:%M}–{events[0].end:%H:%M}", "task": f"📅 {events[0].title}"})
    return blocks


def generate_morning(owner) -> Briefing:
    """Build + persist the morning briefing."""
    data = build_morning(owner)
    lines = [
        f"# Morning Briefing — {date.fromisoformat(data['date']):%A, %b %d}",
        "",
        "## Today's priorities",
        "",
    ]
    if data["priorities"]:
        lines += [f"- **{p['title']}** ({p['priority']})" for p in data["priorities"]]
    else:
        lines.append("- Nothing scheduled. A good day to plan the week ahead.")

    if data["deadlines"]:
        lines += ["", "## Upcoming deadlines", ""]
        lines += [f"- {d['title']} — {d['days_left']}d left" for d in data["deadlines"]]

    if data["events"]:
        lines += ["", "## Calendar today", ""]
        lines += [f"- {e['title']} @ {e['start'][11:16]}" for e in data["events"]]

    lines += ["", "## Risk analysis", ""]
    lines += [f"- **{r['level']}**: {r['text']}" for r in data["risks"]]

    lines += ["", "## Suggested schedule", ""]
    lines += [f"- {b['time']} — {b['task']}" for b in data["suggested_schedule"]]

    template = "\n".join(lines)
    content, provenance = generate_prose_detailed(
        system="You are a personal Chief of Staff writing a concise morning briefing for a full-stack developer. Use only the supplied data.",
        user=template,
        fallback=template,
        owner=owner,
    )
    briefing, _ = Briefing.objects.update_or_create(
        owner=owner,
        kind="morning",
        date=data["date"],
        defaults={"content": content, "data": data, "provenance": provenance},
    )
    return briefing


# ── End of day ─────────────────────────────────────────────────────────────
def generate_eod(owner) -> Briefing:
    today = timezone.localdate()
    done = list(_completed_today(owner))
    pending = list(_open_tasks(owner).order_by("-priority", "due_date")[:6])
    score = productivity_score(owner)
    focus_total = FocusSession.objects.filter(owner=owner, started_at__date=today).aggregate(s=Sum("duration_minutes"))["s"] or 0

    # Simple "tomorrow's plan": top pending tasks carried forward.
    tomorrow_plan = pending[:3]

    data = {
        "date": today.isoformat(),
        "completed": [{"id": str(t.id), "title": t.title, "priority": t.priority} for t in done],
        "pending": [{"id": str(t.id), "title": t.title, "priority": t.priority, "due_date": t.due_date.isoformat() if t.due_date else None} for t in pending],
        "productivity_score": score,
        "focus_minutes": focus_total,
        "tomorrow_plan": [{"id": str(t.id), "title": t.title} for t in tomorrow_plan],
    }

    lines = [
        f"# End of Day — {today:%A, %b %d}",
        "",
        f"## Productivity score: **{score}/100**  ·  Focus: {focus_total:.0f} min",
        "",
        "## Completed today",
        "",
    ]
    lines += [f"- {t['title']}" for t in data["completed"]] or ["- Nothing completed yet."]
    lines += ["", "## Still pending", ""]
    lines += [f"- {t['title']} ({t['priority']})" for t in data["pending"]] or ["- Great — inbox zero!"]
    lines += ["", "## Tomorrow's plan", ""]
    lines += [f"- {t['title']}" for t in data["tomorrow_plan"]]

    template = "\n".join(lines)
    content, provenance = generate_prose_detailed(
        system="You are a personal Chief of Staff writing an end-of-day wrap-up. Use only the supplied data.",
        user=template,
        fallback=template,
        owner=owner,
    )
    briefing, _ = Briefing.objects.update_or_create(
        owner=owner,
        kind="eod",
        date=data["date"],
        defaults={"content": content, "data": data, "provenance": provenance},
    )
    return briefing


# ── Command-router helpers ────────────────────────────────────────────────
def today_briefing(owner) -> AgentResult:
    briefing = generate_morning(owner)
    return AgentResult(
        agent="productivity",
        status="ok",
        summary="Morning briefing",
        output=briefing.content,
        data={**briefing.data, "provenance": briefing.provenance},
    )


def eod_wrap_up(owner) -> AgentResult:
    briefing = generate_eod(owner)
    return AgentResult(
        agent="productivity",
        status="ok",
        summary="EOD wrap-up",
        output=briefing.content,
        data={**briefing.data, "provenance": briefing.provenance},
    )
