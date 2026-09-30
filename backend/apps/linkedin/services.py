"""LinkedIn optimization services: profile scoring, suggestions, post generation."""
import logging
from datetime import date, timedelta

from ai.services import generate_prose_detailed
from ai.types import AgentResult

from .models import LinkedInProfile, PostIdea, ProfileScore

logger = logging.getLogger("agents")

TECH_KEYWORDS = [
    "python", "django", "react", "typescript", "javascript", "node", "postgresql",
    "docker", "aws", "kubernetes", "graphql", "api", "machine learning", "ai",
    "full-stack", "frontend", "backend", "sql", "git", "ci/cd", "llm", "langchain",
]

HEADLINE_KEYWORDS = ["full-stack", "engineer", "developer", "ai", "machine learning", "backend"]

BEST_POSTING_TIMES = [
    {"window": "Tue–Thu 8–10 AM", "reason": "Highest engagement for B2B tech professionals"},
    {"window": "Wed–Tue 6–9 PM", "reason": "Strong reach in the evening scroll window"},
]


def _profile(owner) -> LinkedInProfile:
    profile, _ = LinkedInProfile.objects.get_or_create(owner=owner)
    return profile


# ── Profile scoring ────────────────────────────────────────────────────────
def compute_profile_score(owner) -> dict:
    """Heuristic 0-100 analysis: headline, about, experience, skills, keywords."""
    profile = _profile(owner)
    breakdown: dict[str, float] = {}

    h = profile.headline
    breakdown["headline"] = min(20, 12 + (6 if h and (25 <= len(h) <= 120) else 0) + (6 if any(k in h.lower() for k in HEADLINE_KEYWORDS) else 0))

    about = profile.about.lower()
    hits = [k for k in TECH_KEYWORDS if k in about]
    breakdown["about"] = round(min(25, 8 + len(profile.about) * 0.04 + len(hits) * 1.2), 1)

    # Experience: top roles with quantified bullets are weighted higher.
    quantified = sum(1 for e in profile.experience if any(str(b) for b in e.get("bullets", [])))
    breakdown["experience"] = min(25, len(profile.experience) * 6 + quantified * 3)

    skills = profile.skills
    breakdown["skills"] = min(20, len(skills) * 2.0 + (6 if len(skills) >= 10 else 0))

    density = (len(hits) / max(len(profile.about.split()), 1)) if profile.about else 0
    breakdown["keywords"] = round(min(10, density * 100 * 0.6), 1)

    score = round(min(100.0, round(sum(breakdown.values()), 1)), 1)
    return {"score": score, "breakdown": breakdown}


def generate_suggestions(owner) -> list[str]:
    profile = _profile(owner)
    breakdown = compute_profile_score(owner)["breakdown"]
    out = []
    if not profile.headline:
        out.append("Add a headline that states role + stack, e.g. 'Full-Stack Engineer · Django · React · AI'.")
    elif len(profile.headline) > 120:
        out.append("Trim your headline to under 120 characters for search visibility.")
    if len(profile.about) < 120:
        out.append("Expand About past 120 characters with outcomes and 3+ relevant keywords.")
    if len(profile.skills) < 10:
        out.append("List 10+ skills from your repositories — recruiters filter by skills.")
    if len(profile.experience) < 2:
        out.append("Add quantified bullet points to each role (e.g. 'reduced API latency 40%').")
    if breakdown["keywords"] < 6:
        out.append("Increase keyword density in About to match job descriptions.")
    return (out or ["Profile looks strong — keep it refreshed monthly as you ship new work."])[:4]


def analyze_profile(owner) -> AgentResult:
    result = compute_profile_score(owner)
    suggestions = generate_suggestions(owner)
    ProfileScore.objects.update_or_create(
        owner=owner,
        date=date.today(),
        defaults={"score": result["score"], "breakdown": result["breakdown"], "suggestions": suggestions},
    )
    lines = [f"# LinkedIn Profile — {result['score']}/100", "", "## Breakdown", ""]
    lines += [f"- **{k.replace('_', ' ').title()}:** {v:.0f}" for k, v in result["breakdown"].items()]
    lines += ["", "## Suggestions", ""]
    lines += [f"- {s}" for s in suggestions]
    return AgentResult(
        agent="linkedin",
        status="ok",
        summary=f"Profile score {result['score']}",
        output="\n".join(lines),
        data={**result, "suggestions": suggestions, "best_times": BEST_POSTING_TIMES},
    )


# ── Post generation ────────────────────────────────────────────────────────
def _recent_work(owner) -> str:
    from github.models import Commit, Release

    commits = Commit.objects.filter(owner=owner, date__gte=date.today() - timedelta(days=7))[:3]
    releases = Release.objects.filter(owner=owner)[:2]
    rows = [f"- {c.repository.name}: {c.message}" for c in commits]
    rows += [f"- Shipped {r.repository.full_name} {r.name or r.body}" for r in releases]
    return "\n".join(rows) or "- Deepened tooling and architecture work"


def generate_post(owner) -> PostIdea:
    work = _recent_work(owner)
    hashtags = ["#SoftwareEngineering", "#FullStack", "#AI", "#Productivity"]
    template = (
        f"**What shipped this week** 💡\n\n{work}\n\n"
        "Lessons I keep relearning:\n"
        "- Ship the risky parts first, polish later\n"
        "- Small, reviewable PRs beat the big-bang\n\n"
        "Curious what resonates — what shipped in your world this week?"
    )
    # skip_mock: keep the curated post unless a real provider rewrites it —
    # the mock would digest the raw work log into bullet points.
    content, provenance = generate_prose_detailed(
        system=(
            "You are a LinkedIn social strategist. Turn the developer's work log into an "
            "engaging, human post (under 200 words). Return only the post body."
        ),
        user=f"Work log:\n{work}",
        fallback=template,
        owner=owner,
        skip_mock=True,
    )
    logger.info("LinkedIn post provenance: %s", provenance)
    return PostIdea.objects.create(owner=owner, topic="Weekly progress", content=content, hashtags=hashtags, source="agent")


def best_posting_time() -> dict:
    return {"windows": BEST_POSTING_TIMES, "reason": "Based on engagement curves for B2B tech audiences."}


def run_agent(owner) -> AgentResult:
    """Full optimization pass: re-score the profile and draft a post idea."""
    analyzed = analyze_profile(owner)
    post = generate_post(owner)
    return AgentResult(
        agent="linkedin",
        status="ok",
        summary=f"Score {analyzed.data['score']} · post drafted",
        output=f"{analyzed.output}\n\n---\n\n{post.content}",
        data={**analyzed.data, "post": {"content": post.content, "hashtags": post.hashtags}},
    )
