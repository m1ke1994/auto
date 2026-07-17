from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_website_template_categories(apps, schema_editor):
    WebsiteTemplateCategory = apps.get_model("sites", "WebsiteTemplateCategory")
    categories = [
        ("tourism", "Туризм", 10),
        ("services", "Услуги", 20),
        ("construction", "Строительство", 30),
        ("beauty", "Красота", 40),
        ("education", "Образование", 50),
        ("restaurant", "Рестораны", 60),
        ("business", "Бизнес", 70),
        ("ecommerce", "Интернет-магазин", 80),
        ("other", "Другое", 100),
    ]
    for slug, name, sort_order in categories:
        WebsiteTemplateCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "sort_order": sort_order, "is_active": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sites", "0018_site_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebsiteTemplateCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Название")),
                ("slug", models.SlugField(max_length=80, unique=True, verbose_name="Slug")),
                ("sort_order", models.PositiveIntegerField(default=100, verbose_name="Сортировка")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Категория шаблонов сайтов",
                "verbose_name_plural": "Категории шаблонов сайтов",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="WebsiteTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Название")),
                ("slug", models.SlugField(max_length=120, unique=True, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("preview_image", models.CharField(blank=True, max_length=500, verbose_name="Preview image")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("is_featured", models.BooleanField(default=False, verbose_name="Featured")),
                ("sort_order", models.PositiveIntegerField(default=100, verbose_name="Сортировка")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="templates",
                        to="sites.websitetemplatecategory",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "source_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="website_template_sources",
                        to="sites.site",
                        verbose_name="Исходный сайт",
                    ),
                ),
            ],
            options={
                "verbose_name": "Шаблон клиентского сайта",
                "verbose_name_plural": "Шаблоны клиентских сайтов",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="WebsiteTemplateCloneRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "site",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="sites.site"),
                ),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clone_requests",
                        to="sites.websitetemplate",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="website_template_clone_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Запрос клонирования шаблона сайта",
                "verbose_name_plural": "Запросы клонирования шаблонов сайтов",
            },
        ),
        migrations.AddConstraint(
            model_name="websitetemplateclonerequest",
            constraint=models.UniqueConstraint(
                fields=("user", "idempotency_key"),
                name="unique_website_template_clone_request",
            ),
        ),
        migrations.RunPython(seed_website_template_categories, migrations.RunPython.noop),
    ]
