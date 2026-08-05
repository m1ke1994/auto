from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.sites.models import Site, SiteLead


class TrackNodeWebsiteOrderLeadTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="owner", email="owner@example.com", password="pass")
        self.site = Site.objects.create(name="TrackNode", slug="tracknode", domain="tracknode.ru", owner=self.owner)
        self.url = "/api/public/sites/tracknode/leads/"

    def test_tracknode_order_requires_consent(self):
        response = self.client.post(
            self.url,
            {
                "name": "Alex",
                "telegram": "@alex",
                "service_type": "tracknode_website_order",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("consent", response.json()["errors"])
        self.assertFalse(SiteLead.objects.exists())

    def test_tracknode_order_accepts_telegram_contact_and_stores_source_payload(self):
        response = self.client.post(
            self.url,
            {
                "name": "<b>Alex</b>",
                "telegram": "@alex",
                "message": "<script>alert(1)</script>Need site",
                "service_type": "tracknode_website_order",
                "service_title": "Corporate site",
                "existing_site_url": "https://example.ru",
                "preferred_contact": "telegram",
                "consent": True,
                "payload": {"utm_source": "test"},
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        lead = SiteLead.objects.get()
        self.assertEqual(lead.site, self.site)
        self.assertEqual(lead.name, "Alex")
        self.assertEqual(lead.service_type, "tracknode_website_order")
        self.assertNotIn("<script>", lead.message)
        self.assertEqual(lead.payload["source"], "tracknode_website_order")
        self.assertEqual(lead.payload["telegram"], "@alex")
        self.assertEqual(lead.payload["existing_site_url"], "https://example.ru")
        self.assertIn("consent_at", lead.payload)
