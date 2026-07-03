from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from clients.models import Client
from subscriptions.models import Subscription, SubscriptionPlan


def grant_business_analytics(user, *, client=None):
    """Подготавливает бизнес-тариф для тестов защищённых продуктовых API."""
    if client is None:
        client, _ = Client.objects.get_or_create(
            owner=user,
            defaults={"name": user.email or user.username, "is_active": True},
        )
    plan, _ = SubscriptionPlan.objects.get_or_create(
        slug="business-analytics-test",
        defaults={
            "name": "Бизнес-аналитика",
            "price": Decimal("1000.00"),
            "duration_days": 30,
            "period_months": 1,
        },
    )
    subscription, _ = Subscription.objects.update_or_create(
        client=client,
        defaults={
            "plan": plan,
            "status": Subscription.Status.ACTIVE,
            "paid_until": timezone.now() + timedelta(days=30),
            "admin_override": False,
        },
    )
    return subscription
