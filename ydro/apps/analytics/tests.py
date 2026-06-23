from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.sites.models import Site, SiteLead
from tracker.models import Event as TrackerEvent
from tracker.models import PageView as TrackerPageView
from tracker.models import Site as TrackerSite
from tracker.models import Visit as TrackerVisit


class AnalyticsApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner-analytics",
            email="owner.analytics@example.com",
            password="test-test",
        )
        self.other_user = user_model.objects.create_user(
            username="other-owner",
            email="other.owner@example.com",
            password="test-test",
        )
        self.site = Site.objects.create(
            name="Analytics Site",
            slug="analytics-site",
            domain="localhost",
            owner=self.user,
            is_active=True,
        )
        self.other_site = Site.objects.create(
            name="Foreign Site",
            slug="foreign-site",
            domain="localhost",
            owner=self.other_user,
            is_active=True,
        )

    def test_public_tracking_endpoints_create_data(self):
        visit_start_url = reverse("track-visit-start")
        pageview_url = reverse("track-pageview")
        event_url = reverse("track-event")
        visit_end_url = reverse("track-visit-end")

        payload_base = {
            "token": self.site.api_key,
            "session_id": "session-1",
            "visitor_id": "visitor-1",
        }

        start_response = self.client.post(
            visit_start_url,
            {**payload_base, "referrer": "https://google.com"},
            format="json",
        )
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)

        pageview_response = self.client.post(
            pageview_url,
            {**payload_base, "url": "http://localhost:5173/", "title": "Home"},
            format="json",
        )
        self.assertEqual(pageview_response.status_code, status.HTTP_201_CREATED)

        event_response = self.client.post(
            event_url,
            {**payload_base, "type": "click", "payload": {"target": "button"}},
            format="json",
        )
        self.assertEqual(event_response.status_code, status.HTTP_201_CREATED)

        end_response = self.client.post(
            visit_end_url,
            {**payload_base, "duration": 42},
            format="json",
        )
        self.assertEqual(end_response.status_code, status.HTTP_200_OK)

        self.assertEqual(Visit.objects.filter(site=self.site).count(), 1)
        self.assertEqual(PageView.objects.filter(visit__site=self.site).count(), 1)
        self.assertEqual(TrackingEvent.objects.filter(visit__site=self.site).count(), 1)

    def test_owner_can_view_own_analytics_summary_only(self):
        Visit.objects.create(site=self.site, session_id="s1", visitor_id="v1")
        self.client.force_authenticate(user=self.user)

        own_url = reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id})
        own_response = self.client.get(own_url)
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_response.data["visit_count"], 1)

        foreign_url = reverse("admin-site-analytics-summary", kwargs={"site_id": self.other_site.id})
        foreign_response = self.client.get(foreign_url)
        self.assertEqual(foreign_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_summary_counts_tracker_data_for_site_api_key(self):
        tracker_site = TrackerSite.objects.create(token=self.site.api_key, domain=self.site.domain, is_active=True)
        now = timezone.now()
        first_visit = TrackerVisit.objects.create(
            site=tracker_site,
            session_id="session-1",
            visitor_id="visitor-1",
            device_type="desktop",
            browser_family="Chrome",
            os="Windows",
            referrer="https://google.com/search",
            started_at=now,
            duration=40,
            is_bot=False,
        )
        second_visit = TrackerVisit.objects.create(
            site=tracker_site,
            session_id="session-2",
            visitor_id="visitor-1",
            device_type="mobile",
            browser_family="Mobile Safari",
            os="iOS",
            started_at=now,
            duration=20,
            is_bot=False,
        )
        TrackerVisit.objects.create(
            site=tracker_site,
            session_id="legacy-session",
            visitor_id="",
            device_type="desktop",
            browser_family="Chrome",
            os="Windows",
            started_at=now,
            is_bot=False,
        )
        TrackerVisit.objects.create(
            site=tracker_site,
            session_id="bot-session",
            visitor_id="bot-visitor",
            started_at=now,
            is_bot=True,
        )
        TrackerPageView.objects.create(visit=first_visit, url="https://example.com/", title="Home", timestamp=now)
        TrackerPageView.objects.create(visit=first_visit, url="https://example.com/prices", title="Prices", timestamp=now)
        TrackerPageView.objects.create(visit=second_visit, url="https://example.com/", title="Home", timestamp=now)
        TrackerEvent.objects.create(
            visit=first_visit,
            type="time_on_page",
            payload={"duration_seconds": 90},
            timestamp=now,
        )
        SiteLead.objects.create(site=self.site, name="Lead", phone="+79990000000", created_at=now)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["visit_count"], 3)
        self.assertEqual(response.data["visitors_unique"], 2)
        self.assertEqual(response.data["pageviews_count"], 3)
        self.assertEqual(response.data["leads_count"], 1)
        self.assertEqual(response.data["conversion"], 33.33)
        self.assertEqual(response.data["devices"]["desktop"], 2)
        self.assertEqual(response.data["devices"]["mobile"], 1)
        self.assertEqual(response.data["browsers"]["Chrome"], 2)
        self.assertEqual(response.data["os"]["Windows"], 2)
        self.assertEqual(response.data["total_time_on_site_seconds"], 60)
        self.assertEqual(response.data["avg_duration"], 30)
        self.assertEqual(response.data["avg_time_on_site"], 30)

    def test_admin_summary_uses_time_on_page_fallback_when_visit_duration_is_empty(self):
        tracker_site = TrackerSite.objects.create(token=self.site.api_key, domain=self.site.domain, is_active=True)
        now = timezone.now()
        visit = TrackerVisit.objects.create(
            site=tracker_site,
            session_id="session-fallback",
            visitor_id="visitor-fallback",
            started_at=now,
            duration=0,
            is_bot=False,
        )
        TrackerEvent.objects.create(
            visit=visit,
            type="time_on_page",
            payload={"duration_seconds": 25},
            timestamp=now,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["visit_count"], 1)
        self.assertEqual(response.data["total_time_on_site_seconds"], 25)
        self.assertEqual(response.data["avg_duration"], 25)
        self.assertEqual(response.data["avg_time_on_site"], 25)

    def test_admin_summary_ignores_invalid_duration_values(self):
        tracker_site = TrackerSite.objects.create(token=self.site.api_key, domain=self.site.domain, is_active=True)
        now = timezone.now()
        visit = TrackerVisit.objects.create(
            site=tracker_site,
            session_id="session-invalid-duration",
            visitor_id="visitor-invalid-duration",
            started_at=now,
            duration=0,
            is_bot=False,
        )
        TrackerEvent.objects.create(
            visit=visit,
            type="time_on_page",
            payload={"duration_seconds": 0},
            timestamp=now,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_time_on_site_seconds"], 0)
        self.assertEqual(response.data["avg_duration"], 0)

    def test_tracking_key_refresh_preserves_existing_tracker_history(self):
        tracker_site = TrackerSite.objects.create(token=self.site.api_key, domain=self.site.domain, is_active=True)
        TrackerVisit.objects.create(site=tracker_site, session_id="session-1", visitor_id="visitor-1")

        self.client.force_authenticate(user=self.user)
        refresh_response = self.client.post(
            reverse("admin-site-tracking-key-refresh", kwargs={"site_id": self.site.id})
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.site.refresh_from_db()
        tracker_site.refresh_from_db()
        self.assertEqual(tracker_site.token, self.site.api_key)

        summary_response = self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id}))
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)
        self.assertEqual(summary_response.data["visit_count"], 1)
