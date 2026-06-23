from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "avatar",
                    models.ImageField(blank=True, null=True, upload_to="reviews/"),
                ),
                ("name", models.CharField(max_length=255)),
                ("event_name", models.CharField(max_length=255)),
                (
                    "rating",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "1"),
                            (2, "2"),
                            (3, "3"),
                            (4, "4"),
                            (5, "5"),
                        ]
                    ),
                ),
                ("text", models.TextField()),
                ("date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "\u041e\u0442\u0437\u044b\u0432",
                "verbose_name_plural": "\u041e\u0442\u0437\u044b\u0432\u044b",
                "ordering": ["-date", "-created_at"],
            },
        ),
    ]
