"""Populate Prolithica OS with the company's recorded position.

Idempotent: run it as often as you like. Apps seed in dependency order so that
records which hang off another app's records can find their parent.
"""
import importlib

from django.core.management.base import BaseCommand
from django.db import transaction

ORDER = [
    "accounts", "crm", "delivery", "finance", "knowledge", "secretariat", "documents", "core",
]


class Command(BaseCommand):
    help = "Seed every app with the company's recorded position."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only", nargs="*", choices=ORDER,
            help="Seed only these apps (still in dependency order).",
        )

    def handle(self, *args, **options):
        wanted = options.get("only") or ORDER
        for app in ORDER:
            if app not in wanted:
                continue
            try:
                module = importlib.import_module(f"apps.{app}.seed")
            except ModuleNotFoundError:
                self.stdout.write(self.style.WARNING(f"  {app}: no seed module, skipped"))
                continue
            with transaction.atomic():
                module.run()
            self.stdout.write(self.style.SUCCESS(f"  {app}: seeded"))
        self.stdout.write(self.style.SUCCESS("Prolithica OS is seeded."))
