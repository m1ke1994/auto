from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_categories(apps, schema_editor):
    SiteTemplateCategory = apps.get_model("sites", "SiteTemplateCategory")
    categories = [
        ("tourism", "Туризм и отдых", 10),
        ("services", "Услуги", 20),
        ("construction", "Строительство", 30),
        ("beauty", "Красота и здоровье", 40),
        ("education", "Образование", 50),
        ("restaurant", "Рестораны и кафе", 60),
        ("business", "Бизнес и IT", 70),
        ("ecommerce", "Интернет-магазины", 80),
        ("other", "Другое", 100),
    ]
    for slug, name, sort_order in categories:
        SiteTemplateCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "sort_order": sort_order, "is_active": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sites", "0015_rebrand_a_meditation_public_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteTemplateCategory",
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
                "verbose_name": "Категория шаблонов",
                "verbose_name_plural": "Категории шаблонов",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="SiteTemplate",
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
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="templates", to="sites.sitetemplatecategory", verbose_name="Категория"),
                ),
                (
                    "source_site",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="template_sources", to="sites.site", verbose_name="Исходный сайт"),
                ),
            ],
            options={
                "verbose_name": "Шаблон сайта",
                "verbose_name_plural": "Шаблоны сайтов",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="SiteTemplateCloneRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="sites.site")),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clone_requests", to="sites.sitetemplate")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="site_template_clone_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Запрос клонирования шаблона",
                "verbose_name_plural": "Запросы клонирования шаблонов",
            },
        ),
        migrations.AddConstraint(
            model_name="sitetemplateclonerequest",
            constraint=models.UniqueConstraint(fields=("user", "idempotency_key"), name="unique_site_template_clone_request"),
        ),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
