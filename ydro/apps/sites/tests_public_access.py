from unittest.mock import patch
import os
from importlib import import_module

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.analytics.models import TrackingEvent, Visit
from apps.sites.models import Site, SiteLead


EXTERNAL_ORIGIN = "https://public-site.example"


class PublicApiAccessTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="public-site-owner",
            email="public-site-owner@example.com",
            password="test-pass-123",
        )
        self.site = Site.objects.create(
            name="A Meditation",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.owner,
            is_active=True,
        )

    def assert_public_cors(self, response):
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
        self.assertNotIn("Access-Control-Allow-Credentials", response.headers)

    def test_public_site_bundle_allows_external_origin_without_authentication(self):
        response = self.client.get(
            reverse("public-site-bundle", kwargs={"site_slug": self.site.slug}),
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )

        self.assertEqual(response.status_code, 200)
        site_payload = response.json()["site"]
        self.assertEqual(site_payload["domain"], "leelabird.ru")
        self.assertEqual(site_payload["tracker_key"], self.site.api_key)
        self.assert_public_cors(response)

    @patch.dict(os.environ, {"PUBLIC_SITE_DEFAULT_DOMAIN": "ameditation.example"})
    def test_domain_migration_updates_only_local_a_meditation_domain(self):
        self.site.domain = "localhost:5173"
        self.site.save(update_fields=["domain"])

        migration = import_module("apps.sites.migrations.0012_update_a_meditation_public_domain")
        migration.update_a_meditation_public_domain(django_apps, None)

        self.site.refresh_from_db()
        self.assertEqual(self.site.domain, "ameditation.example")

    def test_public_lead_preflight_allows_external_origin_without_credentials(self):
        response = self.client.options(
            reverse("public-leads-create"),
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("POST", response.headers["Access-Control-Allow-Methods"])
        self.assertIn("content-type", response.headers["Access-Control-Allow-Headers"].lower())
        self.assert_public_cors(response)

    def test_private_admin_endpoint_stays_protected_and_has_no_wildcard_cors(self):
        response = self.client.get(
            reverse("admin-my-sites"),
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    @patch("apps.sites.serializers.send_lead_telegram_notification", return_value=True)
    def test_public_lead_is_created_for_site_without_cookies(self, mocked_telegram):
        response = self.client.post(
            reverse("public-leads-create"),
            {
                "site_slug": self.site.slug,
                "section_key": "contacts",
                "form_name": "Public contact form",
                "name": "Public visitor",
                "phone": "+79990000000",
                "message": "Please contact me",
            },
            content_type="application/json",
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
        )

        self.assertEqual(response.status_code, 201)
        lead = SiteLead.objects.get()
        self.assertEqual(lead.site_id, self.site.id)
        self.assert_public_cors(response)
        mocked_telegram.assert_called_once()

    def test_tracker_script_and_event_are_available_to_external_origin(self):
        script_response = self.client.get(
            reverse("tracker-js"),
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
        )
        self.assertEqual(script_response.status_code, 200)
        self.assert_public_cors(script_response)

        visit_response = self.client.post(
            reverse("track-visit-start"),
            {
                "token": self.site.api_key,
                "session_id": "public-session",
                "visitor_id": "public-visitor",
            },
            content_type="application/json",
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
        )
        self.assertEqual(visit_response.status_code, 201)
        self.assert_public_cors(visit_response)

        event_response = self.client.post(
            reverse("track-event"),
            {
                "token": self.site.api_key,
                "session_id": "public-session",
                "visitor_id": "public-visitor",
                "type": "click",
                "payload": {"target": "contact-button"},
            },
            content_type="application/json",
            HTTP_ORIGIN=EXTERNAL_ORIGIN,
        )
        self.assertEqual(event_response.status_code, 201)
        self.assert_public_cors(event_response)
        self.assertEqual(Visit.objects.filter(site=self.site).count(), 1)
        self.assertEqual(TrackingEvent.objects.filter(visit__site=self.site).count(), 1)
