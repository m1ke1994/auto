from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0015_rebrand_a_meditation_public_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="generation_status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает"),
                    ("running", "Выполняется"),
                    ("completed", "Завершена"),
                    ("failed", "Ошибка"),
                ],
                default="pending",
                max_length=32,
                verbose_name="Статус генерации",
            ),
        ),
    ]
