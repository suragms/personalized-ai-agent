"""Daily Productivity agent — generates the morning briefing and EOD wrap-up."""
from ai.graphs import AgentGraph
from ai.types import AgentResult

from .services import generate_eod, generate_morning


def collect(state: dict) -> dict:
    owner = state["owner"]
    return {"morning": generate_morning(owner), "eod": generate_eod(owner)}


def summarize(state: dict) -> dict:
    morning, eod = state["morning"], state["eod"]
    return {
        "result": AgentResult(
            agent="productivity",
            status="ok",
            summary=f"Briefing ready · score {eod.data.get('productivity_score', '—')}",
            output=f"{morning.content}\n\n---\n\n{eod.content}",
            data={"morning": morning.data, "eod": eod.data},
        )
    }


def run_agent(owner) -> AgentResult:
    graph = AgentGraph("productivity")
    graph.add_node("collect", collect)
    graph.add_node("summarize", summarize)
    graph.set_entry_point("collect")
    graph.add_edge("collect", "summarize")
    return graph.invoke({"owner": owner})["result"]
