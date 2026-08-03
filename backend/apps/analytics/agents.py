"""Analytics agent — computes and caches cross-module analytics."""
from ai.graphs import AgentGraph

from .services import run_agent as _run


def collect(state: dict) -> dict:
    return {"result": _run(state["owner"])}


def summarize(state: dict) -> dict:
    return {"result": state["result"]}


def run_agent(owner):
    graph = AgentGraph("analytics")
    graph.add_node("collect", collect)
    graph.add_node("summarize", summarize)
    graph.set_entry_point("collect")
    graph.add_edge("collect", "summarize")
    return graph.invoke({"owner": owner})["result"]
