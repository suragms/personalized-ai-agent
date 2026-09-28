from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = "Initializes the admin user with the expected login credentials."

    def handle(self, *args, **options):
        # We ensure user 'admin' exists and has password 'GHOST CHANGE' as requested.
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@localhost", "role": User.OWNER, "is_superuser": True, "is_staff": True}
        )

        admin_user.set_password("GHOST CHANGE")
        admin_user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Successfully created new 'admin' user."))
        else:
            self.stdout.write(self.style.SUCCESS("Successfully updated existing 'admin' user's password."))
