from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.db.models import NOT_PROVIDED
from django.urls import reverse
from io import StringIO
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import TrackingEvent, Visit
from apps.sites.models import Site, SiteLead, SiteSection, SiteTemplate, WebsiteTemplate, WebsiteTemplateCategory
from apps.sites.website_templates import build_site_snapshot
from clients.models import Client
from subscriptions.models import Subscription
from subscriptions.test_utils import grant_business_analytics


class SiteTemplateCatalogTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.source_owner = user_model.objects.create_user(
            username="source-owner",
            email="source@example.com",
            password="test-test",
        )
        self.user = user_model.objects.create_user(
            username="template-user",
            email="template-user@example.com",
            password="test-test",
        )
        client = Client.objects.create(owner=self.user, name="Template user", is_active=True)
        grant_business_analytics(self.user, client=client)
        self.client.force_authenticate(self.user)
        self.category = WebsiteTemplateCategory.objects.get(slug="services")
        self.source_site = Site.objects.create(
            owner=self.source_owner,
            name="Leelabird",
            slug="leelabird",
            domain="leelabird.ru",
            telegram_chat_id="12345",
            send_to_telegram=True,
            seo={"title": "Leelabird"},
            design_preset=Site.DesignPreset.WARM_NATURE,
            builder_template_key="services-landing",
            builder_config={"theme": {"primary": "#176b45"}, "pages": [{"slug": "home"}]},
        )
        self.source_section = SiteSection.objects.create(
            site=self.source_site,
            title="Hero",
            key="hero",
            section_type="hero",
            order=1,
            schema={
                "fields": [
                    {"key": "title", "type": "text", "label": "Title"},
                    {"key": "phone", "type": "text", "label": "Phone"},
                ]
            },
            content={"title": "Leelabird", "phone": "+79990000000"},
            component_key="hero-centered",
            settings={"color": "green"},
            seo={"title": "Leelabird hero"},
        )
        SiteLead.objects.create(site=self.source_site, name="Lead", phone="+79990000000")
        visit = Visit.objects.create(site=self.source_site, session_id="s1", visitor_id="v1")
        TrackingEvent.objects.create(visit=visit, type="page_view", payload={"path": "/"})
        self.template = WebsiteTemplate.objects.create(
            name="Leelabird",
            slug="leelabird-template",
            category=self.category,
            source_site=self.source_site,
            description="Template",
            snapshot_config=build_site_snapshot(self.source_site),
            is_published=True,
            is_active=True,
        )

    def create_from_template(self, company_name="New Company", site_name="", key="same-request"):
        return self.client.post(
            reverse("website-template-create-site", kwargs={"slug": self.template.slug}),
            {"template_slug": self.template.slug, "company_name": company_name, "site_name": site_name},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_catalog_lists_only_published_templates(self):
        WebsiteTemplate.objects.create(
            name="Hidden",
            slug="hidden-template",
            category=self.category,
            source_site=self.source_site,
            snapshot_config=build_site_snapshot(self.source_site),
            is_published=False,
        )

        response = self.client.get(reverse("website-template-catalog"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["slug"] for item in response.data["templates"]], [self.template.slug])
        self.assertEqual(response.data["templates"][0]["source_site_slug"], self.source_site.slug)

    def test_unauthenticated_user_gets_401_for_catalog(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("website-template-catalog"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_catalog_category_filter_works(self):
        tourism = WebsiteTemplateCategory.objects.get(slug="tourism")
        tourism_site = Site.objects.create(owner=self.source_owner, name="Tour", slug="tour-source")
        SiteSection.objects.create(site=tourism_site, title="Hero", key="hero", section_type="hero")
        tourism_template = WebsiteTemplate.objects.create(
            name="Tour template",
            slug="tour-template",
            category=tourism,
            source_site=tourism_site,
            snapshot_config=build_site_snapshot(tourism_site),
            is_published=True,
        )

        response = self.client.get(reverse("website-template-catalog"), {"category": "tourism"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["slug"] for item in response.data["templates"]], [tourism_template.slug])

    def test_generate_site_chooses_template_from_selected_category(self):
        tourism = WebsiteTemplateCategory.objects.get(slug="tourism")
        tourism_site = Site.objects.create(
            owner=self.source_owner,
            name="Tour",
            slug="tour-generate-source",
            builder_template_key="tourism-landing",
            builder_config={"company_name": "Tour"},
        )
        SiteSection.objects.create(site=tourism_site, title="Hero", key="hero", section_type="hero")
        tourism_template = WebsiteTemplate.objects.create(
            name="Tour template",
            slug="tour-generate-template",
            category=tourism,
            source_site=tourism_site,
            snapshot_config=build_site_snapshot(tourism_site),
            is_published=True,
            is_active=True,
        )

        response = self.client.post(
            reverse("website-template-generate"),
            {
                "category_id": tourism.id,
                "company_name": "Tour Company",
                "description": "Travel",
                "phone": "+79990000001",
                "email": "tour@example.com",
                "city": "Moscow",
                "idempotency_key": "generate-tour",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="generate-tour",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["selected_template"]["id"], tourism_template.id)
        self.assertEqual(response.data["site"]["status"], Site.Status.DRAFT)

    def test_generate_site_is_idempotent(self):
        payload = {
            "category_id": self.category.id,
            "company_name": "Repeat Company",
            "idempotency_key": "generate-repeat",
        }

        first = self.client.post(reverse("website-template-generate"), payload, format="json", HTTP_IDEMPOTENCY_KEY="generate-repeat")
        second = self.client.post(reverse("website-template-generate"), payload, format="json", HTTP_IDEMPOTENCY_KEY="generate-repeat")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["site"]["id"], second.data["site"]["id"])

    def test_generate_site_returns_error_when_category_has_no_templates(self):
        empty_category = WebsiteTemplateCategory.objects.create(name="Empty", slug="empty")

        response = self.client.post(
            reverse("website-template-generate"),
            {"category_id": empty_category.id, "company_name": "Empty Company"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "category_has_no_templates")

    def test_regenerate_design_excludes_current_template(self):
        alternate_site = Site.objects.create(
            owner=self.source_owner,
            name="Alt",
            slug="alt-template-source",
            builder_template_key="services-landing",
            builder_config={"company_name": "Alt"},
        )
        SiteSection.objects.create(site=alternate_site, title="Hero", key="hero", section_type="hero")
        alternate_template = WebsiteTemplate.objects.create(
            name="Alt template",
            slug="alt-template",
            category=self.category,
            source_site=alternate_site,
            snapshot_config=build_site_snapshot(alternate_site),
            is_published=True,
            is_active=True,
        )
        create_response = self.create_from_template(company_name="Regenerate", key="regen-create")
        site_id = create_response.data["id"]

        response = self.client.post(
            reverse("site-regenerate-design", kwargs={"site_id": site_id}),
            {"exclude_template_ids": [self.template.id], "idempotency_key": "regen-design"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="regen-design",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["selected_template"]["id"], alternate_template.id)
        self.assertEqual(Site.objects.filter(owner=self.user, name="Regenerate").count(), 1)

    def test_catalog_returns_three_published_templates(self):
        WebsiteTemplate.objects.all().delete()
        for index, category_slug in enumerate(("business", "services", "tourism"), start=1):
            category = WebsiteTemplateCategory.objects.get(slug=category_slug)
            source = Site.objects.create(owner=self.source_owner, name=f"Source {index}", slug=f"source-{index}")
            SiteSection.objects.create(site=source, title="Hero", key="hero", section_type="hero")
            WebsiteTemplate.objects.create(
                name=f"Template {index}",
                slug=f"template-{index}",
                category=category,
                source_site=source,
                snapshot_config=build_site_snapshot(source),
                is_published=True,
                sort_order=index,
            )

        response = self.client.get(reverse("website-template-catalog"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["templates"]), 3)

    def test_legacy_site_template_model_remains_available(self):
        legacy_template = SiteTemplate.objects.create(
            key="legacy-hero",
            title="Legacy hero",
            category="hero",
            description="Existing builder template",
            preview_image="/media/legacy.jpg",
            component_key="hero-centered",
            schema={"fields": [{"key": "title", "type": "text"}]},
            default_config={"title": "Default"},
            is_active=True,
        )

        self.assertEqual(legacy_template.title, "Legacy hero")
        self.assertEqual(SiteTemplate.objects.get(key="legacy-hero").default_config["title"], "Default")
        self.assertFalse(WebsiteTemplate.objects.filter(slug="legacy-hero").exists())

    def test_selecting_template_creates_independent_site_copy(self):
        subscription_count = Subscription.objects.count()
        response = self.create_from_template(site_name="New Site")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        copy = Site.objects.get(id=response.data["id"])
        self.assertNotEqual(copy.id, self.source_site.id)
        self.assertEqual(copy.owner, self.user)
        self.assertEqual(copy.name, "New Site")
        self.assertEqual(copy.source, Site.SOURCE_TEMPLATE)
        self.assertEqual(copy.render_mode, Site.RENDER_MODE_BUILDER)
        self.assertEqual(copy.status, Site.Status.DRAFT)
        self.assertIn(copy.status, {choice[0] for choice in Site.Status.choices})
        self.assertEqual(copy.generation_status, Site.GenerationStatus.COMPLETED)
        self.assertIsNotNone(copy.generation_status)
        self.assertIn(copy.generation_status, {choice[0] for choice in Site.GenerationStatus.choices})
        self.assertEqual(copy.generation_progress, 100)
        self.assertIsNotNone(copy.generation_progress)
        self.assertGreaterEqual(copy.generation_progress, 0)
        self.assertLessEqual(copy.generation_progress, 100)
        self.assertEqual(copy.generation_error, "")
        self.assertEqual(copy.design_preset, Site.DesignPreset.WARM_NATURE)
        self.assertEqual(copy.builder_template_key, "services-landing")
        self.assertEqual(copy.builder_config, self.source_site.builder_config)
        self.assertIsNotNone(copy.public_id)
        copy.full_clean()
        for field in Site._meta.concrete_fields:
            if field.primary_key or field.auto_created or field.null:
                continue
            self.assertIsNotNone(
                getattr(copy, field.attname, None),
                f"Required Site field {field.name} must not be None",
            )
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["created_from_template"], self.template.slug)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["dashboard_url"], f"/sites/{copy.id}")
        self.assertEqual(response.data["editor_url"], f"/sites/{copy.id}/sections")
        self.assertEqual(self.source_site.owner, self.source_owner)
        self.assertNotEqual(copy.slug, self.source_site.slug)
        self.assertEqual(copy.domain, "")
        self.assertFalse(copy.is_active)
        self.assertFalse(copy.send_to_telegram)
        self.assertIsNone(copy.telegram_chat_id)
        self.assertNotEqual(copy.api_key, self.source_site.api_key)

        copied_section = SiteSection.objects.get(site=copy, key="hero")
        self.assertNotEqual(copied_section.id, self.source_section.id)
        self.assertEqual(copied_section.content["title"], "New Company")
        self.assertEqual(copied_section.content["phone"], "")
        self.assertEqual(copied_section.schema, self.source_section.schema)
        self.assertEqual(copied_section.settings, self.source_section.settings)
        self.assertFalse(SiteLead.objects.filter(site=copy).exists())
        self.assertFalse(Visit.objects.filter(site=copy).exists())
        self.assertFalse(TrackingEvent.objects.filter(visit__site=copy).exists())

        self.assertEqual(Subscription.objects.count(), subscription_count)

    def test_full_visual_snapshot_is_cloned_and_exposed_to_editor(self):
        source_builder_config = {
            "theme": {"colors": {"primary": "#176b45", "background": "#f7fbf8"}},
            "design_tokens": {
                "fonts": {"heading": "Manrope", "body": "Inter"},
                "spacing": {"section": 96},
            },
            "pages_config": {"home": {"title": "Главная", "path": "/"}},
            "pages": [{"key": "home", "title": "Главная", "path": "/"}],
            "site_settings": {"button_radius": 6},
        }
        self.source_site.builder_config = source_builder_config
        self.source_site.save(update_fields=["builder_config", "updated_at"])
        second_source_section = SiteSection.objects.create(
            site=self.source_site,
            title="Services",
            key="services",
            section_type="services",
            component_key="services-grid",
            order=2,
            schema={
                "fields": [
                    {"key": "title", "type": "text"},
                    {"key": "image", "type": "image"},
                ]
            },
            content={"title": "Наши услуги", "image": "/static/templates/services.webp"},
            settings={"styles": {"background": "#f7fbf8", "gap": 24}, "responsive": {"columns": 2}},
            seo={"title": "Услуги"},
        )
        self.template.snapshot_config = build_site_snapshot(self.source_site)
        self.template.save(update_fields=["snapshot_config", "updated_at"])

        response = self.create_from_template(company_name="Visual Company", key="full-visual")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        copy = Site.objects.get(pk=response.data["id"])
        self.assertEqual(copy.design_preset, self.source_site.design_preset)
        self.assertEqual(copy.builder_config, source_builder_config)
        self.assertIsNot(copy.builder_config, self.template.snapshot_config["site"]["builder_config"])
        self.assertEqual(
            list(copy.sections.order_by("order").values_list("key", "order")),
            [("hero", 1), ("services", 2)],
        )
        copied_services = copy.sections.get(key="services")
        self.assertNotEqual(copied_services.pk, second_source_section.pk)
        self.assertEqual(copied_services.component_key, "services-grid")
        self.assertEqual(copied_services.content, second_source_section.content)
        self.assertEqual(copied_services.settings, second_source_section.settings)
        self.assertEqual(copied_services.seo, second_source_section.seo)

        editor_response = self.client.get(reverse("admin-my-site-detail", kwargs={"site_id": copy.pk}))
        sections_response = self.client.get(reverse("admin-my-site-sections", kwargs={"site_id": copy.pk}))
        self.assertEqual(editor_response.status_code, status.HTTP_200_OK)
        self.assertEqual(editor_response.data["design_preset"], self.source_site.design_preset)
        self.assertEqual(editor_response.data["builder_config"], source_builder_config)
        self.assertEqual([item["key"] for item in sections_response.data], ["hero", "services"])

        copy.builder_config["theme"]["colors"]["primary"] = "#000000"
        copy.save(update_fields=["builder_config", "updated_at"])
        copied_services.settings["styles"]["background"] = "#ffffff"
        copied_services.save(update_fields=["settings", "updated_at"])
        self.template.refresh_from_db()
        self.assertEqual(
            self.template.snapshot_config["site"]["builder_config"]["theme"]["colors"]["primary"],
            "#176b45",
        )
        self.assertEqual(
            self.template.snapshot_config["sections"][1]["settings"]["styles"]["background"],
            "#f7fbf8",
        )

    def test_snapshot_sync_command_validates_and_updates_only_selected_template(self):
        original_source_config = self.source_site.builder_config
        self.source_site.builder_config = {
            "design_tokens": {"colors": {"accent": "#d4a72c"}},
            "pages": [{"key": "home", "path": "/"}],
        }
        self.source_site.save(update_fields=["builder_config", "updated_at"])
        output = StringIO()

        call_command(
            "sync_website_template_snapshot",
            template_id=self.template.pk,
            source_site_id=self.source_site.pk,
            dry_run=True,
            stdout=output,
        )
        self.template.refresh_from_db()
        self.assertNotEqual(self.template.snapshot_config["site"]["builder_config"], self.source_site.builder_config)

        call_command(
            "sync_website_template_snapshot",
            template_id=self.template.pk,
            source_site_id=self.source_site.pk,
            stdout=output,
        )
        self.template.refresh_from_db()
        self.source_site.refresh_from_db()
        self.assertEqual(self.template.snapshot_config["site"]["builder_config"], self.source_site.builder_config)
        self.assertEqual(self.template.snapshot_config["site"]["design_tokens"], {"colors": {"accent": "#d4a72c"}})
        self.assertEqual(self.template.snapshot_config["pages"], [{"key": "home", "path": "/"}])
        self.assertNotEqual(self.source_site.builder_config, original_source_config)

        with self.assertRaises(CommandError):
            call_command("sync_website_template_snapshot", template_id=999999, dry_run=True)

    def test_plain_site_create_gets_default_status(self):
        site = Site.objects.create(owner=self.source_owner, name="Plain site", slug="plain-site")

        self.assertEqual(site.status, Site.Status.DRAFT)
        self.assertIsNotNone(site.status)
        self.assertEqual(site.generation_status, Site.GenerationStatus.PENDING)
        self.assertIsNotNone(site.generation_status)
        self.assertEqual(site.generation_progress, 0)
        self.assertIsNotNone(site.generation_progress)
        self.assertEqual(site.generation_error, "")
        self.assertEqual(site.design_preset, Site.DesignPreset.CLEAN_BUSINESS)
        self.assertEqual(site.builder_config, {})

    def test_clone_integrity_error_does_not_leak_raw_database_error(self):
        self.client.raise_request_exception = False

        with patch(
            "apps.sites.website_templates.Site.save",
            side_effect=IntegrityError('null value in column "status" violates not-null constraint'),
        ):
            response = self.create_from_template(company_name="Broken", key="integrity-error")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "template_clone_failed")
        self.assertNotIn("IntegrityError", response.data["detail"])
        self.assertNotIn("null value in column", response.data["detail"])

    def test_old_snapshot_without_new_site_fields_is_normalized(self):
        self.template.snapshot_config = {
            "version": 1,
            "sections": [
                {
                    "title": "Hero",
                    "key": "hero",
                    "section_type": "hero",
                    "content": {"title": "Legacy snapshot"},
                }
            ],
        }
        self.template.save(update_fields=["snapshot_config", "updated_at"])

        response = self.create_from_template(company_name="Legacy Company", key="legacy-snapshot")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        copy = Site.objects.get(pk=response.data["id"])
        self.assertEqual(copy.design_preset, Site.DesignPreset.WARM_NATURE)
        self.assertEqual(copy.builder_config, {})
        self.assertEqual(copy.builder_template_key, "")
        self.assertEqual(copy.generation_status, Site.GenerationStatus.COMPLETED)
        self.assertEqual(copy.generation_progress, 100)
        self.assertEqual(copy.generation_error, "")

    def test_site_model_has_no_unhandled_required_fields(self):
        server_fields = {
            "name",
            "slug",
            "domain",
            "owner",
            "source",
            "render_mode",
            "status",
            "generation_status",
            "generation_progress",
            "generation_error",
            "design_preset",
            "public_id",
            "builder_template_key",
            "builder_config",
            "api_key",
            "send_to_telegram",
            "seo",
            "is_active",
        }
        required_without_default = {
            field.name
            for field in Site._meta.concrete_fields
            if not field.primary_key
            and not field.auto_created
            and not getattr(field, "auto_now", False)
            and not getattr(field, "auto_now_add", False)
            and not field.null
            and field.default is NOT_PROVIDED
        }

        self.assertEqual(required_without_default, {"name", "slug", "domain", "owner"})
        self.assertTrue(required_without_default.issubset(server_fields))

    def test_copy_and_source_do_not_change_each_other(self):
        response = self.create_from_template(company_name="Independent")
        copy = Site.objects.get(id=response.data["id"])
        copied_section = SiteSection.objects.get(site=copy, key="hero")

        copied_section.content = {"title": "Changed copy"}
        copied_section.save(update_fields=["content", "updated_at"])
        self.source_section.refresh_from_db()
        self.assertEqual(self.source_section.content["title"], "Leelabird")

        self.source_section.content = {"title": "Changed source"}
        self.source_section.save(update_fields=["content", "updated_at"])
        copied_section.refresh_from_db()
        self.assertEqual(copied_section.content["title"], "Changed copy")

    def test_source_changes_after_snapshot_do_not_change_created_site(self):
        self.source_section.content = {"title": "Changed live source"}
        self.source_section.save(update_fields=["content", "updated_at"])

        response = self.create_from_template(company_name="Snapshot Company")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        copy = Site.objects.get(id=response.data["id"])
        copied_section = SiteSection.objects.get(site=copy, key="hero")
        self.assertEqual(copied_section.content["title"], "Snapshot Company")

    def test_template_changes_do_not_change_existing_sites(self):
        response = self.create_from_template(company_name="Before", key="before")
        copy = Site.objects.get(id=response.data["id"])
        copied_section = SiteSection.objects.get(site=copy, key="hero")

        snapshot = self.template.snapshot_config
        snapshot["sections"][0]["content"] = {"title": "Changed template"}
        self.template.snapshot_config = snapshot
        self.template.save(update_fields=["snapshot_config", "updated_at"])

        copied_section.refresh_from_db()
        self.assertEqual(copied_section.content["title"], "Before")

    def test_two_users_can_clone_same_template_independently(self):
        first = self.create_from_template(company_name="First", key="first")
        other = get_user_model().objects.create_user(username="other-template-user", email="other@example.com")
        other_client = Client.objects.create(owner=other, name="Other", is_active=True)
        grant_business_analytics(other, client=other_client)
        self.client.force_authenticate(other)
        second = self.create_from_template(company_name="Second", key="second")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.data["id"], second.data["id"])
        self.assertNotEqual(first.data["slug"], second.data["slug"])

    def test_idempotency_key_does_not_create_duplicate_site(self):
        first = self.create_from_template(company_name="Idempotent")
        second = self.create_from_template(company_name="Idempotent")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(Site.objects.filter(owner=self.user, name="Idempotent").count(), 1)

    def test_body_idempotency_key_does_not_create_duplicate_site(self):
        payload = {
            "template_slug": self.template.slug,
            "company_name": "Body key",
            "site_name": "Body key site",
            "idempotency_key": "body-idempotency-key",
        }

        first = self.client.post(reverse("website-template-create-site", kwargs={"slug": self.template.slug}), payload, format="json")
        second = self.client.post(reverse("website-template-create-site", kwargs={"slug": self.template.slug}), payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["id"], second.data["id"])

    def test_inactive_template_cannot_be_used(self):
        self.template.is_published = False
        self.template.save(update_fields=["is_published"])

        response = self.create_from_template()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Site.objects.filter(owner=self.user).count(), 0)

    def test_inactive_category_hides_and_blocks_template(self):
        self.category.is_active = False
        self.category.save(update_fields=["is_active"])

        catalog = self.client.get(reverse("website-template-catalog"))
        create = self.create_from_template()

        self.assertEqual(catalog.status_code, status.HTTP_200_OK)
        self.assertEqual(catalog.data["templates"], [])
        self.assertEqual(create.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clone_error_rolls_back_created_site(self):
        initial_count = Site.objects.filter(owner=self.user).count()
        self.client.raise_request_exception = False

        with patch("apps.sites.website_templates.SiteSection.objects.bulk_create", side_effect=RuntimeError("boom")):
            response = self.create_from_template(company_name="Rollback", key="rollback")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "section_clone_failed")
        self.assertEqual(Site.objects.filter(owner=self.user).count(), initial_count)

    def test_invalid_snapshot_returns_readable_error(self):
        self.template.snapshot_config = {"version": 1, "sections": [None]}
        self.template.save(update_fields=["snapshot_config", "updated_at"])

        response = self.create_from_template(company_name="Invalid snapshot")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_unsupported_snapshot_version_is_rejected(self):
        self.template.snapshot_config = {
            "version": 999,
            "sections": [
                {
                    "key": "hero",
                    "section_type": "hero",
                    "component_key": "hero-centered",
                    "content": {},
                    "settings": {},
                }
            ],
        }
        self.template.save(update_fields=["snapshot_config", "updated_at"])

        response = self.create_from_template(company_name="Unsupported", key="unsupported-version")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "template_snapshot_version_unsupported")

    def test_seed_website_templates_creates_generation_templates_and_is_idempotent(self):
        WebsiteTemplate.objects.all().delete()

        call_command("seed_website_templates")
        call_command("seed_website_templates")

        self.assertEqual(WebsiteTemplate.objects.count(), 2)
        self.assertTrue(
            WebsiteTemplate.objects.filter(
                slug="art-stroy",
                category__slug="construction",
                source_site__slug="tracknode-template-art-stroy-source",
                is_active=True,
                is_published=True,
            ).exists()
        )
        self.assertTrue(
            WebsiteTemplate.objects.filter(
                slug="a-meditation",
                category__slug="tourism",
                source_site__slug="tracknode-template-a-meditation-source",
                is_active=True,
                is_published=True,
            ).exists()
        )
        self.assertFalse(WebsiteTemplate.objects.filter(preview_image__startswith="data:image").exists())

        for slug, key in (("art-stroy", "art-troy"), ("a-meditation", "a-meditation")):
            response = self.client.post(
                reverse("website-template-create-site", kwargs={"slug": slug}),
                {
                    "company_name": f"Company {slug}",
                    "site_name": f"Site {slug}",
                    "idempotency_key": f"create-{slug}",
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            created_site = Site.objects.get(id=response.data["id"])
            self.assertEqual(created_site.owner, self.user)
            self.assertEqual(created_site.status, Site.Status.DRAFT)
            self.assertEqual(created_site.builder_template_key, key)
            self.assertNotIn(created_site.slug, {"tracknode", "a-meditation", "novaya-konakova"})

    def test_seeded_generation_no_longer_returns_no_templates_for_construction_and_tourism(self):
        WebsiteTemplate.objects.all().delete()
        call_command("seed_website_templates")

        for category_slug, expected_key in (("construction", "art-troy"), ("tourism", "a-meditation")):
            category = WebsiteTemplateCategory.objects.get(slug=category_slug)
            response = self.client.post(
                reverse("website-template-generate"),
                {
                    "category_id": category.id,
                    "company_name": f"Company {category_slug}",
                    "description": "Generated description",
                    "phone": "+7 900 000-00-00",
                    "email": "hello@example.com",
                    "city": "Москва",
                    "idempotency_key": f"generate-{category_slug}",
                },
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"generate-{category_slug}",
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["site"]["builder_template_key"], expected_key)
            self.assertIn("/api/public/sites/", response.data["preview_url"])
            self.assertTrue(response.data["preview_url"].endswith("?preview=1"))
            created_site = Site.objects.get(id=response.data["site"]["id"])
            self.assertEqual(created_site.owner, self.user)
            self.assertEqual(created_site.status, Site.Status.DRAFT)
