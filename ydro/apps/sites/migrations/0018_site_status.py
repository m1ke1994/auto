from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0017_site_builder"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="source",
            field=models.CharField(
                choices=[
                    ("legacy", "Legacy"),
                    ("manual", "Manual"),
                    ("ai_generated", "AI generated"),
                    ("connected", "Connected"),
                    ("template", "Template"),
                ],
                default="manual",
                max_length=32,
                verbose_name="Источник создания",
            ),
        ),
        migrations.AddField(
            model_name="site",
            name="render_mode",
            field=models.CharField(
                choices=[("legacy", "Legacy"), ("section_builder", "Section builder"), ("builder", "Builder")],
                default="builder",
                max_length=32,
                verbose_name="Режим рендера",
            ),
        ),
        migrations.AddField(
            model_name="site",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Черновик"),
                    ("active", "Активен"),
                    ("generating", "Генерируется"),
                    ("ready", "Готов"),
                    ("published", "Опубликован"),
                    ("suspended", "Приостановлен"),
                    ("failed", "Ошибка"),
                ],
                default="draft",
                max_length=32,
                verbose_name="Статус",
            ),
        ),
    ]
