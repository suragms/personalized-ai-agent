"""Celery task for the LinkedIn optimization agent (weekly)."""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("linkedin")


@shared_task(name="linkedin.weekly_analytics", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def weekly_analytics() -> None:
    from .agents import run_agent

    for user in User.objects.all():
        try:
            run_agent(user)
        except Exception:  # pragma: no cover - one user must not kill the sweep
            logger.exception("Agent failed for user %s", user.username)
