from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sites.models import Site
from apps.sites.telegram_binding import build_site_start_payload
from clients.models import Client
from clients.telegram_binding import build_secure_start_payload
from subscriptions.models import TelegramLink

User = get_user_model()


class TelegramRelayBindTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="relay-owner",
            email="relay-owner@example.com",
            password="secret12345",
        )
        self.url = reverse("telegram_relay_bind")

    @override_settings(TELEGRAM_RELAY_BIND_TOKEN="relay-secret", TELEGRAM_RELAY_TOKEN="")
    def test_relay_bind_connects_site(self):
        site = Site.objects.create(
            owner=self.user,
            name="Site One",
            slug="site-one",
            domain="example.com",
            is_active=True,
        )
        payload = build_site_start_payload(site)

        response = self.client.post(
            self.url,
            {
                "start_payload": payload,
                "chat_id": "123456",
                "telegram_user_id": 777,
            },
            format="json",
            HTTP_X_RELAY_TOKEN="relay-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["target_type"], "site")
        site.refresh_from_db()
        self.assertEqual(site.telegram_chat_id, "123456")
        self.assertTrue(site.send_to_telegram)
        self.assertIsNotNone(site.telegram_connected_at)

    @override_settings(TELEGRAM_RELAY_BIND_TOKEN="relay-secret", TELEGRAM_RELAY_TOKEN="")
    def test_relay_bind_connects_legacy_client_and_link(self):
        client = Client.objects.create(owner=self.user, name="Mini CRM", is_active=True)
        payload = build_secure_start_payload(client)

        response = self.client.post(
            self.url,
            {
                "start_payload": payload,
                "chat_id": "123456",
                "telegram_user_id": 777,
            },
            format="json",
            HTTP_X_RELAY_TOKEN="relay-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["target_type"], "client")
        client.refresh_from_db()
        self.assertEqual(client.telegram_chat_id, "123456")
        self.assertTrue(client.send_to_telegram)
        link = TelegramLink.objects.get(client=client)
        self.assertEqual(link.telegram_user_id, 777)
        self.assertEqual(link.telegram_chat_id, 123456)

    @override_settings(TELEGRAM_RELAY_BIND_TOKEN="relay-secret", TELEGRAM_RELAY_TOKEN="")
    def test_relay_bind_rejects_invalid_token(self):
        response = self.client.post(
            self.url,
            {"start_payload": "site_1_bad_bad", "chat_id": "123456"},
            format="json",
            HTTP_X_RELAY_TOKEN="wrong",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["ok"])

    @override_settings(TELEGRAM_RELAY_BIND_TOKEN="", TELEGRAM_RELAY_TOKEN="fallback-secret")
    def test_relay_bind_uses_delivery_relay_token_as_fallback(self):
        site = Site.objects.create(
            owner=self.user,
            name="Site One",
            slug="site-one",
            domain="example.com",
            is_active=True,
        )

        response = self.client.post(
            self.url,
            {"start_payload": build_site_start_payload(site), "chat_id": "123456"},
            format="json",
            HTTP_X_RELAY_TOKEN="fallback-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        site.refresh_from_db()
        self.assertEqual(site.telegram_chat_id, "123456")

    @override_settings(TELEGRAM_RELAY_BIND_TOKEN="relay-secret", TELEGRAM_RELAY_TOKEN="")
    def test_relay_bind_rejects_invalid_start_payload(self):
        response = self.client.post(
            self.url,
            {"start_payload": "site_1_bad_bad", "chat_id": "123456"},
            format="json",
            HTTP_X_RELAY_TOKEN="relay-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["ok"])
