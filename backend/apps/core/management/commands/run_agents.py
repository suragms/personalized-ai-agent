"""Run platform agents on demand.

Usage:
    python manage.py run_agents --all
    python manage.py run_agents github productivity
"""
import logging
import sys

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("agents")


class Command(BaseCommand):
    help = "Run one or more AI agents synchronously (used for testing / cron)."

    def add_arguments(self, parser):
        parser.add_argument("agents", nargs="*", type=str, help="Agent keys, e.g. github reports")
        parser.add_argument("--all", action="store_true", help="Run every registered agent")
        parser.add_argument("--user", type=str, default="", help="Owner username (default: demo)")

    def handle(self, *args, **options):
        from accounts.models import User
        from ai.agents import AGENT_REGISTRY

        keys = options["agents"] or (list(AGENT_REGISTRY) if options["all"] else [])
        if not keys:
            self.stderr.write("No agents requested. Use --all or pass agent keys.")
            sys.exit(1)

        username = options["user"] or "demo"
        owner = User.objects.filter(username=username).first()
        if owner is None:
            self.stderr.write(f"Owner user '{username}' not found. Run `python manage.py seed_demo` first.")
            sys.exit(1)

        unknown = [k for k in keys if k not in AGENT_REGISTRY]
        if unknown:
            self.stderr.write(f"Unknown agent(s): {', '.join(unknown)}. Available: {', '.join(AGENT_REGISTRY)}")
            sys.exit(1)

        started = timezone.now()

        def ascii_safe(text: str) -> str:
            return text.encode("ascii", "replace").decode("ascii")

        for key in keys:
            self.stdout.write(f"[{timezone.now():%H:%M:%S}] -> Running agent: {key}")
            try:
                result = AGENT_REGISTRY[key](owner)
                self.stdout.write(f"    OK {result.agent} ({result.status}) - {ascii_safe(result.summary)}")
                if result.output:
                    self.stdout.write(f"      Output: {ascii_safe(result.output[:200])}")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Agent %s failed", key)
                self.stderr.write(f"    FAIL {key}: {ascii_safe(str(exc))}")

        self.stdout.write(self.style.SUCCESS(f"Done in {(timezone.now() - started).total_seconds():.1f}s"))
