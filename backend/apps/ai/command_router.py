"""Natural-language command router.

Maps free-text commands ("Generate today's report") to agent capabilities via a
deterministic keyword matcher, with an optional LLM classification fallback when
a real provider is configured. Every handler returns a `CommandResult` — either
executes a query against the data store or invokes an agent run.
"""
import re

from ai.types import CommandResult

# Each intent: (keywords, agent, label, handler(owner) -> (message, data))
_INTENTS: list[dict] = []


def _register(keywords: list[str], agent: str, intent: str):
    def decorator(fn):
        _INTENTS.append({"keywords": keywords, "agent": agent, "intent": intent, "handler": fn})
        return fn

    return decorator


# ── Intents ───────────────────────────────────────────────────────────────
@_register(["morning", "briefing", "today's priorities", "today priorities", "start the day"], "productivity", "morning_briefing")
def _morning(owner):
    from productivity.services import today_briefing

    briefing = today_briefing(owner)
    message = briefing.output if briefing else "No briefing could be generated."
    return message, (briefing.data if briefing else {})


@_register(["end of day", "eod", "wrap up", "wrap-up", "day wrap"], "productivity", "eod_wrap_up")
def _eod(owner):
    from productivity.services import eod_wrap_up

    result = eod_wrap_up(owner)
    return result.output, result.data


@_register(["today's report", "today report", "generate today", "daily report"], "reports", "generate_report")
def _daily_report(owner):
    from reports.services import generate_report

    result = generate_report(owner, period="daily")
    return result.output or "Daily report generated.", {"report": (result.output or "")[:500]}


@_register(["weekly report", "this week's report", "week summary"], "reports", "weekly_report")
def _weekly_report(owner):
    from reports.services import generate_report

    result = generate_report(owner, period="weekly")
    return result.output or "Weekly report generated.", {"report": (result.output or "")[:500]}


@_register(["monthly report", "month summary"], "reports", "monthly_report")
def _monthly_report(owner):
    from reports.services import generate_report

    result = generate_report(owner, period="monthly")
    return result.output or "Monthly report generated.", {"report": (result.output or "")[:500]}


@_register(["how many commits", "commits this week", "commits did i", "coding summary", "summarize today's coding", "coding productivity"], "github", "github_summary")
def _github_summary(owner):
    from github.services import weekly_analytics_summary

    data = weekly_analytics_summary(owner)
    total = data["totals"]["commits"]
    repos = len(data["repos"])
    message = (
        f"This week you made **{total} commits** across **{repos} active repo(s)** "
        f"with a productivity score of **{data['productivity_score']}/100**. "
    ) + (data["insights"][0] if data.get("insights") else "")
    return message, data


@_register(["which repository", "which repo", "needs attention", "repo needs", "inactive"], "github", "github_attention")
def _github_attention(owner):
    from github.services import at_risk_repositories

    repos = at_risk_repositories(owner)
    if not repos:
        return "All repositories look healthy — no inactive or at-risk repos detected.", {"repos": []}
    lines = [f"- **{r['name']}**: {r['status']} (last commit {r['last_commit_days']} days ago)" for r in repos]
    message = "Repositories that need attention:\n" + "\n".join(lines)
    return message, {"repos": [{"name": r["name"], "status": r["status"], "last_commit_days": r["last_commit_days"]} for r in repos]}


@_register(["project risk", "risk of", "show risk"], "projects", "project_risk")
def _project_risk(owner):
    from projects.services import risk_summary

    data = risk_summary(owner)
    if not data:
        return "No projects with risk data yet.", {}
    top = data[0]
    return f"Highest-risk project: **{top['name']}** (risk {top['risk_score']}/100). " + top.get("reason", ""), {"projects": data}


@_register(["predict delivery", "delivery date", "when will", "completion date", "finish date", "project complete"], "projects", "project_prediction")
def _project_prediction(owner):
    from projects.services import delivery_predictions

    data = delivery_predictions(owner)
    if not data:
        return "No in-flight projects to predict yet.", {}
    top = data[0]
    return (
        f"**{top['name']}** is at {top['completion_pct']:.0f}% — estimated completion "
        f"{top.get('predicted_delivery') or 'not enough data to predict'}"
        + (f" (confidence {top['confidence']}%)." if top.get("confidence") else ".")
    ), {"projects": data}


