from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from clients.models import Client
from subscriptions.models import Subscription, SubscriptionPlan

from .models import Site
from .public_renderer import inject_subscription_lock


@override_settings(ENABLE_BILLING=True, SITE_BASE_URL="https://tracknode.test", PUBLIC_SITE_STATIC_INDEX_URL="")
class PublicSiteSubscriptionLockTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("public-lock-owner", password="pass")
        self.client_account = Client.objects.create(owner=self.owner, name="Public owner")
        self.site = Site.objects.create(name="Public site", slug="public-lock-site", owner=self.owner, is_active=True)
        self.plan = SubscriptionPlan.objects.create(name="Контент и хостинг", slug="content-hosting-monthly", price=100, duration_days=30)

    def subscribe(self, paid_until):
        return Subscription.objects.create(client=self.client_account, plan=self.plan, status=Subscription.Status.ACTIVE, paid_until=paid_until)

    def test_missing_subscription_returns_html_with_lock(self):
        response = self.client.get("/api/public/sites/public-lock-site/html/")
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="tracknode-subscription-lock"', html)
        self.assertIn("Перейти в личный кабинет", html)
        self.assertIn("https://tracknode.test/login?redirect=/billing", html)
        self.assertEqual(response["X-TrackNode-Site-Status"], "suspended")
        self.assertEqual(response["X-TrackNode-Subscription-Required"], "true")

    def test_expired_subscription_returns_html_with_lock(self):
        self.subscribe(timezone.now() - timedelta(seconds=1))
        response = self.client.get("/api/public/sites/public-lock-site/html/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tracknode-subscription-lock")

    def test_active_subscription_returns_html_without_lock(self):
        self.subscribe(timezone.now() + timedelta(days=30))
        response = self.client.get("/api/public/sites/public-lock-site/html/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "tracknode-subscription-lock")
        self.assertEqual(response["X-TrackNode-Site-Status"], "active")
        self.assertEqual(response["X-TrackNode-Subscription-Required"], "false")

    def test_unpublished_and_missing_sites_remain_not_found(self):
        self.site.is_active = False
        self.site.save(update_fields=("is_active",))
        self.assertEqual(self.client.get("/api/public/sites/public-lock-site/html/").status_code, 404)
        self.assertEqual(self.client.get("/api/public/sites/missing/html/").status_code, 404)

    def test_lock_is_appended_when_body_tag_is_missing(self):
        rendered = inject_subscription_lock("<main>Site</main>", "https://tracknode.test/billing?a=1&b=2")
        self.assertTrue(rendered.startswith("<main>Site</main>"))
        self.assertIn("tracknode-subscription-lock", rendered)
        self.assertIn("a=1&amp;b=2", rendered)

    def test_existing_lock_is_not_injected_twice(self):
        source = '<html><body><div id="tracknode-subscription-lock"></div></body></html>'
        self.assertEqual(inject_subscription_lock(source, "https://tracknode.test/billing"), source)

    @override_settings(ENABLE_BILLING=False)
    def test_disabled_billing_preserves_existing_public_site_behavior(self):
        response = self.client.get("/api/public/sites/public-lock-site/html/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "tracknode-subscription-lock")
