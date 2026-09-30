"""Resume services: auto-update from activity, ATS scoring, versioning."""
import logging

from ai.services import generate_prose_detailed
from ai.types import AgentResult

from .models import ResumeVersion

logger = logging.getLogger("agents")

# Keywords commonly targeted by ATS systems for full-stack / AI roles.
ATS_KEYWORDS = [
    "python", "django", "react", "typescript", "javascript", "sql", "postgresql",
    "docker", "git", "rest api", "testing", "ci/cd", "aws", "agile", "problem solving",
]


# ── Build from activity ────────────────────────────────────────────────────
def _gather(owner) -> dict:
    from github.models import Repository
    from projects.models import Project

    repos = list(Repository.objects.filter(owner=owner, status="active")[:4])
    projects = list(Project.objects.filter(owner=owner).exclude(status="completed")[:4])
    profile = getattr(owner, "linkedin_profile", None)

    return {
        "full_name": owner.get_full_name() or owner.username,
        "title": "Full-Stack Developer & AI Engineer",
        "summary": profile.about if profile and profile.about else "Full-stack developer focused on building AI-powered products with Django, React, and modern DevOps.",
        "contact": {"email": owner.email, "github": f"https://github.com/{owner.github_username}" if owner.github_username else ""},
        "experience": profile.experience if profile else [],
        "projects": [
            {"name": r.name, "description": r.description, "skills": [r.language] if r.language else [], "url": r.url}
            for r in repos
        ] + [
            {"name": p.name, "description": p.description, "skills": [], "url": ""}
            for p in projects
        ],
        "skills": (profile.skills if profile and profile.skills else []) + list({r.language for r in repos if r.language}),
        "education": profile.education if profile else [],
    }


def compute_ats(data: dict) -> tuple[float, list[str]]:
    """Heuristic ATS compatibility score 0-100 + missing keywords."""
    score = 0.0
    score += 15 if data["summary"] else 0
    score += 10 if data["contact"].get("email") else 0
    score += 10 if len(data["experience"]) >= 1 else 0
    score += 15 if len(data["projects"]) >= 2 else 0
    score += 10 if len(data["skills"]) >= 8 else 0
    score += 10 if len(data["education"]) >= 1 else 0

    skills_text = " ".join(data["skills"]).lower() + " " + data["summary"].lower()
    missing = [k for k in ATS_KEYWORDS if k not in skills_text]
    present = len(ATS_KEYWORDS) - len(missing)
    score += present / len(ATS_KEYWORDS) * 30

    quantified = any(any(c.isdigit() for c in str(b)) for exp in data["experience"] for b in exp.get("bullets", []))
    score += 10 if quantified else 0
    return round(min(100.0, score), 1), missing


def _render_markdown(data: dict, ats: float) -> str:
    lines = [
        f"# {data['full_name']}",
        f"## {data['title']}",
        "",
        data["summary"],
        "",
        "## Skills",
        "",
        "- " + ", ".join(sorted(set(data["skills"]))),
        "",
        "## Experience",
        "",
    ]
    for exp in data["experience"]:
        lines.append(f"### {exp.get('title', '')} — {exp.get('company', '')}")
        lines.append(exp.get("period", ""))
        lines += [f"- {b}" for b in exp.get("bullets", [])]
    lines += ["", "## Projects", ""]
    for proj in data["projects"]:
        lines.append(f"- **{proj['name']}**: {proj['description']}")
    return "\n".join(lines)


def update_resume(owner) -> ResumeVersion:
    """Generate a new resume version from current activity."""
    data = _gather(owner)
    ats, missing = compute_ats(data)
    content = _render_markdown(data, ats)

    # Polished summary via LLM when available; otherwise the template.
    # skip_mock: the mock provider would digest the paragraph — keep the
    # curated summary unless a real provider actually rewrites it.
    polished, provenance = generate_prose_detailed(
        system="You are a resume writer. Improve this summary to be crisp and ATS-friendly. Return only the summary paragraph.",
        user=f"Summary: {data['summary']}",
        fallback=data["summary"],
        owner=owner,
        skip_mock=True,
    )
    data["summary"] = polished.strip() or data["summary"]
    logger.info("Resume summary provenance: %s", provenance)

    latest = ResumeVersion.objects.filter(owner=owner).order_by("-version_number").first()
    version = ResumeVersion.objects.create(
        owner=owner,
        version_number=(latest.version_number + 1 if latest else 1),
        full_name=data["full_name"],
        title=data["title"],
        summary=data["summary"],
        contact=data["contact"],
        experience=data["experience"],
        projects=data["projects"],
        education=data["education"],
        skills=sorted(set(data["skills"])),
        ats_score=ats,
        keywords_missing=missing,
        content=content,
    )
    return version


def latest_resume(owner) -> ResumeVersion | None:
    return ResumeVersion.objects.filter(owner=owner).order_by("-version_number").first()


def run_agent(owner) -> AgentResult:
    version = update_resume(owner)
    return AgentResult(
        agent="resume",
        status="ok",
        summary=f"v{version.version_number} · ATS {version.ats_score}",
        output=version.content,
        data={"version_number": version.version_number, "ats_score": version.ats_score, "keywords_missing": version.keywords_missing},
    )
