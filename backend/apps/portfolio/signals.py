"""Signal wiring: whenever a GitHub release is created, refresh the portfolio."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger("portfolio")


@receiver(post_save, sender="github.Release")
def on_release_created(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from .services import refresh_portfolio_for_repo

        refresh_portfolio_for_repo(instance.owner, instance.repository, instance.tag)
    except Exception as exc:  # pragma: no cover - never block a release save
        logger.warning("Portfolio refresh on release failed: %s", exc)
