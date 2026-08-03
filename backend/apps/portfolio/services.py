"""Portfolio services — sync portfolio projects from GitHub activity."""
import logging

from .models import PortfolioProject, PortfolioSettings

logger = logging.getLogger("agents")


def _sync_project(owner, repo) -> PortfolioProject | None:
    """Create or update a PortfolioProject from a repository."""
    if repo.status == "inactive" and not PortfolioProject.objects.filter(owner=owner, repository=repo).exists():
        return None
    skills = list({repo.language} if repo.language else {})
    project, _ = PortfolioProject.objects.update_or_create(
        owner=owner,
        repository=repo,
        defaults={
            "name": repo.name.replace("-", " ").title(),
            "description": repo.description or f"{repo.language or 'Open-source'} project — {repo.name}",
            "skills": skills,
            "deployment_status": "live" if repo.status == "active" else "not_deployed",
            "last_release_tag": repo.releases.first().tag if repo.releases.exists() else "",
        },
    )
    return project


def refresh_portfolio(owner) -> list[PortfolioProject]:
    """Rebuild the portfolio from active repositories."""
    from github.models import Repository

    updated = []
    for repo in Repository.objects.filter(owner=owner):
        try:
            project = _sync_project(owner, repo)
            if project:
                updated.append(project)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Portfolio sync failed for %s: %s", repo, exc)
    PortfolioSettings.objects.get_or_create(owner=owner)
    return updated


def refresh_portfolio_for_repo(owner, repo, tag: str) -> None:
    project = _sync_project(owner, repo)
    if project:
        project.last_release_tag = tag
        project.save(update_fields=["last_release_tag", "updated_at"])


def run_agent(owner) -> list[PortfolioProject]:
    return refresh_portfolio(owner)
