"""Celery tasks for the Report agent (daily/weekly schedules)."""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .services import generate_report

User = get_user_model()
logger = logging.getLogger("reports")


def _run_for_users(period: str) -> dict:
    """Generate a report for every user, isolating per-user failures."""
    results = {}
    for user in User.objects.all():
        try:
            generate_report(user, period=period)
            results[user.username] = "ok"
        except Exception:
            logger.exception("Report generation (%s) failed for user %s", period, user.username)
            results[user.username] = "error"
    return results


@shared_task(name="reports.generate_daily_report", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def generate_daily_report() -> dict:
    return _run_for_users("daily")


@shared_task(name="reports.generate_weekly_report", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def generate_weekly_report() -> dict:
    return _run_for_users("weekly")
