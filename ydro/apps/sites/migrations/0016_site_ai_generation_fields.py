import django.core.validators
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
        migrations.AddField(
            model_name="site",
            name="generation_progress",
            field=models.PositiveSmallIntegerField(
                default=0,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name="Прогресс генерации",
            ),
        ),
        migrations.AddField(
            model_name="site",
            name="generation_error",
            field=models.TextField(blank=True, default="", verbose_name="Ошибка генерации"),
        ),
    ]
