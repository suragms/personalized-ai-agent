"""Celery task for the Learning agent."""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="learning.daily_suggestions")
def daily_suggestions_task() -> None:
    from .agents import run_agent

    for user in User.objects.all():
        run_agent(user)
