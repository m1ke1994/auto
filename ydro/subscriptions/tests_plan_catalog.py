from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from subscriptions.models import SubscriptionPlan
from subscriptions.plan_catalog import DEFAULT_SUBSCRIPTION_PLANS


class SubscriptionPlanSeedTests(TestCase):
    def test_seed_creates_or_updates_six_plans_without_duplicates(self):
        SubscriptionPlan.objects.filter(slug="content-hosting-1").update(price=Decimal("1.00"))

        call_command("seed_subscription_plans", stdout=StringIO())
        call_command("seed_subscription_plans", stdout=StringIO())

        slugs = [plan["slug"] for plan in DEFAULT_SUBSCRIPTION_PLANS]
        plans = SubscriptionPlan.objects.filter(slug__in=slugs)
        self.assertEqual(plans.count(), 6)
        self.assertEqual(plans.values("slug").distinct().count(), 6)
        self.assertEqual(
            plans.get(slug="content-hosting-1").price,
            Decimal("1299.00"),
        )
        self.assertEqual(
            plans.filter(period_months=1, is_active=True).count(),
            2,
        )
        self.assertEqual(
            plans.filter(period_months=6, discount_percent=5, is_active=True).count(),
            2,
        )
        self.assertEqual(
            plans.filter(period_months=12, discount_percent=10, is_active=True).count(),
            2,
        )

    def test_seed_marks_business_analytics_as_recommended(self):
        call_command("seed_subscription_plans", stdout=StringIO())

        recommended = SubscriptionPlan.objects.filter(
            slug__startswith="business-analytics-",
            recommended=True,
        )
        self.assertEqual(recommended.count(), 3)
        self.assertTrue(all(plan.features for plan in recommended))


class SubscriptionPlanApiTests(TestCase):
    def test_api_returns_two_seeded_plans_for_each_dashboard_period(self):
        response = APIClient().get("/api/mini/subscription/plans/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 6)
        for months in (1, 6, 12):
            period_plans = [
                plan for plan in response.data
                if plan["period_months"] == months
            ]
            self.assertEqual(len(period_plans), 2)
            self.assertEqual(
                {plan["name"] for plan in period_plans},
                {"Контент и хостинг", "Бизнес-аналитика"},
            )
            self.assertTrue(all(isinstance(plan["features"], list) for plan in period_plans))

    def test_api_exposes_admin_managed_presentation_fields(self):
        response = APIClient().get("/api/mini/subscription/plans/")
        plan = response.data[0]

        self.assertTrue(
            {
                "slug",
                "short_description",
                "description",
                "old_price",
                "discount_percent",
                "period_months",
                "features",
                "recommended",
                "sort_order",
            }.issubset(plan)
        )
