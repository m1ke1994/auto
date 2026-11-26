from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0003_cinematic_projects")]
    operations = [migrations.AddField(model_name="project", name="contacts", field=models.JSONField(default=dict, blank=True))]
