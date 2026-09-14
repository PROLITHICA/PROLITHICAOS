from django.core.management.base import BaseCommand
from django.db import transaction
from apps.delivery.models import Project

class Command(BaseCommand):
    help='Reconcile the company project catalogue, preserving existing linked records.'
    @transaction.atomic
    def handle(self,*args,**options):
        names=[('PRJ-041','LIMS (legislative information system)'),('PRJ-018','PBO Workflow'),('PRJ-038','Directorate of Committees system'),('PRJ-030','Bunema billing system'),(None,'Expresscarpets'),(None,'Kienyeji Hub'),(None,'Goalhub'),(None,'Partec internal system')]
        for order,(ref,name) in enumerate(names):
            project=Project.objects.filter(ref=ref).first() if ref else Project.objects.filter(name=name).first()
            if project is None: project=Project(name=name)
            project.name=name; project.full_name=name; project.short_label=name[:60]
            project.tag_label=name[:20];project.order=order
            project.save()
        self.stdout.write(self.style.SUCCESS('Eight company projects configured. Existing assignments and delivery records preserved.'))
