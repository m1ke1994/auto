from datetime import date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_article"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="published_date",
            field=models.DateField(default=date(2026, 2, 17), verbose_name="Дата публикации"),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="article",
            options={
                "ordering": ["-published_date", "-created_at"],
                "verbose_name": "Статья / Видео",
                "verbose_name_plural": "Статьи и видео",
            },
        ),
    ]
