from getpass import getpass
import sys

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import Department, Role, User


class Command(BaseCommand):
    help = "Create the first CEO account on a fresh Prolithica OS installation."

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists() or User.objects.filter(role__is_director=True).exists():
            self.stdout.write("A CEO account already exists; no account was changed.")
            return
        if not sys.stdin.isatty():
            raise CommandError("Run bootstrap_ceo in an interactive terminal to securely set the CEO email and password.")
        email = input("CEO work email: ").strip().lower()
        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError("Enter a valid work email address.") from exc
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError("That email already belongs to an account. Use the existing CEO account or resolve the account first.")
        password = getpass("Choose a CEO password: ")
        confirm = getpass("Confirm the CEO password: ")
        if password != confirm:
            raise CommandError("The passwords did not match.")
        try:
            validate_password(password, User(email=email, display_name="Company CEO"))
        except ValidationError as exc:
            raise CommandError("Choose a stronger password: " + " ".join(exc.messages)) from exc
        department, _ = Department.objects.get_or_create(
            slug="ceo", defaults={"label": "Executive office", "initials": "CEO", "home_view": "dashboard"}
        )
        role, _ = Role.objects.get_or_create(
            slug="director", defaults={"label": "Chief Executive Officer", "scope": "company", "is_director": True}
        )
        role.is_director = True
        role.scope = "company"
        role.save(update_fields=["is_director", "scope"])
        User.objects.create_superuser(
            email=email, password=password, display_name="Chief Executive Officer",
            job_title="Chief Executive Officer", department=department, role=role,
        )
        self.stdout.write(self.style.SUCCESS("CEO account created. Sign in with the email and password you entered."))
