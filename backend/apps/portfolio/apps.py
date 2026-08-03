from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portfolio"

    def ready(self) -> None:
        import portfolio.signals  # noqa: F401  (registers the release → portfolio hook)
