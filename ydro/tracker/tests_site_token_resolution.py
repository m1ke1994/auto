from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.sites.models import Site as CoreSite
from clients.models import Client
from tracker.models import Event as TrackerEvent
from tracker.models import Site as TrackerSite, Visit


class TrackerSiteTokenResolutionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="tracker-owner@example.com",
            email="tracker-owner@example.com",
            password="test-test-123",
        )
        self.client_obj = Client.objects.create(owner=self.owner, name="Tracker Client", is_active=True)
        self.site = CoreSite.objects.create(
            name="Leelabird",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.owner,
            is_active=True,
        )
        self.api = APIClient()

    def test_visit_start_accepts_core_site_api_key_and_creates_tracker_site(self):
        payload = {
            "token": self.site.api_key,
            "visitor_id": "visitor-1",
            "session_id": "session-1",
        }
        response = self.api.post("/api/mini/track/visit-start/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["ok"])

        tracker_site = TrackerSite.objects.filter(token=self.site.api_key).first()
        self.assertIsNotNone(tracker_site)
        self.assertTrue(Visit.objects.filter(site=tracker_site, session_id="session-1").exists())

    def test_site_api_keys_are_unique(self):
        other_site = CoreSite.objects.create(
            name="Novoe Konakovo",
            slug="novaya-konakova",
            domain="novoe-konakovo.ru",
            owner=self.owner,
            is_active=True,
        )

        self.assertNotEqual(self.site.api_key, other_site.api_key)

    def test_core_site_tracking_creates_lifecycle_events(self):
        payload = {
            "token": self.site.api_key,
            "visitor_id": "visitor-1",
            "session_id": "session-1",
        }

        self.api.post("/api/mini/track/visit-start/", payload, format="json")
        self.api.post(
            "/api/mini/track/pageview/",
            {**payload, "url": "https://leelabird.ru/", "title": "Leelabird"},
            format="json",
        )
        self.api.post(
            "/api/mini/track/visit-end/",
            {**payload, "duration": 45},
            format="json",
        )

        event_types = set(TrackerEvent.objects.values_list("type", flat=True))
        self.assertTrue({"visit", "session_start", "page_view", "session_end"}.issubset(event_types))

    def test_event_with_site_a_token_writes_only_site_a(self):
        site_b = CoreSite.objects.create(
            name="Novoe Konakovo",
            slug="novaya-konakova",
            domain="novoe-konakovo.ru",
            owner=self.owner,
            is_active=True,
        )

        response = self.api.post(
            "/api/mini/track/event/",
            {
                "token": self.site.api_key,
                "visitor_id": "visitor-a",
                "session_id": "session-a",
                "type": "click",
                "payload": {"target": "hero-button"},
            },
            format="json",
            HTTP_ORIGIN="https://leelabird.ru",
        )

        self.assertEqual(response.status_code, 201)
        tracker_site_a = TrackerSite.objects.get(token=self.site.api_key)
        self.assertEqual(TrackerEvent.objects.filter(visit__site=tracker_site_a, type="click").count(), 1)
        self.assertFalse(TrackerSite.objects.filter(token=site_b.api_key).exists())

    def test_site_a_token_is_rejected_from_site_b_origin_without_event(self):
        CoreSite.objects.create(
            name="Novoe Konakovo",
            slug="novaya-konakova",
            domain="novoe-konakovo.ru",
            owner=self.owner,
            is_active=True,
        )

        response = self.api.post(
            "/api/mini/track/event/",
            {
                "token": self.site.api_key,
                "visitor_id": "visitor-a",
                "session_id": "session-a",
                "type": "click",
                "payload": {"target": "wrong-site-button"},
            },
            format="json",
            HTTP_ORIGIN="https://novoe-konakovo.ru",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TrackerEvent.objects.count(), 0)
        self.assertFalse(TrackerSite.objects.filter(token=self.site.api_key).exists())

    def test_www_origin_matches_site_domain(self):
        response = self.api.post(
            "/api/mini/track/visit-start/",
            {
                "token": self.site.api_key,
                "visitor_id": "visitor-www",
                "session_id": "session-www",
            },
            format="json",
            HTTP_ORIGIN="https://www.leelabird.ru",
        )

        self.assertEqual(response.status_code, 201)
        tracker_site = TrackerSite.objects.get(token=self.site.api_key)
        self.assertTrue(Visit.objects.filter(site=tracker_site, session_id="session-www").exists())

    def test_invalid_token_is_rejected_without_event(self):
        response = self.api.post(
            "/api/mini/track/event/",
            {
                "token": "invalid-token",
                "visitor_id": "visitor-invalid",
                "session_id": "session-invalid",
                "type": "click",
                "payload": {"target": "button"},
            },
            format="json",
            HTTP_ORIGIN="https://leelabird.ru",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TrackerEvent.objects.count(), 0)
        self.assertFalse(TrackerSite.objects.filter(token="invalid-token").exists())

    def test_technical_template_source_token_is_rejected(self):
        source_site = CoreSite.objects.create(
            name="A Meditation Template Source",
            slug="tracknode-template-a-meditation-source",
            domain="",
            owner=self.owner,
            is_active=True,
        )

        with patch("tracker.views.is_technical_template_source_site", return_value=True):
            response = self.api.post(
                "/api/mini/track/event/",
                {
                    "token": source_site.api_key,
                    "visitor_id": "visitor-source",
                    "session_id": "session-source",
                    "type": "click",
                    "payload": {"target": "template"},
                },
                format="json",
                HTTP_ORIGIN="https://leelabird.ru",
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TrackerEvent.objects.count(), 0)
