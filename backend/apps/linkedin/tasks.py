"""Celery task for the Linkedin optimization agent (weekly)."""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="linkedin.weekly_analytics")
def weekly_analytics() -> None:
    from .agents import run_agent

    for user in User.objects.all():
        run_agent(user)
