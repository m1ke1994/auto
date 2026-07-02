from decimal import Decimal

from django.db import transaction

from subscriptions.models import SubscriptionPlan


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

DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "slug": "content-hosting-1",
        "name": "Контент и хостинг",
        "short_description": "Надёжная техническая основа и удобное управление сайтом.",
        "description": "Хостинг, резервное копирование и поддержание стабильной работы сайта.",
        "price": Decimal("1299.00"),
        "old_price": None,
        "discount_percent": 0,
        "period_months": 1,
        "duration_days": 30,
        "features": HOSTING_FEATURES,
        "recommended": False,
        "sort_order": 10,
    },
    {
        "slug": "business-analytics-1",
        "name": "Бизнес-аналитика",
        "short_description": "Данные и рекомендации для уверенного роста вашего проекта.",
        "description": "Расширенная аналитика, SEO, сравнение с конкурентами и AI-рекомендации для роста.",
        "price": Decimal("1999.00"),
        "old_price": None,
        "discount_percent": 0,
        "period_months": 1,
        "duration_days": 30,
        "features": ANALYTICS_FEATURES,
        "recommended": True,
        "sort_order": 20,
    },
    {
        "slug": "content-hosting-6",
        "name": "Контент и хостинг",
        "short_description": "Надёжная техническая основа и удобное управление сайтом.",
        "description": "Хостинг, резервное копирование и поддержание стабильной работы сайта.",
        "price": Decimal("7404.00"),
        "old_price": Decimal("7794.00"),
        "discount_percent": 5,
        "period_months": 6,
        "duration_days": 180,
        "features": HOSTING_FEATURES,
        "recommended": False,
        "sort_order": 10,
    },
    {
        "slug": "business-analytics-6",
        "name": "Бизнес-аналитика",
        "short_description": "Данные и рекомендации для уверенного роста вашего проекта.",
        "description": "Расширенная аналитика, SEO, сравнение с конкурентами и AI-рекомендации для роста.",
        "price": Decimal("11394.00"),
        "old_price": Decimal("11994.00"),
        "discount_percent": 5,
        "period_months": 6,
        "duration_days": 180,
        "features": ANALYTICS_FEATURES,
        "recommended": True,
        "sort_order": 20,
    },
    {
        "slug": "content-hosting-12",
        "name": "Контент и хостинг",
        "short_description": "Надёжная техническая основа и удобное управление сайтом.",
        "description": "Хостинг, резервное копирование и поддержание стабильной работы сайта.",
        "price": Decimal("14029.00"),
        "old_price": Decimal("15588.00"),
        "discount_percent": 10,
        "period_months": 12,
        "duration_days": 365,
        "features": HOSTING_FEATURES,
        "recommended": False,
        "sort_order": 10,
    },
    {
        "slug": "business-analytics-12",
        "name": "Бизнес-аналитика",
        "short_description": "Данные и рекомендации для уверенного роста вашего проекта.",
        "description": "Расширенная аналитика, SEO, сравнение с конкурентами и AI-рекомендации для роста.",
        "price": Decimal("21589.00"),
        "old_price": Decimal("23988.00"),
        "discount_percent": 10,
        "period_months": 12,
        "duration_days": 365,
        "features": ANALYTICS_FEATURES,
        "recommended": True,
        "sort_order": 20,
    },
]


@transaction.atomic
def seed_subscription_plans() -> tuple[int, int]:
    SubscriptionPlan.objects.filter(name__in=("1 месяц", "3 месяца", "6 месяцев")).update(
        is_active=False
    )

    created_count = 0
    updated_count = 0
    for plan_data in DEFAULT_SUBSCRIPTION_PLANS:
        slug = plan_data["slug"]
        defaults = {
            **plan_data,
            "currency": "RUB",
            "is_active": True,
        }
        defaults.pop("slug")
        _, created = SubscriptionPlan.objects.update_or_create(slug=slug, defaults=defaults)
        created_count += int(created)
        updated_count += int(not created)

    return created_count, updated_count
