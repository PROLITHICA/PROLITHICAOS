from django.db import migrations


def archive_legacy_data_portal(apps, schema_editor):
    Project = apps.get_model("delivery", "Project")
    # PRJ-030 has seeded AN-PBO contracts, finances, assignments and tasks.
    # Preserve those relations and their references without claiming that record
    # as Bunema's billing project.
    Project.objects.filter(ref="PRJ-030").update(
        name="AN-PBO Data Portal",
        full_name="AN-PBO Data Portal",
        short_label="Data Portal",
        tag_label="Portal",
        is_archived=True,
    )


class Migration(migrations.Migration):
    dependencies = [("delivery", "0004_project_is_archived")]
    operations = [migrations.RunPython(archive_legacy_data_portal, migrations.RunPython.noop)]
