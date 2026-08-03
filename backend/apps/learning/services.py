"""Learning services: trend-aware daily suggestions and roadmaps."""
import logging
from datetime import date

from ai.services import generate_prose
from ai.types import AgentResult

from .models import LearningRoadmap, LearningSuggestion

logger = logging.getLogger("agents")

TRENDS = [
    ("Agentic AI workflows", "trend", "LLM agents are reshaping app architecture; add to your toolchain"),
    ("pgvector + RAG patterns", "trend", "You already use pgvector — deepen retrieval strategies"),
    ("React Server Components", "docs", "Modern React 19 pattern worth mastering"),
    ("Django async views", "docs", "Parallelizes IO-bound endpoints in your backend"),
    ("Celery + Redis at scale", "tool", "Beat/queue tuning pays off on real deployments"),
    ("TypeScript strict mode", "docs", "Catches a class of runtime bugs before CI"),
    ("Docker Compose healthchecks", "docs", "Deterministic local environments for client work"),
]


def _user_stack(owner) -> list[str]:
    from github.models import Repository

    return [r.language for r in Repository.objects.filter(owner=owner).exclude(language="") if r.language]


def daily_suggestions(owner, k: int = 4) -> list[LearningSuggestion]:
    """Generate today's suggestions from active stack + trending topics."""
    stack = set(_user_stack(owner))
    today = date.today()
    existing = {s.title for s in LearningSuggestion.objects.filter(owner=owner, date=today)}

    picked = []
    for title, kind, reason in TRENDS:
        if len(picked) >= k:
            break
        if title in existing:
            continue
        suggestion = LearningSuggestion.objects.create(
            owner=owner, date=today, kind=kind, title=title, reason=reason, source="agent"
        )
        picked.append(suggestion)

    # Fill with stack-relevant docs when trends are exhausted (idempotent: skip titles already made today).
    if len(picked) < k:
        for lang in sorted(stack):
            if len(picked) >= k:
                break
            title = f"{lang} best practices"
            if title in existing:
                continue
            suggestion = LearningSuggestion.objects.create(
                owner=owner, date=today, kind="docs", title=title,
                reason=f"You work in {lang} — brush up on idiomatic patterns.", source="agent",
            )
            picked.append(suggestion)

    # Fall back to existing suggestions for today (idempotent re-runs).
    if not picked:
        picked = list(LearningSuggestion.objects.filter(owner=owner, date=today)[:k])
    return picked


def build_roadmap(owner, title: str = "Full-Stack + AI Engineer Roadmap") -> LearningRoadmap:
    stack = set(_user_stack(owner))
    items = [
        {"topic": "System design for AI apps", "resource": "LLM agents, RAG, evals", "why": "Core skill for production AI work"},
        {"topic": "Observability", "resource": "logging, metrics, tracing", "why": "You ship services; measure them"},
        {"topic": f"Deep dive: {next(iter(stack), 'Python')}", "resource": "docs + hands-on", "why": "Solidify your primary language"},
        {"topic": "Performance optimization", "resource": "query tuning, caching", "why": "Scales HexaStack client work"},
    ]
    roadmap, _ = LearningRoadmap.objects.update_or_create(
        owner=owner, title=title, defaults={"level": "intermediate", "items": items}
    )
    return roadmap


def top_trends(owner) -> list[dict]:
    return [{"title": t, "kind": k, "reason": r} for t, k, r in TRENDS]


def run_agent(owner) -> AgentResult:
    suggestions = daily_suggestions(owner)
    roadmap = build_roadmap(owner)
    lines = [f"# Learning — {date.today():%b %d}", "", "## Today's suggestions", ""]
    lines += [f"- {s.title} ({s.kind}) — {s.reason}" for s in suggestions]
    lines += ["", "## Roadmap", ""]
    lines += [f"- **{i['topic']}**: {i['resource']} — {i['why']}" for i in roadmap.items]
    template = "\n".join(lines)
    output = generate_prose(
        system="You are a learning advisor for a full-stack AI engineer. Return a concise daily learning plan using only the supplied items.",
        user=template,
        fallback=template,
    )
    return AgentResult(
        agent="learning",
        status="ok",
        summary=f"{len(suggestions)} suggestion(s) · roadmap ready",
        output=output,
        data={"suggestions": [{"title": s.title, "kind": s.kind, "reason": s.reason} for s in suggestions], "roadmap": roadmap.items},
    )
