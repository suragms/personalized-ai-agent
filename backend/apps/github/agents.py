"""GitHub agent — LangGraph orchestration.

Graph: collect → analyze → generate → persist. Runs weekly analytics, computes
the productivity score, detects at-risk repositories, and persists insights and
metrics. Fully deterministic with the mock provider.
"""
from datetime import date

from ai.graphs import AgentGraph
from ai.services import generate_prose
from ai.types import AgentResult
from memory.services import remember_decision

from .models import Commit, Repository
from .services import (
    generate_recommendations,
    refresh_repo_status,
    save_insights,
    update_daily_metrics,
    weekly_analytics,
)


def collect(state: dict) -> dict:
    owner = state["owner"]
    return {
        "repos": Repository.objects.filter(owner=owner).count(),
        "commits": Commit.objects.filter(owner=owner).count(),
    }


def analyze(state: dict) -> dict:
    owner = state["owner"]
    analytics = weekly_analytics(owner)
    recommendations = generate_recommendations(owner)
    return {"analytics": analytics, "recommendations": recommendations}


def generate(state: dict) -> dict:
    analytics = state["analytics"]
    recommendations = state["recommendations"]

    lines = [
        f"# GitHub Weekly Report — {date.today():%b %d, %Y}",
        "",
        f"- **Commits:** {analytics['totals']['commits']}",
        f"- **Lines added:** {analytics['totals']['additions']:,}",
        f"- **PRs merged:** {analytics['totals']['prs_merged']}",
        f"- **Issues closed:** {analytics['totals']['issues_closed']}",
        f"- **Productivity score:** {analytics['productivity_score']}/100",
        "",
        "## Recommendations",
        "",
    ]
    lines += [f"- {r}" for r in recommendations]
    template = "\n".join(lines)

    output = generate_prose( 
        system=(
            "You are a GitHub analytics assistant. Turn the supplied metrics and "
            "recommendations into a concise weekly summary for a developer. "
            "Do not invent numbers."
        ),
        user=template,
        fallback=template,
    )
    return {"output": output}


def persist(state: dict) -> dict:
    owner = state["owner"]
    save_insights(owner, state["recommendations"])
    update_daily_metrics(owner)
    refresh_repo_status(owner)
    remember_decision(
        owner,
        f"GitHub agent run on {date.today()}: "
        f"{state['analytics']['totals']['commits']} commits, "
        f"productivity {state['analytics']['productivity_score']}.",
        {"agent": "github", "period": "weekly"},
    )
    return {
        "result": AgentResult(
            agent="github",
            status="ok",
            summary=f"{state['analytics']['totals']['commits']} commits · score {state['analytics']['productivity_score']}",
            output=state["output"],
            data=state["analytics"],
        )
    }


def run_agent(owner) -> AgentResult:
    graph = AgentGraph("github")
    graph.add_node("collect", collect)
    graph.add_node("analyze", analyze)
    graph.add_node("generate", generate)
    graph.add_node("persist", persist)
    graph.set_entry_point("collect")
    for a, b in (("collect", "analyze"), ("analyze", "generate"), ("generate", "persist")):
        graph.add_edge(a, b)
    return graph.invoke({"owner": owner})["result"]
