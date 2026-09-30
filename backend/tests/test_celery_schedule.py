"""Celery beat schedule integrity.

Every scheduled entry must reference a task that is actually registered with
Celery, otherwise beat would fire a name nobody listens to and the work would
silently never run.
"""
from django.conf import settings

from config.celery import app

_ALLOWED_KEYS = {"task", "schedule", "args", "kwargs", "options", "relative"}


def test_beat_schedule_is_not_empty():
    assert settings.CELERY_BEAT_SCHEDULE


def test_every_beat_entry_references_a_registered_task():
    # Simulate worker boot: the loader sends `import_modules`, which triggers
    # autodiscovery of every installed app's tasks module. A syntax/NameError
    # in ANY tasks.py would otherwise only explode at worker startup.
    app.loader.import_default_modules()
    registered = set(app.tasks)
    assert registered, "No Celery tasks registered at all"

    for entry_name, entry in settings.CELERY_BEAT_SCHEDULE.items():
        task_name = entry.get("task")
        assert task_name, f"Beat entry '{entry_name}' has no 'task'"
        assert task_name in registered, (
            f"Beat entry '{entry_name}' references '{task_name}', which is not a registered "
            f"Celery task — beat would fire it into the void."
        )
        assert "schedule" in entry, f"Beat entry '{entry_name}' has no 'schedule'"


def test_beat_entries_use_only_supported_keys():
    for entry_name, entry in settings.CELERY_BEAT_SCHEDULE.items():
        extra = set(entry) - _ALLOWED_KEYS
        assert not extra, f"Beat entry '{entry_name}' has unsupported keys: {sorted(extra)}"


def test_expected_schedules_are_present():
    """The documented recurring work must actually be scheduled."""
    tasks = {e["task"] for e in settings.CELERY_BEAT_SCHEDULE.values()}
    assert tasks == {
        "productivity.generate_morning_briefing",
        "productivity.generate_eod_wrap_up",
        "reports.generate_daily_report",
        "reports.generate_weekly_report",
        "notifications.notification_sweep",
        "github.refresh_github_analytics",
    }


def test_task_retry_policy_is_bounded():
    assert settings.CELERY_TASK_ACKS_LATE is True
    assert settings.CELERY_TASK_REJECT_ON_WORKER_LOSS is True
    assert settings.CELERY_TASK_DEFAULT_RETRY_DELAY > 0
    assert settings.CELERY_TASK_MAX_RETRIES >= 1
