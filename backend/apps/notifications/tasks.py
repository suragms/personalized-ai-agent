"""Celery task for the Notification agent (hourly sweep)."""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("notifications")


@shared_task(name="notifications.notification_sweep", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=3)
def notification_sweep() -> dict:
    from .services import sweep_for

    results = {}
    for user in User.objects.all():
        try:
            results[user.username] = sweep_for(user)
        except Exception:  # pragma: no cover - never kill the sweep
            logger.exception("Notification sweep failed for user %s", user.username)
            results[user.username] = -1
    return results
