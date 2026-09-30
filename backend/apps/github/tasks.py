"""Celery tasks for the GitHub agent."""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("github")


@shared_task(name="github.refresh_github_analytics", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def refresh_github_analytics() -> dict:
    """Run the GitHub agent for every platform user (hourly beat task)."""
    from .agents import run_agent

    results = {}
    for user in User.objects.all():
        try:
            result = run_agent(user)
            results[user.username] = result.status
        except Exception:  # pragma: no cover - defensive, never kill the sweep
            logger.exception("GitHub agent failed for user %s", user.username)
            results[user.username] = "error"
    return results
