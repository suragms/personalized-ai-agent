"""Celery tasks for the Daily Productivity agent."""
from celery import shared_task
from django.contrib.auth import get_user_model

from .services import generate_eod, generate_morning

User = get_user_model()


@shared_task(name="productivity.generate_morning_briefing")
def generate_morning_briefing() -> None:
    for user in User.objects.all():
        generate_morning(user)


@shared_task(name="productivity.generate_eod_wrap_up")
def generate_eod_wrap_up() -> None:
    for user in User.objects.all():
        generate_eod(user)
