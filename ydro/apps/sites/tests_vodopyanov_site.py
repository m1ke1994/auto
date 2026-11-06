"""Check that author-site CMS seeding preserves edits and isolates site data."""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.sites.models import Site, SiteSection
from apps.sites.vodopyanov_site import SECTION_SEEDS
from tracker.models import Site as TrackerSite, Visit


class VodopyanovSiteTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner-vodopyanov", email="owner-vodopyanov@example.com", password="test123456"
        )
        self.other = get_user_model().objects.create_user(
            username="reader-vodopyanov", email="reader-vodopyanov@example.com", password="test123456"
        )
        self.tracknode = Site.objects.create(
            name="TrackNode", slug="tracknode", domain="tracknode.ru", owner=self.owner
        )

    def register(self):
        call_command("seed_vodopyanov_site", "--apply", stdout=StringIO())

    def test_initial_seed_and_public_bundle(self):
        call_command("seed_vodopyanov_site", "--check", stdout=StringIO())
        self.assertFalse(Site.objects.filter(slug="vodopyanov").exists())
        self.register()
        self.register()
        site = Site.objects.get(slug="vodopyanov")
        self.assertEqual(site.domain, "stariy-site.ru")
        self.assertEqual(site.owner, self.owner)
        self.assertEqual(site.sections.count(), len(SECTION_SEEDS))
        response = APIClient().get("/api/sites/vodopyanov/")
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["site"]["tracker_key"], site.api_key)
        sections = {section["key"]: section["content"] for section in data["sections"]}
        self.assertEqual(len(sections["poems"]["items"]), 3)
        self.assertEqual(len(sections["songs"]["items"]), 3)
        self.assertEqual(sections["contacts"]["items"][0]["caption"], "@A1exdr56")

    def test_edits_survive_rerun_and_other_site_untouched(self):
        self.register()
        site = Site.objects.get(slug="vodopyanov")
        poem = SiteSection.objects.get(site=site, key="poems")
        poem.content["items"][0]["title"] = "Мой настоящий стих"
        poem.save(update_fields=["content", "updated_at"])
        token = site.api_key
        self.register()
        poem.refresh_from_db()
        site.refresh_from_db()
        self.tracknode.refresh_from_db()
        self.assertEqual(poem.content["items"][0]["title"], "Мой настоящий стих")
        self.assertEqual(site.api_key, token)
        self.assertEqual(self.tracknode.domain, "tracknode.ru")
        self.assertEqual(self.tracknode.sections.count(), 0)

    def test_owner_can_patch_repeater_other_user_cannot(self):
        self.register()
        site = Site.objects.get(slug="vodopyanov")
        section = SiteSection.objects.get(site=site, key="poems")
        content = dict(section.content)
        content["items"] = [
            {"id": "real-poem", "title": "Авторский стих", "theme": "Лирика",
             "publishedAt": "2026-11-06", "demo": False,
             "lines": "Первая строка\nВторая строка"}
        ]
        api = APIClient()
        api.force_authenticate(self.owner)
        response = api.patch(f"/api/admin/my-sites/{site.id}/sections/{section.id}/", {"content": content}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(SiteSection.objects.get(pk=section.pk).content["items"][0]["title"], "Авторский стих")
        response = APIClient().get("/api/sites/vodopyanov/")
        self.assertEqual(response.data["sections"][3]["content"]["items"][0]["title"], "Авторский стих")
        stranger = APIClient()
        stranger.force_authenticate(self.other)
        response = stranger.patch(f"/api/admin/my-sites/{site.id}/sections/{section.id}/", {"content": content}, format="json")
        self.assertIn(response.status_code, (402, 403, 404))

    def test_tracker_token_is_site_specific(self):
        self.register()
        site = Site.objects.get(slug="vodopyanov")
        payload = {
            "token": site.api_key, "visitor_id": "vodopyanov-visitor", "session_id": "vodopyanov-session",
            "url": "https://stariy-site.ru/",
        }
        response = APIClient().post("/api/track/visit-start/", payload, format="json", HTTP_ORIGIN="https://stariy-site.ru")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Visit.objects.filter(site=TrackerSite.objects.get(token=site.api_key)).exists())
        self.assertFalse(TrackerSite.objects.filter(token=self.tracknode.api_key).exists())

    def test_domain_collision_causes_no_partial_writes(self):
        Site.objects.create(name="Other", slug="other-author", domain="stariy-site.ru", owner=self.owner)
        with self.assertRaises(CommandError):
            self.register()
        self.assertFalse(Site.objects.filter(slug="vodopyanov").exists())
