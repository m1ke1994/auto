import uuid

from django.db import migrations, models


def populate_preview_tokens(apps, schema_editor):
    Project=apps.get_model("ai_builder","Project")
    for project in Project.objects.filter(preview_token__isnull=True).iterator():
        project.preview_token=uuid.uuid4()
        project.save(update_fields=["preview_token"])


class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0002_design_engine")]

    operations = [
        migrations.AddField(
            model_name="project",
            name="engine",
            field=models.CharField(
                choices=(("quick", "Quick concept"), ("cinematic", "Cinematic agent")),
                default="quick",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="generation_status",
            field=models.CharField(
                choices=(("complete", "Complete"), ("queued", "Queued"), ("running", "Running"), ("failed", "Failed")),
                default="complete",
                max_length=16,
            ),
        ),
        migrations.AddField(model_name="project", name="generation_stage", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="project", name="generation_error", field=models.TextField(blank=True)),
        migrations.AddField(model_name="project", name="run_directory", field=models.CharField(blank=True, max_length=128)),
        migrations.AddField(model_name="project", name="preview_token", field=models.UUIDField(editable=False, null=True)),
        migrations.RunPython(populate_preview_tokens,migrations.RunPython.noop),
        migrations.AlterField(model_name="project", name="preview_token", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.AddField(model_name="project", name="updated_at", field=models.DateTimeField(auto_now=True)),
    ]
