"""Celery tasks for the Daily Productivity agent."""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .services import generate_eod, generate_morning

User = get_user_model()
logger = logging.getLogger("productivity")


def _run_for_users(fn, **kwargs) -> dict:
    """Run a generator for every user, isolating per-user failures.

    One user's failure never aborts the sweep, and every failure is logged so
    tasks cannot fail silently.
    """
    results = {}
    for user in User.objects.all():
        try:
            fn(user, **kwargs)
            results[user.username] = "ok"
        except Exception:
            logger.exception("Task %s failed for user %s", fn.__name__, user.username)
            results[user.username] = "error"
    return results


@shared_task(name="productivity.generate_morning_briefing", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def generate_morning_briefing() -> dict:
    return _run_for_users(generate_morning)


@shared_task(name="productivity.generate_eod_wrap_up", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def generate_eod_wrap_up() -> dict:
    return _run_for_users(generate_eod)
