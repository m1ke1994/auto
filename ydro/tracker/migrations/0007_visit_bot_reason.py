from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0006_alter_event_options_alter_pageview_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="bot_reason",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Причина определения бота"),
        ),
    ]
