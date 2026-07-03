from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.sites.models import SectionSchema, Site, SiteLead, SiteSection
from apps.sites.tracknode_site import TRACKNODE_SECTION_SEEDS, TRACKNODE_SITE_SEO
from clients.models import Client


class TrackNodeSiteSeedTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="tracknode-admin",
            email="tracknode-admin@example.com",
            password="test-pass-123",
        )

    def seed(self, *args):
        call_command("seed_tracknode_site", *args, stdout=StringIO(), stderr=StringIO())

    def test_seed_is_idempotent_and_exposes_public_bundle(self):
        self.seed()
        self.seed()

        site = Site.objects.get(slug="tracknode")
        self.assertEqual(site.name, "TrackNode")
        self.assertEqual(site.domain, "tracknode.ru")
        self.assertEqual(site.owner, self.owner)
        self.assertTrue(site.is_active)
        self.assertEqual(site.seo["canonical"], TRACKNODE_SITE_SEO["canonical"])
        self.assertEqual(site.sections.count(), len(TRACKNODE_SECTION_SEEDS))
        self.assertEqual(Client.objects.filter(owner=self.owner).count(), 1)
        self.assertEqual(
            SectionSchema.objects.filter(section_key__startswith="tracknode-").count(),
            len(TRACKNODE_SECTION_SEEDS),
        )

        response = APIClient().get("/api/sites/tracknode/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["site"]["slug"], "tracknode")
        self.assertTrue(response.data["site"]["tracker_key"])
        self.assertEqual(len(response.data["sections"]), len(TRACKNODE_SECTION_SEEDS))

        lead_response = APIClient().post(
            "/api/public/sites/tracknode/leads/",
            {"name": "Иван", "phone": "+79990000000", "message": "Нужна консультация"},
            format="json",
        )
        self.assertEqual(lead_response.status_code, 201)
        self.assertTrue(SiteLead.objects.filter(site=site, phone="+79990000000").exists())

    def test_regular_seed_preserves_admin_content_and_reset_restores_it(self):
        self.seed()
        hero = SiteSection.objects.get(site__slug="tracknode", key="hero")
        hero.content["title_line_1"] = "Заголовок из админки"
        hero.save(update_fields=["content", "updated_at"])

        self.seed()
        hero.refresh_from_db()
        self.assertEqual(hero.content["title_line_1"], "Заголовок из админки")

        self.seed("--reset-content")
        hero.refresh_from_db()
        self.assertEqual(hero.content["title_line_1"], "Понимайте аудиторию.")
