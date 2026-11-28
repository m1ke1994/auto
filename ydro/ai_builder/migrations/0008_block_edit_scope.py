from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_builder", "0007_version_manifest")]
    operations = [
        migrations.AlterField(model_name="blockedit", name="block", field=models.CharField(max_length=48)),
    ]
