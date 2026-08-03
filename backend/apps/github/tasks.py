"""Celery tasks for the GitHub agent."""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="github.refresh_github_analytics")
def refresh_github_analytics() -> dict:
    """Run the GitHub agent for every platform user (hourly beat task)."""
    from .agents import run_agent

    results = {}
    for user in User.objects.all():
        try:
            result = run_agent(user)
            results[user.username] = result.status
        except Exception:  # pragma: no cover - defensive, never kill the sweep
            results[user.username] = "error"
    return results
