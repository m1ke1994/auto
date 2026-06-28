from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0006_alter_client_options_alter_client_api_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint", models.URLField(max_length=1024, unique=True, verbose_name="Push endpoint")),
                ("p256dh", models.TextField(verbose_name="Ключ p256dh")),
                ("auth", models.TextField(verbose_name="Ключ auth")),
                ("user_agent", models.CharField(blank=True, max_length=512, verbose_name="User-Agent")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Активна")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="push_subscriptions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Push-подписка",
                "verbose_name_plural": "Push-подписки",
                "ordering": ("-updated_at",),
            },
        ),
    ]
