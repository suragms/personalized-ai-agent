"""Agent orchestration.

`AgentGraph` wraps LangGraph's StateGraph when it is installed and transparently
falls back to a sequential executor otherwise — so the platform runs without the
optional `langgraph` dependency. Agents declare nodes (collect → analyze →
generate → persist) and the wrapper handles execution.
"""
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("agents")

try:
    from langgraph.graph import END, StateGraph

    HAS_LANGGRAPH = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_LANGGRAPH = False

NodeFn = Callable[[dict], dict | None]

_END = "__end__"


class _FallbackGraph:
    """Sequential executor for graphs without LangGraph installed.

    Runs nodes in the order they were added, threading a shared state dict.
    Nodes returning a dict are merged into the state (partial updates).
    """

    def __init__(self, nodes: list[tuple[str, NodeFn]]):
        self._nodes = nodes

    def invoke(self, state: dict | None) -> dict:
        out = dict(state or {})
        for _, fn in self._nodes:
            result = fn(out) if fn else None
            if result:
                out.update(result)
        return out


class AgentGraph:
    """Small state-graph builder with a LangGraph back end when available."""

    def __init__(self, name: str):
        self.name = name
        self._nodes: dict[str, NodeFn] = {}
        self._edges: list[tuple[str, str]] = []
        self._entry: str | None = None

    def add_node(self, name: str, fn: NodeFn) -> AgentGraph:
        self._nodes[name] = fn
        if self._entry is None:
            self._entry = name
        return self

    def add_edge(self, source: str, target: str) -> AgentGraph:
        self._edges.append((source, target))
        return self

    def set_entry_point(self, name: str) -> AgentGraph:
        self._entry = name
        return self

    def compile(self) -> Any:
        if self._entry is None:
            raise ValueError(f"Graph '{self.name}' has no entry point.")
        if HAS_LANGGRAPH:
            graph = StateGraph(dict)

            def _merge_node(fn: NodeFn) -> NodeFn:
                # With a plain-dict schema, LangGraph *replaces* the whole state
                # with a node's return value. Nodes in this platform return only
                # their partial updates, so wrap each node to merge them into the
                # surviving state — keeping `owner` (etc.) threaded between nodes.
                def wrapped(state: dict) -> dict:
                    result = fn(dict(state)) if fn else None
                    if not result:
                        return state
                    merged = dict(state)
                    merged.update(result)
                    return merged

                return wrapped

            for name, fn in self._nodes.items():
                graph.add_node(name, _merge_node(fn))
            graph.set_entry_point(self._entry)
            for src, dst in self._edges:
                if dst == _END:
                    graph.add_edge(src, END)
                elif dst in self._nodes:
                    graph.add_edge(src, dst)
            try:
                return graph.compile()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("LangGraph compile failed (%s); using fallback executor.", exc)
        nodes = [(name, fn) for name, fn in self._nodes.items()]
        return _FallbackGraph(nodes)

    def invoke(self, initial_state: dict | None = None) -> dict:
        return self.compile().invoke(initial_state or {})
