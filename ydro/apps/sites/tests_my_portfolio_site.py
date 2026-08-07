from io import StringIO
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.mediafiles.models import MediaFile
from apps.sites.models import SectionSchema, Site, SiteLead, SiteSection
from apps.sites.my_portfolio_site import (
    MY_PORTFOLIO_SECTION_SEEDS,
    MY_PORTFOLIO_SERVICES,
    MY_PORTFOLIO_SITE_SEO,
    SERVICE_CATEGORY_LABELS,
)
from clients.models import Client
from tracker.models import Site as TrackerSite, Visit


class MyPortfolioSiteSeedTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_superuser(
            username="tracknode-admin",
            email="tracknode-admin@example.com",
            password="test-pass-123",
        )
        self.other_user = user_model.objects.create_user(
            username="other-user",
            email="other@example.com",
            password="test-pass-123",
        )
        self.tracknode = Site.objects.create(
            name="TrackNode",
            slug="tracknode",
            domain="tracknode.ru",
            owner=self.owner,
            is_active=True,
        )

    def seed(self, *args):
        call_command("seed_my_portfolio_site", *args, stdout=StringIO(), stderr=StringIO())

    def test_seed_is_idempotent_and_public_bundle_is_available(self):
        self.seed()
        self.seed()

        site = Site.objects.get(slug="my-portfolio")
        self.assertEqual(site.name, "Портфолио Александра")
        self.assertEqual(site.domain, "tishechkinalexandr.ru")
        self.assertEqual(site.owner, self.owner)
        self.assertTrue(site.is_active)
        self.assertEqual(site.seo["canonical"], MY_PORTFOLIO_SITE_SEO["canonical"])
        self.assertEqual(site.sections.count(), len(MY_PORTFOLIO_SECTION_SEEDS))
        self.assertEqual(Client.objects.filter(owner=self.owner).count(), 1)
        self.assertEqual(
            SectionSchema.objects.filter(section_key__startswith="my-portfolio-").count(),
            len(MY_PORTFOLIO_SECTION_SEEDS),
        )

        response = APIClient().get("/api/sites/my-portfolio/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["site"]["slug"], "my-portfolio")
        self.assertEqual(response.data["site"]["domain"], "tishechkinalexandr.ru")
        self.assertTrue(response.data["site"]["tracker_key"])
        self.assertEqual(len(response.data["sections"]), len(MY_PORTFOLIO_SECTION_SEEDS))
        section_payload = {section["key"]: section["content"] for section in response.data["sections"]}
        self.assertIn("services", section_payload)
        self.assertEqual(section_payload["services"]["title"], "Услуги")
        self.assertEqual(
            section_payload["services"]["description"],
            "Разработка, администрирование и техническая помощь — выберите нужное направление.",
        )
        self.assertEqual(len(section_payload["services"]["services"]), 18)
        self.assertEqual(
            self._category_counts(section_payload["services"]["services"]),
            {"development": 6, "administration": 6, "technical_support": 6},
        )
        self.assertEqual(
            [service["title"] for service in section_payload["services"]["services"][:6]],
            [
                "Разработка сайта",
                "Доработка существующего сайта",
                "Интернет-магазин",
                "API и CRM интеграции",
                "Telegram-боты",
                "Автоматизация процессов",
            ],
        )
        self.assertEqual(
            {service["category_label"] for service in section_payload["services"]["services"]},
            set(SERVICE_CATEGORY_LABELS.values()),
        )

    def test_portfolio_and_tracknode_are_visible_only_to_owner(self):
        self.seed()

        owner_api = APIClient()
        owner_api.force_authenticate(self.owner)
        response = owner_api.get("/api/admin/my-sites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["slug"] for item in response.data}, {"tracknode", "my-portfolio"})

        other_api = APIClient()
        other_api.force_authenticate(self.other_user)
        response = other_api.get("/api/admin/my-sites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_public_domain_lookup_supports_root_and_www_alias(self):
        self.seed()

        root_response = APIClient().get("/api/public/by-domain/", {"domain": "tishechkinalexandr.ru"})
        www_response = APIClient().get("/api/public/by-domain/", {"domain": "www.tishechkinalexandr.ru"})

        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(www_response.status_code, 200)
        self.assertEqual(root_response.data["site"]["slug"], "my-portfolio")
        self.assertEqual(www_response.data["site"]["slug"], "my-portfolio")

    def test_content_leads_and_tracker_data_are_isolated_from_tracknode(self):
        self.seed()
        portfolio = Site.objects.get(slug="my-portfolio")

        portfolio_hero = SiteSection.objects.get(site=portfolio, key="hero")
        portfolio_hero.content["title"] = "Портфолио из админки"
        portfolio_hero.save(update_fields=["content", "updated_at"])
        tracknode_section = SiteSection.objects.create(
            site=self.tracknode,
            key="hero",
            title="Hero",
            section_type="hero",
            order=1,
            is_active=True,
            schema={"fields": [{"key": "title", "label": "Title", "type": "text"}]},
            content={"title": "TrackNode title"},
        )

        response = APIClient().get("/api/sites/my-portfolio/")
        section_payload = {section["key"]: section["content"] for section in response.data["sections"]}
        self.assertEqual(section_payload["hero"]["title"], "Портфолио из админки")
        tracknode_section.refresh_from_db()
        self.assertEqual(tracknode_section.content["title"], "TrackNode title")

        lead_response = APIClient().post(
            "/api/public/sites/my-portfolio/leads/",
            {"name": "Иван", "phone": "+79990000000", "message": "Нужен сайт"},
            format="json",
        )
        self.assertEqual(lead_response.status_code, 201)
        self.assertTrue(SiteLead.objects.filter(site=portfolio, phone="+79990000000").exists())
        self.assertFalse(SiteLead.objects.filter(site=self.tracknode, phone="+79990000000").exists())

        payload = {
            "token": portfolio.api_key,
            "visitor_id": "visitor-portfolio",
            "session_id": "session-portfolio",
            "url": "https://tishechkinalexandr.ru/",
        }
        track_response = APIClient().post("/api/track/visit-start/", payload, format="json")
        self.assertEqual(track_response.status_code, 201)
        portfolio_tracker_site = TrackerSite.objects.get(token=portfolio.api_key)
        self.assertTrue(Visit.objects.filter(site=portfolio_tracker_site, session_id="session-portfolio").exists())
        self.assertFalse(TrackerSite.objects.filter(token=self.tracknode.api_key).exists())

    def test_portfolio_contact_lead_stores_service_comment_and_source(self):
        self.seed()
        portfolio = Site.objects.get(slug="my-portfolio")

        response = APIClient().post(
            "/api/public/sites/my-portfolio/leads/",
            {
                "name": "Alex",
                "phone": "+79991234567",
                "message": "Нужно поправить форму",
                "service_type": "my_portfolio_contact",
                "service_title": "КриптоПро и ЭЦП",
                "payload": {"source": "my_portfolio_contact", "selected_service": "КриптоПро и ЭЦП"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        lead = SiteLead.objects.latest("id")
        self.assertEqual(lead.site, portfolio)
        self.assertEqual(lead.service_type, "my_portfolio_contact")
        self.assertEqual(lead.service_title, "КриптоПро и ЭЦП")
        self.assertEqual(lead.message, "Нужно поправить форму")
        self.assertEqual(lead.payload["source"], "my_portfolio_contact")
        self.assertEqual(lead.payload["selected_service"], "КриптоПро и ЭЦП")

    def test_regular_seed_preserves_admin_content_and_reset_restores_it(self):
        self.seed()
        hero = SiteSection.objects.get(site__slug="my-portfolio", key="hero")
        hero.content["title"] = "Заголовок из админки"
        hero.save(update_fields=["content", "updated_at"])

        self.seed()
        hero.refresh_from_db()
        self.assertEqual(hero.content["title"], "Заголовок из админки")

        self.seed("--reset-content")
        hero.refresh_from_db()
        self.assertEqual(hero.content["title"], "Создаю современные веб-приложения")

    def test_reset_services_replaces_only_services_content(self):
        self.seed()
        portfolio = Site.objects.get(slug="my-portfolio")
        hero = SiteSection.objects.get(site=portfolio, key="hero")
        services = SiteSection.objects.get(site=portfolio, key="services")
        hero.content["title"] = "Заголовок из админки"
        services.content["services"] = [
            {
                "id": "custom",
                "title": "Своя услуга",
                "description": "Останется при обычном seed.",
                "category": "development",
                "category_label": "Разработка",
                "is_active": True,
                "order": 10,
            }
        ]
        hero.save(update_fields=["content", "updated_at"])
        services.save(update_fields=["content", "updated_at"])

        self.seed()
        hero.refresh_from_db()
        services.refresh_from_db()
        self.assertEqual(hero.content["title"], "Заголовок из админки")
        self.assertEqual(services.content["services"][0]["title"], "Своя услуга")

        self.seed("--reset-services")
        hero.refresh_from_db()
        services.refresh_from_db()
        self.assertEqual(hero.content["title"], "Заголовок из админки")
        self.assertEqual(services.content["services"], MY_PORTFOLIO_SERVICES)
        self.assertEqual(self._category_counts(services.content["services"]), {
            "development": 6,
            "administration": 6,
            "technical_support": 6,
        })

    def test_portfolio_media_fields_are_explicit_in_section_schemas(self):
        media_fields = {}
        for seed in MY_PORTFOLIO_SECTION_SEEDS:
            SiteSection.validate_schema(seed["schema"])
            SiteSection.validate_content(seed["content"], seed["schema"])
            media_fields[seed["key"]] = self._collect_media_fields(seed["schema"]["fields"])

        self.assertIn("favicon", media_fields["settings"])
        self.assertIn("logo_image", media_fields["settings"])
        self.assertIn("portrait_image", media_fields["hero"])
        self.assertIn("profile_image", media_fields["about"])
        self.assertIn("illustration_image", media_fields["skills"])
        self.assertIn("groups.image", media_fields["skills"])
        self.assertIn("projects.image", media_fields["projects"])
        self.assertIn("projects.images.src", media_fields["projects"])
        self.assertIn("illustration_image", media_fields["why-me"])
        self.assertIn("reasons.image", media_fields["why-me"])
        self.assertIn("illustration_image", media_fields["checklist"])
        self.assertIn("items.image", media_fields["checklist"])
        self.assertIn("cases.image", media_fields["cases"])
        self.assertIn("images.image", media_fields["gallery"])
        self.assertIn("contact_image", media_fields["contact"])
        self.assertIn("logo_image", media_fields["footer"])

    @override_settings(SITE_BASE_URL="https://tracknode.test")
    def test_portfolio_media_upload_patch_and_public_bundle_persist_image_paths(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(media_root, ignore_errors=True))

        with override_settings(MEDIA_ROOT=media_root):
            self.seed()
            portfolio = Site.objects.get(slug="my-portfolio")
            hero = SiteSection.objects.get(site=portfolio, key="hero")
            gallery = SiteSection.objects.get(site=portfolio, key="gallery")

            api = APIClient()
            api.force_authenticate(self.owner)
            first = self._upload_png(api, portfolio, "hero", "portrait_image", "portrait.png")
            second = self._upload_png(api, portfolio, "gallery", "images.0.image", "gallery.png")

            self.assertEqual(MediaFile.objects.filter(site=portfolio).count(), 2)
            self.assertTrue(first["path"].startswith(f"/media/sites/{portfolio.id}/hero/"))
            self.assertTrue(second["path"].startswith(f"/media/sites/{portfolio.id}/gallery/"))

            hero_content = dict(hero.content)
            hero_content["portrait_image"] = first["path"]
            patch_response = api.patch(
                f"/api/admin/my-sites/{portfolio.id}/sections/{hero.id}/",
                {"content": hero_content},
                format="json",
            )
            self.assertEqual(patch_response.status_code, 200)

            gallery_content = dict(gallery.content)
            gallery_content["images"][0]["image"] = second["path"]
            gallery_response = api.patch(
                f"/api/admin/my-sites/{portfolio.id}/sections/{gallery.id}/",
                {"content": gallery_content},
                format="json",
            )
            self.assertEqual(gallery_response.status_code, 200)

            hero.refresh_from_db()
            gallery.refresh_from_db()
            self.assertEqual(hero.content["portrait_image"], first["path"])
            self.assertEqual(gallery.content["images"][0]["image"], second["path"])

            public_response = APIClient().get("/api/sites/my-portfolio/")
            self.assertEqual(public_response.status_code, 200)
            public_sections = {section["key"]: section["content"] for section in public_response.data["sections"]}
            self.assertEqual(public_sections["hero"]["portrait_image"], first["path"])
            self.assertEqual(public_sections["gallery"]["images"][0]["image"], second["path"])

    def test_regular_seed_merges_project_image_fields_without_overwriting_admin_media(self):
        self.seed()
        projects = SiteSection.objects.get(site__slug="my-portfolio", key="projects")
        current_projects = projects.content["projects"]
        current_projects[0]["image"] = "/media/sites/161/projects/custom.webp"
        current_projects[0]["image_alt"] = "Custom project screenshot"
        current_projects[0]["images"] = [{"src": "/media/sites/161/projects/gallery.webp"}]
        current_projects[1].pop("image", None)
        current_projects[1].pop("image_alt", None)
        projects.save(update_fields=["content", "updated_at"])

        self.seed()
        projects.refresh_from_db()
        first_project = projects.content["projects"][0]
        second_project = projects.content["projects"][1]

        self.assertEqual(first_project["image"], "/media/sites/161/projects/custom.webp")
        self.assertEqual(first_project["image_alt"], "Custom project screenshot")
        self.assertEqual(first_project["images"], [{"src": "/media/sites/161/projects/gallery.webp"}])
        self.assertTrue(second_project["image"])
        self.assertTrue(second_project["image_alt"])

    def test_reset_content_restores_project_seed_images_explicitly(self):
        self.seed()
        projects = SiteSection.objects.get(site__slug="my-portfolio", key="projects")
        projects.content["projects"][0]["image"] = "/media/sites/161/projects/custom.webp"
        projects.save(update_fields=["content", "updated_at"])

        self.seed("--reset-content")
        projects.refresh_from_db()

        self.assertNotEqual(projects.content["projects"][0]["image"], "/media/sites/161/projects/custom.webp")
        self.assertTrue(projects.content["projects"][0]["image"].startswith("/"))

    def _collect_media_fields(self, fields, prefix=""):
        keys = set()
        for field in fields:
            key = field.get("key")
            path = f"{prefix}.{key}" if prefix else key
            if field.get("type") in {"image", "video", "media"}:
                keys.add(path)
            if field.get("type") == "repeater":
                keys.update(self._collect_media_fields(field.get("fields", []), path))
        return keys

    def _category_counts(self, services):
        counts = {}
        for service in services:
            category = service["category"]
            counts[category] = counts.get(category, 0) + 1
        return counts

    def _upload_png(self, api, site, section, field_name, filename):
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\x89\xa3\xcd"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = api.post(
            "/api/uploads/",
            {
                "site": str(site.id),
                "section": section,
                "field": field_name,
                "file": SimpleUploadedFile(filename, png_bytes, content_type="image/png"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        return response.data
