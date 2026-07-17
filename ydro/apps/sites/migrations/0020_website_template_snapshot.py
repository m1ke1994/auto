from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0019_website_template_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="websitetemplate",
            name="snapshot_config",
            field=models.JSONField(blank=True, default=dict, verbose_name="Снимок структуры сайта"),
        ),
        migrations.AddField(
            model_name="websitetemplate",
            name="is_published",
            field=models.BooleanField(default=False, verbose_name="Опубликован"),
        ),
    ]
