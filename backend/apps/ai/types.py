"""Shared data types for the AI layer."""
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    """Return value of every agent runner.

    `status` is "ok" (produced output), "empty" (nothing to do), or "error".
    `output` is human-readable markdown; `data` is machine-readable JSON for
    charts and command-router responses.
    """

    agent: str
    status: str = "ok"
    summary: str = ""
    output: str = ""
    data: dict = field(default_factory=dict)


@dataclass
class CommandResult:
    intent: str
    agent: str
    matched: bool = True
    message: str = ""
    data: dict = field(default_factory=dict)