@_register(["linkedin post", "post on linkedin", "linkedin"], "linkedin", "linkedin_post")
def _linkedin_post(owner):
    from linkedin.services import generate_post

    post = generate_post(owner)
    message = f"Here's a LinkedIn post idea based on your recent work:\n\n{post.content}\n\nHashtags: {', '.join(post.hashtags)}"
    return message, {"content": post.content, "hashtags": post.hashtags}


@_register(["update my resume", "resume"], "resume", "resume_update")
def _resume(owner):
    from resume.services import update_resume

    result = update_resume(owner)
    return f"Resume updated — new version **v{result.version_number}** with ATS score {result.ats_score}/100.", {"version": result.version_number, "ats_score": result.ats_score}


@_register(["what should i learn", "learning", "learn today", "roadmap"], "learning", "learning_suggestions")
def _learning(owner):
    from learning.services import daily_suggestions

    items = daily_suggestions(owner)
    if not items:
        return "No learning suggestions right now. Check back after your GitHub data is synced.", {}
    message = "Suggested topics for today:\n" + "\n".join(f"- {i.title}" for i in items)
    return message, {"items": [{"title": i.title, "type": i.kind, "reason": i.reason} for i in items]}


@_register(["notifications", "remind me", "notify"], "notifications", "notifications")
def _notifications(owner):
    from notifications.services import recent_notifications

    items = recent_notifications(owner)
    if not items:
        return "No notifications right now.", {"notifications": []}
    message = "You have " + ", ".join(f"{i.kind} ({'read' if i.read else 'new'})" for i in items[:5])
    return message, {"notifications": [{"id": str(i.id), "kind": i.kind, "title": i.title, "read": i.read} for i in items[:10]]}


@_register(["portfolio", "update portfolio"], "portfolio", "portfolio_update")
def _portfolio(owner):
    from portfolio.services import refresh_portfolio

    result = refresh_portfolio(owner)
    return f"Portfolio refreshed — {len(result)} project(s) up to date.", {"projects": len(result)}


# ── Router ────────────────────────────────────────────────────────────────
def _normalise(text: str) -> str:
    return re.sub(r"[^\w\s'-]", "", text.lower()).strip()


def _classify_with_llm(text: str) -> dict | None:
    """Optional LLM fallback when keyword matching fails."""
    from ai.providers import get_provider

    provider = get_provider()
    if provider.name == "mock" or not provider.is_available():
        return None
    options = "\n".join(f"- {i['intent']} ({', '.join(i['keywords'][:3])})" for i in _INTENTS)
    system = "Classify the user's command into one of these intents. Reply with only the intent slug."
    user = f"Command: {text}\n\nAvailable intents:\n{options}"
    try:
        return {"intent": provider.complete(system, user, temperature=0.0).strip().lower()}
    except Exception:
        return None


def route_command(text: str, owner) -> CommandResult:
    """Route a free-text command to the matching agent capability."""
    normalised = _normalise(text)
    for intent in _INTENTS:
        if any(kw in normalised for kw in intent["keywords"]):
            try:
                message, data = intent["handler"](owner)
                return CommandResult(intent=intent["intent"], agent=intent["agent"], message=message, data=data)
            except Exception as exc:
                return CommandResult(
                    intent=intent["intent"],
                    agent=intent["agent"],
                    matched=False,
                    message=f"Ran into a problem while handling that: {exc}",
                )

    # Fallback: ask the LLM (only for real providers), otherwise list capabilities.
    if (_classified := _classify_with_llm(text)) and (lookup := next((i for i in _INTENTS if i["intent"] == _classified["intent"]), None)):
        try:
            message, data = lookup["handler"](owner)
            return CommandResult(intent=lookup["intent"], agent=lookup["agent"], message=message, data=data)
        except Exception as exc:
            return CommandResult(intent=lookup["intent"], agent=lookup["agent"], matched=False, message=str(exc))

    capabilities = ", ".join(sorted({i["intent"].replace("_", " ") for i in _INTENTS}))
    return CommandResult(
        intent="help",
        agent="assistant",
        matched=False,
        message=(
            "I can handle commands like: "
            '"Generate today\'s report", "How many commits this week?", '
            '"Which repository needs attention?", "Show project risk", '
            '"Predict delivery date", "Generate a LinkedIn post", "Update my resume".\n\n'
            f"Capabilities: {capabilities}."
        ),
    )
