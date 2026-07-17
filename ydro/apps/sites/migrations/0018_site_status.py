from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0017_site_builder"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="source",
            field=models.CharField(default="manual", max_length=32, verbose_name="Источник создания"),
        ),
    ]
