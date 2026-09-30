"""Create (or update) the initial platform administrator.

DEVELOPMENT / bootstrap helper. The password must be supplied explicitly —
this command never ships a hardcoded credential.

Usage:
    python manage.py init_admin --password "$ADMIN_PASSWORD"
    python manage.py init_admin --username admin --email admin@example.com --password "..."
    python manage.py init_admin --password "..." --reset-password   # overwrite existing
"""
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Create the initial admin user. Requires an explicit --password (or ADMIN_PASSWORD env)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@localhost")
        parser.add_argument("--password", default="")
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Overwrite the password of an existing user (off by default).",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"] or os.getenv("ADMIN_PASSWORD", "")

        if not password:
            raise CommandError(
                "No password provided. Pass --password or set ADMIN_PASSWORD. "
                "Refusing to create/update an admin with a hardcoded or empty password."
            )

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("Password does not meet policy: " + "; ".join(exc.messages)) from exc

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "role": User.OWNER, "is_superuser": True, "is_staff": True},
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
            return

        if options["reset_password"]:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Reset password for existing user '{username}'."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"User '{username}' already exists; password left unchanged "
                    "(use --reset-password to overwrite)."
                )
            )
