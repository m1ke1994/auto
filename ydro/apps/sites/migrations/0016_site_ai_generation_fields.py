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
                    ("not_started", "Не запущена"),
                    ("pending", "Ожидает"),
                    ("queued", "В очереди"),
                    ("analyzing", "Анализ"),
                    ("running", "Выполняется"),
                    ("generating_structure", "Генерация структуры"),
                    ("saving_sections", "Сохранение секций"),
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
            field=models.CharField(blank=True, default="", max_length=500, verbose_name="Ошибка генерации"),
        ),
        migrations.AddField(
            model_name="site",
            name="design_preset",
            field=models.CharField(
                choices=[
                    ("premium-glass", "Premium Glass"),
                    ("clean-business", "Clean Business"),
                    ("modern-dark", "Modern Dark"),
                    ("warm-nature", "Warm Nature"),
                    ("minimal-light", "Minimal Light"),
                ],
                default="clean-business",
                max_length=64,
                verbose_name="Дизайн-пресет",
            ),
        ),
        migrations.AddField(
            model_name="site",
            name="generation_job_id",
            field=models.UUIDField(blank=True, db_index=True, null=True, verbose_name="ID задачи генерации"),
        ),
        migrations.AddField(
            model_name="site",
            name="generation_started_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Генерация начата"),
        ),
        migrations.AddField(
            model_name="site",
            name="generation_completed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Генерация завершена"),
        ),
    ]
