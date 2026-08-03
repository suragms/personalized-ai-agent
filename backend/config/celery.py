"""Celery application configuration.

The beat schedule lives in `config.settings.CELERY_BEAT_SCHEDULE` and is loaded
from Django's settings namespace below.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("agent_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
