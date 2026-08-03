"""Registry of platform agents.

Each entry maps a key (used by `run_agents`, Celery, and the command router)
to a `run_agent(owner) -> AgentResult` callable. Imports are lazy to avoid
circular imports at module load time.
"""
import importlib

_AGENT_MODULES = {
    "github": ("github.agents", "run_agent"),
    "productivity": ("productivity.agents", "run_agent"),
    "projects": ("projects.agents", "run_agent"),
    "reports": ("reports.agents", "run_agent"),
    "linkedin": ("linkedin.agents", "run_agent"),
    "resume": ("resume.agents", "run_agent"),
    "portfolio": ("portfolio.agents", "run_agent"),
    "learning": ("learning.agents", "run_agent"),
    "analytics": ("analytics.agents", "run_agent"),
    "notifications": ("notifications.agents", "run_agent"),
}


def _resolve(key: str):
    module, attr = _AGENT_MODULES[key]
    return getattr(importlib.import_module(module), attr)


def run_agent(key: str, owner) -> object:
    """Invoke a registered agent by key."""
    if key not in _AGENT_MODULES:
        raise KeyError(f"Unknown agent '{key}'. Available: {', '.join(_AGENT_MODULES)}")
    return _resolve(key)(owner)


# Eagerly resolved registry for the management command and Celery.
AGENT_REGISTRY = {key: _resolve(key) for key in _AGENT_MODULES}
