from django.db import migrations

def backfill(apps, schema_editor):
    User=apps.get_model('accounts','User')
    Sequence=apps.get_model('accounts','EmployeeSequence')
    for user in User.objects.order_by('-is_superuser','created_at','id'):
        if not user.employee_number:
            user.employee_number=f'EN-P{Sequence.objects.create().pk:03d}'
            user.save(update_fields=['employee_number'])

class Migration(migrations.Migration):
    dependencies=[('accounts','0002_employeesequence_user_employee_number_and_more')]
    operations=[migrations.RunPython(backfill,migrations.RunPython.noop)]
