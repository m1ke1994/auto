from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.sites.models import Site
from clients.models import Client
from subscriptions.access import BUSINESS_ANALYTICS_REQUIRED_MESSAGE, resolve_plan_code
from subscriptions.models import Subscription, SubscriptionPayment, SubscriptionPlan


@override_settings(ENABLE_BILLING=True)
class SubscriptionFeatureAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="feature-user@example.com",
            email="feature-user@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Feature Client", is_active=True)
        self.site = Site.objects.create(name="Feature Site", slug="feature-site", owner=self.user)
        self.content_plan = self.create_plan("content-hosting-1", "Контент и хостинг")
        self.business_plan = self.create_plan("business-analytics-1", "Бизнес-аналитика")
        self.subscription = Subscription.objects.create(
            client=self.client_obj,
            status=Subscription.Status.EXPIRED,
            paid_until=timezone.now() - timedelta(days=1),
        )
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def create_plan(self, slug, name):
        plan, _ = SubscriptionPlan.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "price": Decimal("1000.00"),
                "duration_days": 30,
                "period_months": 1,
            },
        )
        return plan

    def activate(self, plan):
        self.subscription.plan = plan
        self.subscription.status = Subscription.Status.ACTIVE
        self.subscription.paid_until = timezone.now() + timedelta(days=30)
        self.subscription.save(update_fields=("plan", "status", "paid_until", "updated_at"))

    def test_content_hosting_status_exposes_only_base_content_features(self):
        self.activate(self.content_plan)

        response = self.api.get("/api/mini/subscription/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan_code"], "content_hosting")
        self.assertEqual(response.data["plan"], "content_hosting")
        self.assertEqual(response.data["plan_details"]["id"], self.content_plan.id)
        self.assertEqual(response.data["plan_title"], "Контент и хостинг")
        self.assertTrue({"dashboard_overview", "site_edit", "leads", "notifications"}.issubset(response.data["allowed_features"]))
        self.assertNotIn("analytics", response.data["allowed_features"])
        self.assertNotIn("seo_audit", response.data["allowed_features"])

    def test_content_hosting_can_edit_site_and_open_leads_and_news(self):
        self.activate(self.content_plan)

        sections = self.api.get(f"/api/admin/my-sites/{self.site.id}/sections/")
        leads = self.api.get("/api/admin/leads/")
        news = self.api.get("/api/client/news/unread-count/")

        self.assertEqual(sections.status_code, 200)
        self.assertEqual(leads.status_code, 200)
        self.assertEqual(news.status_code, 200)

    def test_content_hosting_is_denied_business_analytics_api(self):
        self.activate(self.content_plan)

        protected_urls = (
            "/api/mini/analytics/overview/",
            "/api/mini/analytics/ai-recommendations/",
            f"/api/mini/seo/audits/?site_id={self.site.id}",
            f"/api/admin/sites/{self.site.id}/competitors/",
            "/api/mini/reports/toggle-daily/",
            f"/api/admin/my-sites/{self.site.id}/analytics/heatmap/",
            f"/api/admin/my-sites/{self.site.id}/analytics/sessions/",
            f"/api/admin/my-sites/{self.site.id}/analytics/recommendations/",
            f"/api/admin/my-sites/{self.site.id}/telegram/",
        )

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.api.get(url)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.data["detail"], BUSINESS_ANALYTICS_REQUIRED_MESSAGE)

    def test_business_analytics_has_full_access(self):
        self.activate(self.business_plan)

        status_response = self.api.get("/api/mini/subscription/status/")
        analytics_response = self.api.get("/api/mini/analytics/overview/")
        competitors_response = self.api.get(f"/api/admin/sites/{self.site.id}/competitors/")

        self.assertEqual(status_response.data["plan_code"], "business_analytics")
        self.assertEqual(status_response.data["plan"], "business_analytics")
        self.assertIn("analytics", status_response.data["allowed_features"])
        self.assertIn("competitors", status_response.data["allowed_features"])
        self.assertEqual(analytics_response.status_code, 200)
        self.assertEqual(competitors_response.status_code, 200)

    def test_user_without_active_plan_keeps_base_pages_but_not_site_edit(self):
        status_response = self.api.get("/api/mini/subscription/status/")
        sites_response = self.api.get("/api/admin/my-sites/")
        news_response = self.api.get("/api/client/news/unread-count/")
        sections_response = self.api.get(f"/api/admin/my-sites/{self.site.id}/sections/")

        self.assertEqual(status_response.data["plan_code"], None)
        self.assertIsNone(status_response.data["plan"])
        self.assertEqual(status_response.data["plan_title"], "Тариф не выбран")
        self.assertEqual(
            status_response.data["allowed_features"],
            ["dashboard_overview", "notifications", "billing"],
        )
        self.assertEqual(sites_response.status_code, 200)
        self.assertEqual(news_response.status_code, 200)
        self.assertEqual(sections_response.status_code, 403)
        self.assertEqual(sections_response.data["detail"], "Для доступа к функции подключите тариф")

    def test_active_subscription_without_plan_never_gets_full_access(self):
        self.activate(None)

        status_response = self.api.get("/api/mini/subscription/status/")
        analytics_response = self.api.get("/api/mini/analytics/overview/")

        self.assertTrue(status_response.data["access_allowed"])
        self.assertIsNone(status_response.data["plan"])
        self.assertEqual(status_response.data["plan_title"], "Тариф не выбран")
        self.assertFalse(status_response.data["is_paid"])
        self.assertEqual(
            status_response.data["allowed_features"],
            ["dashboard_overview", "notifications", "billing"],
        )
        self.assertEqual(analytics_response.status_code, 403)

    @override_settings(ENABLE_BILLING=False)
    def test_disabled_billing_does_not_bypass_content_plan_limits(self):
        self.subscription.plan = self.content_plan
        self.subscription.save(update_fields=("plan", "updated_at"))

        status_response = self.api.get("/api/mini/subscription/status/")
        analytics_response = self.api.get("/api/mini/analytics/overview/")

        self.assertTrue(status_response.data["access_allowed"])
        self.assertEqual(status_response.data["plan"], "content_hosting")
        self.assertNotIn("analytics", status_response.data["allowed_features"])
        self.assertEqual(analytics_response.status_code, 403)

    def test_unknown_active_plan_uses_safe_base_features(self):
        unknown_plan = self.create_plan("legacy-unknown", "Архивный тариф")
        self.activate(unknown_plan)

        response = self.api.get("/api/mini/subscription/status/")

        self.assertIsNone(response.data["plan"])
        self.assertEqual(
            response.data["allowed_features"],
            ["dashboard_overview", "notifications", "billing"],
        )

    def test_plan_relation_is_restored_from_successful_payment(self):
        SubscriptionPayment.objects.create(
            client=self.client_obj,
            plan=self.content_plan,
            yookassa_payment_id="successful-plan-recovery",
            status=SubscriptionPayment.Status.SUCCEEDED,
            activated_at=timezone.now(),
        )
        self.activate(None)

        response = self.api.get("/api/mini/subscription/status/")

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan_id, self.content_plan.id)
        self.assertEqual(response.data["plan"], "content_hosting")

    def test_legacy_plan_names_have_stable_codes(self):
        content_plan = self.create_plan("legacy-content", "Контент + хостинг")
        business_plan = self.create_plan("legacy-business", "Бизнес аналитика")

        self.assertEqual(resolve_plan_code(content_plan), "content_hosting")
        self.assertEqual(resolve_plan_code(business_plan), "business_analytics")
