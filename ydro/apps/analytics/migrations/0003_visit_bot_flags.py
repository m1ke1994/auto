from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0002_rename_analytics_p_visit_i_415ecc_idx_analytics_p_visit_i_619245_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="is_bot",
            field=models.BooleanField(default=False, verbose_name="Bot"),
        ),
        migrations.AddField(
            model_name="visit",
            name="bot_reason",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Bot reason"),
        ),
    ]
