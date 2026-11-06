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

    def test_catalog_pages_are_editable_and_existing_poems_survive(self):
        self.register()
        site = Site.objects.get(slug="vodopyanov")
        poet = SiteSection.objects.get(site=site, key="catalog-poems")
        songs_page = SiteSection.objects.get(site=site, key="catalog-songs")
        self.assertEqual(poet.content["heading_accent"], "стихи.")
        self.assertEqual(songs_page.content["heading_accent"], "песни.")
        original = SiteSection.objects.get(site=site, key="poems")
        original.content["items"].append({
            "id": "new-author-poem", "title": "Новая работа",
            "theme": "Лирика", "lines": "Моя строка",
            "publishedAt": "2026-11-06", "demo": False,
        })
        original.save(update_fields=["content"])
        payload = dict(poet.content)
        payload["intro"] = "Новый текст страницы стихов"
        api = APIClient()
        api.force_authenticate(self.owner)
        response = api.patch(
            f"/api/admin/my-sites/{site.id}/sections/{poet.id}/",
            {"content": payload}, format="json",
        )
        self.assertEqual(response.status_code, 200, getattr(response, "data", None))
        self.register()
        poet.refresh_from_db()
        original.refresh_from_db()
        self.assertEqual(poet.content["intro"], "Новый текст страницы стихов")
        self.assertEqual(original.content["items"][-1]["title"], "Новая работа")
        api_data = APIClient().get("/api/sites/vodopyanov/").data
        sections = {row["key"]: row["content"] for row in api_data["sections"]}
        self.assertEqual(sections["catalog-poems"]["intro"], "Новый текст страницы стихов")
        self.assertEqual(len(sections["poems"]["items"]), 4)
        self.assertEqual(len(sections), len(SECTION_SEEDS))

    def test_check_mode_does_not_modify_existing_site(self):
        self.register()
        before = {s.key: s.content for s in SiteSection.objects.filter(site__slug="vodopyanov")}
        call_command("seed_vodopyanov_site", "--check", stdout=StringIO())
        after = {s.key: s.content for s in SiteSection.objects.filter(site__slug="vodopyanov")}
        self.assertEqual(after, before)
