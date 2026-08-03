"""Celery task for the Project Performance agent."""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="projects.refresh_metrics")
def refresh_metrics() -> None:
    from .agents import run_agent

    for user in User.objects.all():
        run_agent(user)
