from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0009_fix_russian_verbose_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="features",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="old_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="recommended",
            field=models.BooleanField(default=False),
        ),
    ]
