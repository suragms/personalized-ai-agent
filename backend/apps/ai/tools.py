from typing import Callable, Dict

TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str):
    def decorator(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return decorator

# Example safe tools
@register_tool("get_current_time")
def _get_current_time(owner, **kwargs):
    from django.utils import timezone
    return {"time": timezone.now().isoformat()}

@register_tool("read_github_events")
def _read_github_events(owner, **kwargs):
    from github.services import fetch_events
    return {"events": fetch_events(owner)}

# Legacy tools wrapper for built-in capabilities
@register_tool("morning_briefing")
def _tool_morning_briefing(owner, **kwargs):
    from productivity.services import today_briefing
    briefing = today_briefing(owner)
    message = briefing.output if briefing else "No briefing could be generated."
    return {"message": message, "data": (briefing.data if briefing else {})}

@register_tool("eod_wrap_up")
def _tool_eod_wrap_up(owner, **kwargs):
    from productivity.services import eod_wrap_up
    result = eod_wrap_up(owner)
    return {"message": result.output, "data": result.data}
@register_tool("github_summary")
def _tool_github_summary(owner, **kwargs):
    from github.services import weekly_analytics_summary
    data = weekly_analytics_summary(owner)
    total = data.get("totals", {}).get("commits", 0)
    repos = len(data.get("repos", []))
    message = (
        f"This week you made **{total} commits** across **{repos} active repo(s)**. "
    )
    return {"message": message, "data": data}

@register_tool("github_attention")
def _tool_github_attention(owner, **kwargs):
    from github.services import at_risk_repositories
    repos = at_risk_repositories(owner)
    if not repos:
        return {"message": "All repositories look healthy.", "data": {"repos": []}}
    lines = [f"- **{r['name']}**: {r['status']} (last commit {r['last_commit_days']} days ago)" for r in repos]
    message = "Repositories that need attention:\n" + "\n".join(lines)
    return {"message": message, "data": {"repos": repos}}

@register_tool("generate_report")
def _tool_generate_report(owner, **kwargs):
    from reports.services import generate_report
    result = generate_report(owner, period="daily")
    return {"message": result.output or "Daily report generated.", "data": {"report": (result.output or "")[:500]}}
