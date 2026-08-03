"""Seed the platform with realistic demo data (idempotent per user)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed realistic demo data for the demo user (all modules)."

    def handle(self, *args, **options):
        from seeds.demo import DEMO_PASSWORD, DEMO_USERNAME, seed_demo

        owner = seed_demo()
        self.stdout.write(self.style.SUCCESS(f"Seeded demo data for '{owner.username}'."))
        self.stdout.write(f"  Login:   {DEMO_USERNAME} / {DEMO_PASSWORD}")
        self.stdout.write("  Next:    python manage.py run_agents --all")
