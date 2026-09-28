"""Natural-language command router.

Maps free-text commands to agent capabilities via the Skill Registry.
Each intent maps to a declarative skill in skills/<skill-id>/. The router
validates permissions and integrations before executing.
"""
import re
import logging

from .types import CommandResult
from .skills import registry as skill_registry, SkillExecutor, SkillRegistryError

logger = logging.getLogger("ai")

# Keyword → skill-id mapping. A skill id corresponds to a folder under skills/.
# The intent returned in CommandResult is the tool name the skill uses (for
# backwards-compatibility with existing tests and UI consumers).
_INTENTS: list[dict] = [
    {
        "keywords": ["morning", "briefing", "today's priorities", "today priorities", "start the day"],
        "skill_id": "morning-briefing",
        "intent": "morning_briefing",
    },
    {
        "keywords": ["end of day", "eod", "wrap up", "wrap-up", "day wrap"],
        "skill_id": "eod-wrap-up",
        "intent": "eod_wrap_up",
    },
    {
        "keywords": ["how many commits", "commits this week", "commits did i", "coding summary", "summarize today's coding", "coding productivity"],
        "skill_id": "github-summary",
        "intent": "github_summary",
    },
    {
        "keywords": ["which repository", "which repo", "needs attention", "repo needs", "inactive"],
        "skill_id": "github-attention",
        "intent": "github_attention",
    },
    {
        "keywords": ["today's report", "today report", "generate today", "daily report"],
        "skill_id": "generate-report",
        "intent": "generate_report",
    },
]


def _normalise(text: str) -> str:
    return re.sub(r"[^\w\s'-]", "", text.lower()).strip()


def route_command(text: str, owner) -> CommandResult:
    """Route a free-text command to the matching Skill."""
    # Ensure registry is loaded (idempotent — only loads when empty)
    if not skill_registry._skills:
        skill_registry.load()

    normalised = _normalise(text)
    matched = None

    for intent_def in _INTENTS:
        if any(kw in normalised for kw in intent_def["keywords"]):
            matched = intent_def
            break

    if not matched:
        return CommandResult(
            intent="help",
            agent="assistant",
            matched=False,
            message=(
                "I can handle commands like: "
                '"How many commits this week?", '
                '"Which repository needs attention?", '
                '"Generate today\'s report", '
                '"Morning briefing", "EOD wrap up".'
            ),
        )

    skill_id = matched["skill_id"]
    intent = matched["intent"]
    executor = SkillExecutor()

    try:
        result_data = executor.execute(owner, skill_id, text)
        msg = result_data.get("message", "Task completed.")
        # Expose the nested .data dict directly so callers get e.g. result.data["totals"]
        nested = result_data.get("data", result_data)
        return CommandResult(
            intent=intent,
            agent="skill",
            matched=True,
            message=msg,
            data=nested,
        )
    except SkillRegistryError as exc:
        return CommandResult(
            intent=intent,
            agent="skill",
            matched=False,
            message=f"Skill error: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error in route_command")
        return CommandResult(
            intent=intent,
            agent="skill",
            matched=False,
            message=f"An unexpected error occurred: {exc}",
        )
