"""Portfolio agent — refreshes the portfolio from GitHub activity."""
from ai.graphs import AgentGraph
from ai.types import AgentResult

from .services import run_agent as _run


def collect(state: dict) -> dict:
    return {"projects": _run(state["owner"])}


def summarize(state: dict) -> dict:
    projects = state["projects"]
    return {
        "result": AgentResult(
            agent="portfolio",
            status="ok",
            summary=f"{len(projects)} project(s) refreshed",
            output="\n".join(f"- {p.name} ({p.deployment_status})" for p in projects) or "No active projects to show.",
            data={"projects": [{"name": p.name, "deployment_status": p.deployment_status, "skills": p.skills} for p in projects]},
        )
    }


def run_agent(owner):
    graph = AgentGraph("portfolio")
    graph.add_node("collect", collect)
    graph.add_node("summarize", summarize)
    graph.set_entry_point("collect")
    graph.add_edge("collect", "summarize")
    return graph.invoke({"owner": owner})["result"]
