"""Project Performance agent — records snapshots, computes risk/prediction."""
from datetime import date

from ai.graphs import AgentGraph
from ai.services import generate_prose
from ai.types import AgentResult
from memory.services import remember_decision

from .models import Project
from .services import project_metrics, record_snapshot, risk_score


def collect(state: dict) -> dict:
    owner = state["owner"]
    return {"projects": list(Project.objects.filter(owner=owner))}


def analyze(state: dict) -> dict:
    metrics = [project_metrics(p) for p in state["projects"]]
    return {"metrics": metrics}


def generate(state: dict) -> dict:
    metrics = state["metrics"]
    lines = [f"# Project Performance — {date.today():%b %d, %Y}", ""]
    if not metrics:
        lines.append("No projects tracked yet.")
    for m in metrics:
        lines.append(
            f"## {m['name']}  —  {m['completion_pct']:.0f}% complete · risk {m['risk_score']}/100"
        )
        lines.append(f"- Velocity: {m['velocity']}%/period")
        if m["delivery"]["predicted_delivery"]:
            lines.append(f"- Predicted delivery: {m['delivery']['predicted_delivery']}")
        else:
            lines.append("- Not enough data to predict delivery yet.")
    template = "\n".join(lines)
    output = generate_prose( 
        system="You are a project manager summarizing HexaStack project health. Use only supplied data.",
        user=template,
        fallback=template,
    )
    return {"output": output}


def persist(state: dict) -> dict:
    owner = state["owner"]
    for p in state["projects"]:
        record_snapshot(p)
        remember_decision(
            owner,
            f"Project '{p.name}': {p.completion_pct:.0f}% complete, risk {risk_score(p)}/100 on {date.today()}.",
            {"agent": "projects", "project": p.name},
        )
    return {
        "result": AgentResult(
            agent="projects",
            status="ok",
            summary=f"{len(state['metrics'])} project(s) analyzed",
            output=state["output"],
            data={"projects": state["metrics"]},
        )
    }


def run_agent(owner) -> AgentResult:
    graph = AgentGraph("projects")
    graph.add_node("collect", collect)
    graph.add_node("analyze", analyze)
    graph.add_node("generate", generate)
    graph.add_node("persist", persist)
    graph.set_entry_point("collect")
    for a, b in (("collect", "analyze"), ("analyze", "generate"), ("generate", "persist")):
        graph.add_edge(a, b)
    return graph.invoke({"owner": owner})["result"]
