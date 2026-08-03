"""Celery task for the Notification agent (hourly sweep)."""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="notifications.notification_sweep")
def notification_sweep() -> dict:
    from .services import sweep_for

    results = {}
    for user in User.objects.all():
        try:
            results[user.username] = sweep_for(user)
        except Exception:  # pragma: no cover - never kill the sweep
            results[user.username] = -1
    return results
