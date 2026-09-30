"""Celery application configuration.

The beat schedule lives in `config.settings.CELERY_BEAT_SCHEDULE` and is loaded
from Django's settings namespace below.
"""
import logging
import os

from celery import Celery
from celery.signals import task_failure

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("agent_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logger = logging.getLogger("celery")


@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """A task must never fail silently — always report the failure."""
    name = getattr(sender, "name", repr(sender))
    logger.error("Celery task %s [%s] failed: %s", name, task_id, exception, exc_info=True)
