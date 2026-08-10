from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seo_audit", "0009_siteseoaudit_external_target"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteseoaudit",
            name="error_message",
            field=models.TextField(blank=True, default=""),
        ),
    ]
