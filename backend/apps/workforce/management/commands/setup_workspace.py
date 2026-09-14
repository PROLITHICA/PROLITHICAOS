from django.core.management.base import BaseCommand
from django.db import transaction

from apps.delivery.models import Project

# PRJ-041, PRJ-018, and PRJ-038 are already used by the company's
# project, dashboard and document links. The new systems get stable references
# after the existing PRJ-041 series. PRJ-030 is retained as archived history.
PROJECTS = [
    ("PRJ-041", "LIMS (legislative information system)"),
    ("PRJ-018", "PBO Workflow"),
    ("PRJ-038", "Directorate of Committees system"),
    ("PRJ-046", "Bunema billing system"),
    ("PRJ-042", "Expresscarpets"),
    ("PRJ-043", "Kienyeji Hub"),
    ("PRJ-044", "Goalhub"),
    ("PRJ-045", "Partec internal system"),
]
LEGACY_NAMES = {
    "PRJ-041": "LIMS",
    "PRJ-018": "PBO System",
    "PRJ-038": "DCS System",
}


class Command(BaseCommand):
    help = "Ensure the eight active company project records exist."

    @transaction.atomic
    def handle(self, *args, **options):
        for order, (ref, name) in enumerate(PROJECTS):
            project = Project.objects.filter(ref=ref).first()
            if project is None:
                project = Project(ref=ref, name=name)
                project.full_name = name
                project.short_label = name[:60]
                project.tag_label = name[:20]
                project.order = order
                project.save()
            elif project.name == LEGACY_NAMES.get(ref):
                # Rename only known starter labels; preserve later company edits.
                project.name = name
                project.full_name = name
                project.short_label = name[:60]
                project.tag_label = name[:20]
                project.order = order
                project.save()
        self.stdout.write(self.style.SUCCESS("Eight active company projects configured; archived history and company edits preserved."))
