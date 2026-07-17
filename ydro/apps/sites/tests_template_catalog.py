from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.urls import reverse
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

    def test_plain_site_create_gets_default_status(self):
        site = Site.objects.create(owner=self.source_owner, name="Plain site", slug="plain-site")

        self.assertEqual(site.status, Site.Status.DRAFT)
        self.assertIsNotNone(site.status)

    def test_clone_integrity_error_does_not_leak_raw_database_error(self):
        self.client.raise_request_exception = False

        with patch(
            "apps.sites.website_templates.Site.objects.create",
            side_effect=IntegrityError('null value in column "status" violates not-null constraint'),
        ):
            response = self.create_from_template(company_name="Broken", key="integrity-error")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "template_clone_failed")
        self.assertNotIn("IntegrityError", response.data["detail"])
        self.assertNotIn("null value in column", response.data["detail"])

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

    def test_seed_website_templates_uses_real_source_slugs_and_is_idempotent(self):
        WebsiteTemplate.objects.all().delete()
        for slug in ("tracknode", "a-meditation", "novaya-konakova"):
            site = Site.objects.create(owner=self.source_owner, name=slug, slug=slug)
            SiteSection.objects.create(site=site, title="Hero", key="hero", section_type="hero")

        call_command("seed_website_templates")
        call_command("seed_website_templates")

        self.assertEqual(WebsiteTemplate.objects.count(), 3)
        self.assertTrue(WebsiteTemplate.objects.filter(slug="saas-digital-service", source_site__slug="tracknode").exists())
        self.assertTrue(
            WebsiteTemplate.objects.filter(slug="expert-practice-consulting", source_site__slug="a-meditation").exists()
        )
        self.assertTrue(
            WebsiteTemplate.objects.filter(slug="country-retreat-events", source_site__slug="novaya-konakova").exists()
        )
        self.assertFalse(WebsiteTemplate.objects.filter(preview_image__startswith="data:image").exists())

        for slug in ("saas-digital-service", "expert-practice-consulting", "country-retreat-events"):
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
            self.assertEqual(Site.objects.get(id=response.data["id"]).owner, self.user)
