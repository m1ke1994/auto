import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0004_project_contacts")]
    operations = [migrations.CreateModel(
        name="BlockEdit",
        fields=[
            ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ("block", models.CharField(max_length=16)),
            ("instruction", models.TextField()),
            ("base_run", models.CharField(max_length=128)),
            ("base_stage", models.CharField(max_length=80)),
            ("upgrade_motion", models.BooleanField(default=False)),
            ("decision", models.CharField(max_length=16, default="pending")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="block_edits", to="ai_builder.project")),
        ],
        options={"ordering": ["-created_at", "-id"]},
    )]
