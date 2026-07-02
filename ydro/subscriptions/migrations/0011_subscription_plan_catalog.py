from decimal import Decimal

from django.db import migrations, models
from django.utils.text import slugify


HOSTING_FEATURES = [
    "Хостинг сайта",
    "Управление контентом",
    "Резервное копирование",
    "Поддержание работоспособности сайта",
]

ANALYTICS_FEATURES = [
    "Сравнение конкурента с вашим сайтом",
    "Подключение Telegram",
    "Расширенная аналитика сайта",
    "Возможности роста сайта",
    "SEO-аналитика сайта",
    "AI-рекомендации",
    "Управление контентом",
]

PLANS = [
    ("content-hosting-1", "Контент и хостинг", 1, 30, "1299.00", None, 0, HOSTING_FEATURES, False, 10),
    ("business-analytics-1", "Бизнес-аналитика", 1, 30, "1999.00", None, 0, ANALYTICS_FEATURES, True, 20),
    ("content-hosting-6", "Контент и хостинг", 6, 180, "7404.00", "7794.00", 5, HOSTING_FEATURES, False, 10),
    ("business-analytics-6", "Бизнес-аналитика", 6, 180, "11394.00", "11994.00", 5, ANALYTICS_FEATURES, True, 20),
    ("content-hosting-12", "Контент и хостинг", 12, 365, "14029.00", "15588.00", 10, HOSTING_FEATURES, False, 10),
    ("business-analytics-12", "Бизнес-аналитика", 12, 365, "21589.00", "23988.00", 10, ANALYTICS_FEATURES, True, 20),
]


def populate_catalog(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")

    used_slugs = set()
    for plan in SubscriptionPlan.objects.order_by("id"):
        base = slugify(f"{plan.name}-{plan.duration_days}") or f"legacy-plan-{plan.pk}"
        slug = base
        suffix = 2
        while slug in used_slugs:
            slug = f"{base}-{suffix}"
            suffix += 1
        plan.slug = slug
        plan.period_months = max(1, round(plan.duration_days / 30))
        plan.save(update_fields=["slug", "period_months"])
        used_slugs.add(slug)

    SubscriptionPlan.objects.filter(name__in=("1 месяц", "3 месяца", "6 месяцев")).update(
        is_active=False
    )

    short_descriptions = {
        "Контент и хостинг": "Надёжная техническая основа и удобное управление сайтом.",
        "Бизнес-аналитика": "Данные и рекомендации для уверенного роста вашего проекта.",
    }
    full_descriptions = {
        "Контент и хостинг": "Хостинг, резервное копирование и поддержание стабильной работы сайта.",
        "Бизнес-аналитика": "Расширенная аналитика, SEO, сравнение с конкурентами и AI-рекомендации для роста.",
    }

    for slug, name, months, days, price, old_price, discount, features, recommended, order in PLANS:
        SubscriptionPlan.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "short_description": short_descriptions[name],
                "description": full_descriptions[name],
                "price": Decimal(price),
                "old_price": Decimal(old_price) if old_price else None,
                "discount_percent": discount,
                "currency": "RUB",
                "period_months": months,
                "duration_days": days,
                "features": features,
                "recommended": recommended,
                "is_active": True,
                "sort_order": order,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0010_subscription_plan_presentation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscriptionplan",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="short_description",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="discount_percent",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="period_months",
            field=models.PositiveSmallIntegerField(db_index=True, default=1),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="sort_order",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterModelOptions(
            name="subscriptionplan",
            options={
                "ordering": ("period_months", "sort_order", "price"),
                "verbose_name": "Тариф",
                "verbose_name_plural": "Тарифы",
            },
        ),
        migrations.RunPython(populate_catalog, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="subscriptionplan",
            name="slug",
            field=models.SlugField(max_length=160, unique=True),
        ),
    ]
