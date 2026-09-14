from django.db import migrations

def designate(apps,schema_editor):
    User=apps.get_model('accounts','User')
    # These are the department-head accounts already identified in accounts.seed.
    User.objects.filter(email__in=['franklin.karanja@prolithica.com','edwin.ndiritu@prolithica.com','milele.faith@prolithica.com','grace.mwende@prolithica.com'],department__isnull=False).update(is_department_head=True)
class Migration(migrations.Migration):
    dependencies=[('accounts','0003_employee_numbers')]
    operations=[migrations.RunPython(designate,migrations.RunPython.noop)]
