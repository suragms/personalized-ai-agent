"""Report agent — generates reports across all periods."""
from datetime import date

from ai.graphs import AgentGraph
from ai.types import AgentResult
from memory.services import remember_decision

from .services import PERIOD_KEYS, generate_report


def collect(state: dict) -> dict:
    owner = state["owner"]
    results = {period: generate_report(owner, period=period) for period in PERIOD_KEYS}
    return {"results": results}


def summarize(state: dict) -> dict:
    results = state["results"]
    primary = results.get("daily")
    return {
        "result": AgentResult(
            agent="reports",
            status="ok",
            summary=f"{len(results)} reports generated",
            output="\n\n---\n\n".join(r.output for r in results.values()),
            data={"generated": list(results), "daily_report_id": str(primary.data.get("report_id")) if primary else None},
        )
    }


def run_agent(owner) -> AgentResult:
    graph = AgentGraph("reports")
    graph.add_node("collect", collect)
    graph.add_node("summarize", summarize)
    graph.set_entry_point("collect")
    graph.add_edge("collect", "summarize")
    result = graph.invoke({"owner": owner})["result"]
    remember_decision(
        owner,
        f"Generated {len(result.data.get('generated', []))} reports on {date.today()}.",
        {"agent": "reports"},
    )
    return result
