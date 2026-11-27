from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0006_project_version")]
    operations = [
        migrations.AddField(
            model_name="projectversion", name="manifest",
            field=models.JSONField(default=dict, blank=True),
        ),
    ]
