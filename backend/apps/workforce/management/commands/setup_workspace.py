from django.core.management.base import BaseCommand
from django.db import transaction

from apps.delivery.models import Project


PROJECTS = [
    ("PRJ-041", "LIMS (legislative information system)"),
    ("PRJ-018", "PBO Workflow"),
    ("PRJ-038", "Directorate of Committees system"),
    ("PRJ-030", "Bunema billing system"),
    (None, "Expresscarpets"),
    (None, "Kienyeji Hub"),
    (None, "Goalhub"),
    (None, "Partec internal system"),
]
LEGACY_NAMES = {
    "PRJ-041": "LIMS",
    "PRJ-018": "PBO System",
    "PRJ-038": "DCS System",
    "PRJ-030": "AN-PBO Data Portal",
}


class Command(BaseCommand):
    help = "Ensure the company project catalogue exists, preserving linked records."

    @transaction.atomic
    def handle(self, *args, **options):
        for order, (ref, name) in enumerate(PROJECTS):
            project = Project.objects.filter(ref=ref).first() if ref else Project.objects.filter(name=name).first()
            if project is None:
                project = Project(name=name)
                project.full_name = name
                project.short_label = name[:60]
                project.tag_label = name[:20]
                project.order = order
                project.save()
            elif project.name == LEGACY_NAMES.get(ref):
                # Rename only known starter-dataset labels; retain later company edits.
                project.name = name
                project.full_name = name
                project.short_label = name[:60]
                project.tag_label = name[:20]
                project.order = order
                project.save()
        self.stdout.write(self.style.SUCCESS("Eight company projects configured; existing project edits and linked records preserved."))
