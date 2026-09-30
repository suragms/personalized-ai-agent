"""Celery tasks for the Insight Engine (scheduled pipeline runs).

Per-user failures are isolated and logged — one broken account must not stop
the sweep for everyone (mirrors reports/tasks.py).
"""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("intelligence")

_RETRY = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "max_retries": 3,
}


def _run_engine(user, source_types=None) -> dict:
    from .engine import InsightEngine

    return InsightEngine(user).run(source_types=source_types)


@shared_task(name="intelligence.generate_insights", **_RETRY)
def generate_insights(user_id: int) -> dict:
    """Run the full insight pipeline for one user (idempotent)."""
    user = User.objects.get(pk=user_id)
    return _run_engine(user)


@shared_task(name="intelligence.check_freshness", **_RETRY)
def check_freshness() -> dict:
    """Sweep data-source freshness, broken connections, and overdue goals.

    Raises/keeps alerts current with dedup + cooldown (spec §15).
    """
    from .engine import InsightEngine

    results = {}
    for user in User.objects.all():
        try:
            raised = InsightEngine(user).condition_alerts()
            results[user.username] = {"alerts_raised": raised}
        except Exception:
            logger.exception("Freshness sweep failed for user %s", user.username)
            results[user.username] = {"alerts_raised": 0, "status": "error"}
    return results


@shared_task(name="intelligence.daily_intelligence", **_RETRY)
def daily_intelligence() -> dict:
    """Morning pass: run the engine, then build today's morning plan."""
    from .daily import generate_morning_plan

    results = {}
    for user in User.objects.all():
        try:
            summary = _run_engine(user)
            generate_morning_plan(user)
            results[user.username] = {"created": summary["created"], "updated": summary["updated"]}
        except Exception:
            logger.exception("Daily intelligence failed for user %s", user.username)
            results[user.username] = {"status": "error"}
    return results


@shared_task(name="intelligence.evening_review", **_RETRY)
def evening_review() -> dict:
    """Evening pass: record what happened today and what carries over."""
    from .daily import generate_evening_review

    results = {}
    for user in User.objects.all():
        try:
            generate_evening_review(user)
            results[user.username] = "ok"
        except Exception:
            logger.exception("Evening review failed for user %s", user.username)
            results[user.username] = "error"
    return results
