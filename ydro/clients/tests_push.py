import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sites.models import Site, SiteLead
from clients.models import PushSubscription
from clients.push_services import build_site_lead_push_payload, send_site_lead_push_notifications


PUSH_SETTINGS = {
    "WEB_PUSH_VAPID_PUBLIC_KEY": "public-key",
    "WEB_PUSH_VAPID_PRIVATE_KEY": "private-key",
    "WEB_PUSH_VAPID_SUBJECT": "mailto:test@example.com",
}


@override_settings(**PUSH_SETTINGS)
class PushSubscriptionApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="push-owner", password="test-test")
        self.other_user = user_model.objects.create_user(username="other-push-owner", password="test-test")
        self.url = reverse("admin-push-subscriptions")
        self.payload = {
            "endpoint": "https://push.example.test/subscription-1",
            "keys": {"p256dh": "public_subscription_key", "auth": "auth_key"},
        }

    def test_endpoint_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_public_config_and_only_current_user_endpoints(self):
        PushSubscription.objects.create(
            user=self.user,
            endpoint=self.payload["endpoint"],
            p256dh="key",
            auth="auth",
        )
        PushSubscription.objects.create(
            user=self.other_user,
            endpoint="https://push.example.test/other",
            p256dh="key",
            auth="auth",
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["configured"])
        self.assertEqual(response.data["vapid_public_key"], "public-key")
        self.assertEqual(response.data["active_endpoints"], [self.payload["endpoint"]])
        self.assertNotContains(response, "private-key")

    def test_repeated_subscription_updates_without_duplicate(self):
        self.client.force_authenticate(self.user)
        first_response = self.client.post(self.url, self.payload, format="json", HTTP_USER_AGENT="Browser A")
        updated_payload = {**self.payload, "keys": {"p256dh": "new_key", "auth": "new_auth"}}
        second_response = self.client.post(self.url, updated_payload, format="json", HTTP_USER_AGENT="Browser B")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(PushSubscription.objects.count(), 1)
        subscription = PushSubscription.objects.get()
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.p256dh, "new_key")
        self.assertEqual(subscription.user_agent, "Browser B")
        self.assertTrue(subscription.is_active)

    def test_rejects_non_public_or_non_https_push_endpoint(self):
        self.client.force_authenticate(self.user)
        for endpoint in (
            "http://push.example.test/subscription",
            "https://127.0.0.1/subscription",
            "https://push.internal/subscription",
            "https://push.example.test:8443/subscription",
        ):
            response = self.client.post(self.url, {**self.payload, "endpoint": endpoint}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, endpoint)

        self.assertFalse(PushSubscription.objects.exists())

    def test_user_cannot_take_over_another_users_endpoint(self):
        PushSubscription.objects.create(
            user=self.other_user,
            endpoint=self.payload["endpoint"],
            p256dh="other_key",
            auth="other_auth",
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(PushSubscription.objects.get().user, self.other_user)

    def test_delete_only_deactivates_current_users_subscription(self):
        own = PushSubscription.objects.create(
            user=self.user,
            endpoint=self.payload["endpoint"],
            p256dh="key",
            auth="auth",
        )
        other = PushSubscription.objects.create(
            user=self.other_user,
            endpoint="https://push.example.test/other",
            p256dh="key",
            auth="auth",
        )
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.url, {"endpoint": own.endpoint}, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        own.refresh_from_db()
        other.refresh_from_db()
        self.assertFalse(own.is_active)
        self.assertTrue(other.is_active)


@override_settings(**PUSH_SETTINGS)
class SiteLeadPushServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="site-owner", password="test-test")
        self.other_user = user_model.objects.create_user(username="foreign-owner", password="test-test")
        self.site = Site.objects.create(name="Private Site", slug="private-site", owner=self.owner)
        self.lead = SiteLead.objects.create(
            site=self.site,
            name="Sensitive name",
            phone="+79990000000",
            email="private@example.com",
            message="Sensitive message",
        )
        self.subscription = PushSubscription.objects.create(
            user=self.owner,
            endpoint="https://push.example.test/owner",
            p256dh="owner_key",
            auth="owner_auth",
        )
        PushSubscription.objects.create(
            user=self.other_user,
            endpoint="https://push.example.test/other",
            p256dh="other_key",
            auth="other_auth",
        )

    def test_payload_contains_site_and_link_but_no_personal_data(self):
        payload = build_site_lead_push_payload(self.lead)
        serialized = json.dumps(payload, ensure_ascii=False)

        self.assertIn(self.site.name, serialized)
        self.assertEqual(payload["data"]["url"], f"/sites/{self.site.id}/leads?lead={self.lead.id}")
        self.assertNotIn(self.lead.name, serialized)
        self.assertNotIn(self.lead.phone, serialized)
        self.assertNotIn(self.lead.email, serialized)
        self.assertNotIn(self.lead.message, serialized)

    @patch("clients.push_services.webpush")
    def test_sends_only_to_site_owner_active_subscriptions(self, mocked_webpush):
        delivered = send_site_lead_push_notifications(self.lead)

        self.assertEqual(delivered, 1)
        mocked_webpush.assert_called_once()
        self.assertEqual(mocked_webpush.call_args.kwargs["subscription_info"]["endpoint"], self.subscription.endpoint)

    @patch("clients.push_services.webpush", side_effect=RuntimeError("push provider down"))
    def test_delivery_error_deactivates_subscription(self, mocked_webpush):
        delivered = send_site_lead_push_notifications(self.lead)

        self.assertEqual(delivered, 0)
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.is_active)
