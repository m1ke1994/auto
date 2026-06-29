from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientprofile",
            name="company_name",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="Название компании или проекта",
            ),
        ),
    ]
