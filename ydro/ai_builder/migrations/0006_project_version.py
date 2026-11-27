import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0005_block_edit")]
    operations = [
        migrations.CreateModel(
            name="ProjectVersion",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("number", models.PositiveIntegerField()),
                ("run_directory", models.CharField(max_length=128)),
                ("generation_stage", models.CharField(max_length=80, blank=True)),
                ("kind", models.CharField(max_length=16)),
                ("instruction", models.TextField(blank=True)),
                ("legacy", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="ai_builder.project")),
                ("block_edit", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="ai_builder.blockedit")),
                ("restored_from", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="ai_builder.projectversion")),
            ],
            options={"ordering": ["-number"]},
        ),
        migrations.AddConstraint(
            model_name="projectversion",
            constraint=models.UniqueConstraint(fields=["project", "number"], name="studio_version_project_number"),
        ),
    ]
