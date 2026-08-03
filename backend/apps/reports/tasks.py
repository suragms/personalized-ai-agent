"""Celery tasks for the Report agent (daily/weekly schedules)."""
from celery import shared_task
from django.contrib.auth import get_user_model

from .services import generate_report

User = get_user_model()


@shared_task(name="reports.generate_daily_report")
def generate_daily_report() -> None:
    for user in User.objects.all():
        generate_report(user, period="daily")


@shared_task(name="reports.generate_weekly_report")
def generate_weekly_report() -> None:
    for user in User.objects.all():
        generate_report(user, period="weekly")
