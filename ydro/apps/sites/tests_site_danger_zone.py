from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ai_recommendations.models import AIRecommendationJob
from analytics_app.models import ClickEvent as LegacyClickEvent
from analytics_app.models import Event as LegacyEvent
from analytics_app.models import PageView as LegacyPageView
from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.mediafiles.models import MediaFile
from apps.sites.models import Site, SiteLead, SiteSection
from apps.sites.services import clear_site_analytics, delete_owned_site
from apps.sites.tracknode_site import TRACKNODE_SITE_SLUG
from clients.models import Client
from competitor_analysis.models import CompetitorAnalysis
from platform_admin.models import PlatformAuditLog
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from subscriptions.test_utils import grant_business_analytics
from tracker.models import Event as TrackerEvent
from tracker.models import PageView as TrackerPageView
from tracker.models import Site as TrackerSite
from tracker.models import Visit as TrackerVisit


class SiteDangerZoneApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ensure_production_site_columns()

    def setUp(self):
        self.drop_raw_site_dependency_tables()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("danger-owner", "owner@example.com", "secret12345")
        self.other_user = user_model.objects.create_user("danger-other", "other@example.com", "secret12345")
        self.platform_owner = user_model.objects.create_user("danger-platform", "platform@example.com", "secret12345")
        self.superuser = user_model.objects.create_superuser("danger-root", "root@example.com", "secret12345")
        self.platform_owner.user_permissions.add(
            Permission.objects.get(codename="access_platform", content_type__app_label="platform_admin")
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Owner")
        self.other_client = Client.objects.create(owner=self.other_user, name="Other")
        grant_business_analytics(self.user, client=self.client_obj)
        grant_business_analytics(self.other_user, client=self.other_client)

        self.site = Site.objects.create(
            name="Main Site",
            slug="main-site",
            domain="main.example.com",
            owner=self.user,
        )
        self.second_site = Site.objects.create(
            name="Second Site",
            slug="second-site",
            domain="second.example.com",
            owner=self.user,
        )
        self.foreign_site = Site.objects.create(
            name="Foreign Site",
            slug="foreign-site-danger",
            domain="foreign.example.com",
            owner=self.other_user,
        )

    def drop_raw_site_dependency_tables(self):
        suffix = " CASCADE" if connection.vendor == "postgresql" else ""
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS sites_unknownsitedependency{suffix}")
            cursor.execute(f"DROP TABLE IF EXISTS sites_websitetemplateclonerequest{suffix}")
            cursor.execute(f"DROP TABLE IF EXISTS sites_websitetemplate{suffix}")

    def create_template_clone_tables(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE sites_websitetemplate (
                    id integer PRIMARY KEY,
                    source_site_id integer NOT NULL REFERENCES sites_site(id) ON DELETE NO ACTION,
                    name varchar(255) NOT NULL DEFAULT ''
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE sites_websitetemplateclonerequest (
                    id integer PRIMARY KEY,
                    site_id integer NOT NULL REFERENCES sites_site(id) ON DELETE NO ACTION,
                    template_id integer NOT NULL REFERENCES sites_websitetemplate(id) ON DELETE NO ACTION,
                    idempotency_key varchar(255) NOT NULL DEFAULT ''
                )
                """
            )

    def raw_count(self, table, where="", params=None):
        query = f"SELECT COUNT(*) FROM {table}"
        if where:
            query = f"{query} WHERE {where}"
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            return int(cursor.fetchone()[0] or 0)

    @classmethod
    def ensure_production_site_columns(cls):
        with connection.cursor() as cursor:
            columns = {column.name for column in connection.introspection.get_table_description(cursor, "sites_site")}
            for column, definition in (
                ("source", "varchar(32)"),
                ("render_mode", "varchar(32)"),
                ("status", "varchar(32)"),
            ):
                if column not in columns:
                    cursor.execute(f"ALTER TABLE sites_site ADD COLUMN {column} {definition}")

    def set_production_site_meta(self, site, *, source="template", render_mode="builder", status_value="draft"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE sites_site SET source = %s, render_mode = %s, status = %s WHERE id = %s",
                [source, render_mode, status_value, site.id],
            )

    def mark_technical_template_source(self, site):
        self.set_production_site_meta(site, source="template", render_mode="builder", status_value="draft")

    def mark_legacy_public_site(self, site):
        self.set_production_site_meta(site, source="legacy", render_mode="legacy", status_value="published")

    def create_production_catalog_fixture(self):
        user_model = get_user_model()
        owners = {
            "leelabird": user_model.objects.create_user(
                "production-owner-19",
                "production-owner-19@example.com",
                "secret12345",
            ),
            "konakovo": user_model.objects.create_user(
                "production-owner-21",
                "production-owner-21@example.com",
                "secret12345",
            ),
            "tracknode": user_model.objects.create_user(
                "production-owner-22",
                "production-owner-22@example.com",
                "secret12345",
            ),
        }
        for owner in owners.values():
            grant_business_analytics(owner)

        sites = {
            "leelabird": Site.objects.create(
                name="Leelabird",
                slug="a-meditation",
                domain="leelabird.ru",
                owner=owners["leelabird"],
                is_active=True,
            ),
            "konakovo": Site.objects.create(
                name="Novoe Konakovo",
                slug="novaya-konakova",
                domain="novoe-konakovo.ru",
                owner=owners["konakovo"],
                is_active=True,
            ),
            "tracknode": Site.objects.create(
                name="TrackNode",
                slug=TRACKNODE_SITE_SLUG,
                domain="tracknode.ru",
                owner=owners["tracknode"],
                is_active=True,
            ),
            "portfolio": Site.objects.create(
                name="Portfolio Alexander",
                slug="my-portfolio",
                domain="tishechkinalexandr.ru",
                owner=owners["tracknode"],
                is_active=True,
            ),
        }
        for site in sites.values():
            self.mark_legacy_public_site(site)

        technical_sites = {
            "art_stroy": Site.objects.create(
                name="Art Stroy",
                slug="tracknode-template-art-stroy-source",
                domain="",
                owner=self.user,
                is_active=False,
            ),
            "a_meditation": Site.objects.create(
                name="A Meditation",
                slug="tracknode-template-a-meditation-source",
                domain="",
                owner=self.user,
                is_active=False,
            ),
        }
        for site in technical_sites.values():
            self.mark_technical_template_source(site)

        with connection.cursor() as cursor:
            for template_id, site in (
                (901, sites["tracknode"]),
                (902, sites["leelabird"]),
                (903, sites["konakovo"]),
                (904, technical_sites["art_stroy"]),
                (905, technical_sites["a_meditation"]),
            ):
                cursor.execute(
                    "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                    [template_id, site.id, site.name],
                )

        return owners, sites, technical_sites

    def assert_client_site_endpoints_available(self, user, site):
        self.client.force_authenticate(user)
        checks = (
            self.detail_url(site),
            reverse("admin-site-analytics-summary", kwargs={"site_id": site.id}),
            reverse("admin-site-telegram-status", kwargs={"site_id": site.id}),
            reverse("admin-my-site-sections", kwargs={"site_id": site.id}),
        )
        for url in checks:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)

        leads_response = self.client.get(reverse("admin-leads-list"), {"site_id": site.id})
        self.assertEqual(leads_response.status_code, status.HTTP_200_OK)

    def clear_url(self, site=None):
        return reverse("admin-my-site-analytics-clear", kwargs={"site_id": (site or self.site).id})

    def detail_url(self, site=None):
        return reverse("admin-my-site-detail", kwargs={"site_id": (site or self.site).id})

    def list_url(self):
        return reverse("admin-my-sites")

    def seed_analytics(self, site, *, session_id="session-1", visitor_id="visitor-1"):
        now = timezone.now()
        visit = Visit.objects.create(site=site, session_id=session_id, visitor_id=visitor_id, started_at=now)
        PageView.objects.create(visit=visit, url=f"https://{site.domain}/", pathname="/", timestamp=now)
        TrackingEvent.objects.create(visit=visit, type="click", payload={"path": "/"}, timestamp=now)

        tracker_site = TrackerSite.objects.create(token=site.api_key, domain=site.domain)
        tracker_visit = TrackerVisit.objects.create(
            site=tracker_site,
            session_id=session_id,
            visitor_id=visitor_id,
            started_at=now,
        )
        TrackerPageView.objects.create(visit=tracker_visit, url=f"https://{site.domain}/", timestamp=now)
        TrackerEvent.objects.create(visit=tracker_visit, type="click", payload={"path": "/"}, timestamp=now)

        LegacyPageView.objects.create(
            client=self.client_obj if site.owner_id == self.user.id else self.other_client,
            visitor_id=visitor_id,
            session_id=session_id,
            url=f"https://{site.domain}/pricing",
            pathname="/pricing",
        )
        LegacyEvent.objects.create(
            client=self.client_obj if site.owner_id == self.user.id else self.other_client,
            visitor_id=visitor_id,
            event_type=LegacyEvent.EventType.FORM_SUBMIT,
            page_url=f"https://{site.domain}/pricing",
        )
        LegacyClickEvent.objects.create(
            client=self.client_obj if site.owner_id == self.user.id else self.other_client,
            visitor_id=visitor_id,
            session_id=session_id,
            page_pathname="/pricing",
            element_text="CTA",
        )

        audit = SiteSEOAudit.objects.create(
            client=self.client_obj if site.owner_id == self.user.id else self.other_client,
            requested_by=site.owner,
            domain=site.domain,
            status=SiteSEOAudit.Status.DONE,
        )
        page = SEOPage.objects.create(audit=audit, url=f"https://{site.domain}/", status_code=200)
        SEOIssue.objects.create(page=page, issue_type=SEOIssue.IssueType.MISSING_TITLE, severity=SEOIssue.Severity.LOW, recommendation="Fix")
        CompetitorAnalysis.objects.create(site=site, client=self.client_obj if site.owner_id == self.user.id else self.other_client, status=CompetitorAnalysis.Status.COMPLETED)
        AIRecommendationJob.objects.create(
            site=site,
            user=site.owner,
            recommendation_type=AIRecommendationJob.Type.COMBINED,
            status=AIRecommendationJob.Status.COMPLETED,
            period_from=date(2026, 1, 1),
            period_to=date(2026, 1, 31),
        )

    def test_owner_clears_own_site_analytics(self):
        self.seed_analytics(self.site)
        SiteLead.objects.create(site=self.site, name="Lead", phone="+70000000000")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.clear_url(), {"confirmation": "ОЧИСТИТЬ"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["deleted_total"], 0)
        self.assertEqual(Visit.objects.filter(site=self.site).count(), 0)
        self.assertEqual(TrackerVisit.objects.filter(site__token=self.site.api_key).count(), 0)
        self.assertEqual(SiteLead.objects.filter(site=self.site).count(), 1)
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())
        self.assertTrue(PlatformAuditLog.objects.filter(action="site.analytics.clear", object_id=str(self.site.id)).exists())

    def test_unauthenticated_delete_returns_unauthorized(self):
        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_owner_gets_own_site(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.site.id)
        self.assertEqual(response.data["name"], self.site.name)
        self.assertEqual(response.data["owner_id"], self.user.id)
        self.assertTrue(response.data["capabilities"]["clear_analytics"])
        self.assertTrue(response.data["capabilities"]["delete"])

    def test_my_sites_list_is_owner_scoped_for_regular_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data]
        self.assertIn(self.site.id, ids)
        self.assertIn(self.second_site.id, ids)
        self.assertNotIn(self.foreign_site.id, ids)

    def test_global_admins_can_see_and_open_foreign_sites(self):
        for admin_user in (self.superuser, self.platform_owner):
            self.client.force_authenticate(admin_user)
            list_response = self.client.get(self.list_url())
            detail_response = self.client.get(self.detail_url(self.foreign_site))

            self.assertEqual(list_response.status_code, status.HTTP_200_OK)
            self.assertIn(self.foreign_site.id, [row["id"] for row in list_response.data])
            self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
            self.assertEqual(detail_response.data["id"], self.foreign_site.id)
            self.assertEqual(detail_response.data["owner_id"], self.other_user.id)
            self.assertTrue(detail_response.data["capabilities"]["clear_analytics"])
            self.assertTrue(detail_response.data["capabilities"]["delete"])

    def test_owner_deletes_own_site(self):
        self.seed_analytics(self.site)
        SiteSection.objects.create(site=self.site, key="hero", title="Hero", schema={"fields": []})
        SiteLead.objects.create(site=self.site, name="Lead", phone="+70000000000")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())
        self.assertFalse(SiteLead.objects.filter(site_id=self.site.id).exists())
        self.assertFalse(SiteSection.objects.filter(site_id=self.site.id).exists())
        self.assertFalse(TrackerSite.objects.filter(token=self.site.api_key).exists())
        audit = PlatformAuditLog.objects.get(action="site.delete", object_id=str(self.site.id))
        self.assertIsNone(audit.site_id)
        self.assertEqual(audit.metadata["site"]["id"], self.site.id)
        self.assertEqual(response.data["site"]["id"], self.site.id)
        self.assertEqual(response.data["site"]["name"], self.site.name)

    def test_invalid_delete_confirmation_returns_bad_request_and_preserves_site(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": "wrong"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_confirmation")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_missing_delete_body_returns_bad_request_and_preserves_site(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_confirmation")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_clear_one_site_does_not_touch_second_site_of_same_user(self):
        self.seed_analytics(self.site, session_id="session-main")
        self.seed_analytics(self.second_site, session_id="session-second")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.clear_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Visit.objects.filter(site=self.site).count(), 0)
        self.assertEqual(Visit.objects.filter(site=self.second_site).count(), 1)
        self.assertEqual(LegacyPageView.objects.filter(client=self.client_obj, url__icontains=self.second_site.domain).count(), 1)

    def test_delete_one_site_does_not_touch_second_site_of_same_user(self):
        self.seed_analytics(self.site, session_id="session-main")
        self.seed_analytics(self.second_site, session_id="session-second")
        SiteLead.objects.create(site=self.second_site, name="Second", phone="+70000000001")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())
        self.assertTrue(Site.objects.filter(id=self.second_site.id).exists())
        self.assertEqual(SiteLead.objects.filter(site=self.second_site).count(), 1)
        self.assertEqual(Visit.objects.filter(site=self.second_site).count(), 1)

    def test_user_cannot_delete_foreign_site(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(self.foreign_site), {"confirmation": self.foreign_site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Site.objects.filter(id=self.foreign_site.id).exists())

    def test_user_cannot_clear_foreign_site_analytics(self):
        self.seed_analytics(self.foreign_site, session_id="foreign-session")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.clear_url(self.foreign_site), {"confirmation": "ОЧИСТИТЬ"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Visit.objects.filter(site=self.foreign_site).count(), 1)

    def test_global_admins_can_clear_foreign_site_analytics(self):
        for admin_user in (self.superuser, self.platform_owner):
            target = Site.objects.create(
                name=f"Foreign Clear {admin_user.id}",
                slug=f"foreign-clear-{admin_user.id}",
                domain=f"foreign-clear-{admin_user.id}.example.com",
                owner=self.other_user,
            )
            neighbor = Site.objects.create(
                name=f"Neighbor Clear {admin_user.id}",
                slug=f"neighbor-clear-{admin_user.id}",
                domain=f"neighbor-clear-{admin_user.id}.example.com",
                owner=self.other_user,
            )
            self.seed_analytics(target, session_id=f"foreign-session-{admin_user.id}")
            self.seed_analytics(neighbor, session_id=f"neighbor-session-{admin_user.id}")
            SiteLead.objects.get_or_create(
                site=target,
                name=f"Lead {admin_user.id}",
                defaults={"phone": "+70000000000"},
            )
            self.client.force_authenticate(admin_user)

            response = self.client.delete(self.clear_url(target), {"confirmation": "ОЧИСТИТЬ"}, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Visit.objects.filter(site=target).count(), 0)
            self.assertEqual(Visit.objects.filter(site=neighbor).count(), 1)
            self.assertTrue(Site.objects.filter(id=target.id).exists())
            self.assertTrue(SiteLead.objects.filter(site=target).exists())
            audit = PlatformAuditLog.objects.filter(
                action="site.analytics.clear",
                object_id=str(target.id),
                actor=admin_user,
            ).latest("created_at")
            self.assertEqual(audit.metadata["site"]["owner_id"], self.other_user.id)

    def test_substituted_site_id_returns_not_found(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            self.detail_url(self.foreign_site),
            {"confirmation": self.site.name, "site_id": self.site.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_global_admins_can_delete_foreign_regular_site(self):
        for admin_user in (self.superuser, self.platform_owner):
            site = Site.objects.create(
                name=f"Foreign Delete {admin_user.id}",
                slug=f"foreign-delete-{admin_user.id}",
                domain=f"foreign-delete-{admin_user.id}.example.com",
                owner=self.other_user,
            )
            self.client.force_authenticate(admin_user)

            response = self.client.delete(self.detail_url(site), {"confirmation": site.name}, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(Site.objects.filter(id=site.id).exists())
            self.assertTrue(Site.objects.filter(id=self.site.id).exists())
            audit = PlatformAuditLog.objects.get(action="site.delete", object_id=str(site.id))
            self.assertEqual(audit.actor_id, admin_user.id)
            self.assertEqual(audit.metadata["site"]["owner_id"], self.other_user.id)

    def test_tracknode_system_site_is_not_deleted_with_client_site(self):
        tracknode = Site.objects.create(name="TrackNode", slug=TRACKNODE_SITE_SLUG, domain="tracknode.ru", owner=self.user)
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Site.objects.filter(id=tracknode.id).exists())

    def test_tracknode_system_site_cannot_be_deleted_directly(self):
        tracknode = Site.objects.create(name="TrackNode", slug=TRACKNODE_SITE_SLUG, domain="tracknode.ru", owner=self.user)
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(tracknode), {"confirmation": tracknode.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "protected_site")
        self.assertTrue(Site.objects.filter(id=tracknode.id).exists())

    def test_superuser_sees_tracknode_but_cannot_delete_it(self):
        tracknode = Site.objects.create(name="TrackNode", slug=TRACKNODE_SITE_SLUG, domain="tracknode.ru", owner=self.user)
        self.client.force_authenticate(self.superuser)

        detail = self.client.get(self.detail_url(tracknode))
        response = self.client.delete(self.detail_url(tracknode), {"confirmation": tracknode.name}, format="json")

        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertFalse(detail.data["capabilities"]["delete"])
        self.assertTrue(detail.data["capabilities"]["clear_analytics"])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "protected_site")
        self.assertTrue(Site.objects.filter(id=tracknode.id).exists())

    def test_site_leads_survive_analytics_clear(self):
        SiteLead.objects.create(site=self.site, name="Lead", phone="+70000000000")
        self.seed_analytics(self.site)
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.clear_url(), {"confirmation": "ОЧИСТИТЬ"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SiteLead.objects.filter(site=self.site).count(), 1)

    def test_site_leads_are_deleted_with_site(self):
        SiteLead.objects.create(site=self.site, name="Lead", phone="+70000000000")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SiteLead.objects.filter(site_id=self.site.id).exists())

    def test_repeated_clear_empty_analytics_returns_zero(self):
        self.client.force_authenticate(self.user)

        first = self.client.delete(self.clear_url(), {"confirmation": "ОЧИСТИТЬ"}, format="json")
        second = self.client.delete(self.clear_url(), {"confirmation": "ОЧИСТИТЬ"}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["deleted_total"], 0)

    def test_repeated_delete_returns_not_found(self):
        self.client.force_authenticate(self.user)

        first = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")
        second = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_404_NOT_FOUND)

    def test_transaction_rolls_back_when_clear_fails(self):
        self.seed_analytics(self.site)
        request = type("Request", (), {"user": self.user, "META": {}})()

        def fail_on_real_delete(queryset):
            if queryset.model is CompetitorAnalysis:
                deleted, _details = queryset.delete()
                self.assertGreater(deleted, 0)
                raise RuntimeError("forced failure")
            deleted, _details = queryset.delete()
            return deleted

        with patch("apps.sites.services._delete_queryset", side_effect=fail_on_real_delete):
            with self.assertRaises(RuntimeError):
                clear_site_analytics(site=self.site, request=request)

        self.assertEqual(CompetitorAnalysis.objects.filter(site=self.site).count(), 1)
        self.assertEqual(Visit.objects.filter(site=self.site).count(), 1)

    def test_delete_site_does_not_affect_other_client_data(self):
        self.seed_analytics(self.site, session_id="owner-session")
        self.seed_analytics(self.foreign_site, session_id="foreign-session")
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Site.objects.filter(id=self.foreign_site.id).exists())
        self.assertEqual(Visit.objects.filter(site=self.foreign_site).count(), 1)
        self.assertEqual(LegacyPageView.objects.filter(client=self.other_client, url__icontains=self.foreign_site.domain).count(), 1)

    def test_owner_deletes_template_cloned_client_site(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        other_clone_site = Site.objects.create(
            name="Other Clone",
            slug="other-clone",
            domain="other-clone.example.com",
            owner=self.user,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [101, source_site.id, "Art Stroy"],
            )
            cursor.execute(
                "INSERT INTO sites_websitetemplateclonerequest (id, site_id, template_id, idempotency_key) VALUES (%s, %s, %s, %s)",
                [201, self.site.id, 101, "clone-main"],
            )
            cursor.execute(
                "INSERT INTO sites_websitetemplateclonerequest (id, site_id, template_id, idempotency_key) VALUES (%s, %s, %s, %s)",
                [202, other_clone_site.id, 101, "clone-other"],
            )
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"]["template_clone_requests"], 1)
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())
        self.assertTrue(Site.objects.filter(id=source_site.id).exists())
        self.assertTrue(Site.objects.filter(id=other_clone_site.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [101]), 1)
        self.assertEqual(self.raw_count("sites_websitetemplateclonerequest", "id = %s", [201]), 0)
        self.assertEqual(self.raw_count("sites_websitetemplateclonerequest", "id = %s", [202]), 1)

        repeat = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")
        self.assertEqual(repeat.status_code, status.HTTP_404_NOT_FOUND)

    def test_template_source_sites_are_hidden_from_my_sites_for_owner_and_superuser(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [101, source_site.id, "Art Stroy"],
            )
            cursor.execute(
                "INSERT INTO sites_websitetemplateclonerequest (id, site_id, template_id, idempotency_key) VALUES (%s, %s, %s, %s)",
                [201, self.site.id, 101, "clone-main"],
            )

        self.client.force_authenticate(self.user)
        owner_response = self.client.get(self.list_url())
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertIn(self.site.id, [row["id"] for row in owner_response.data])
        self.assertNotIn(source_site.id, [row["id"] for row in owner_response.data])

        for admin_user in (self.superuser, self.platform_owner):
            self.client.force_authenticate(admin_user)
            admin_response = self.client.get(self.list_url())
            self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
            admin_ids = [row["id"] for row in admin_response.data]
            self.assertIn(self.site.id, admin_ids)
            self.assertIn(self.foreign_site.id, admin_ids)
            self.assertNotIn(source_site.id, admin_ids)

    def test_legacy_public_template_source_remains_visible_to_global_admins(self):
        self.create_template_clone_tables()
        legacy_source = Site.objects.create(
            name="Leelabird",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.other_user,
            is_active=True,
        )
        self.mark_legacy_public_site(legacy_source)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [107, legacy_source.id, "Leelabird"],
            )

        self.client.force_authenticate(self.user)
        owner_response = self.client.get(self.list_url())
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertNotIn(legacy_source.id, [row["id"] for row in owner_response.data])

        for admin_user in (self.superuser, self.platform_owner):
            self.client.force_authenticate(admin_user)
            response = self.client.get(self.list_url())
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            rows = {row["id"]: row for row in response.data}
            self.assertIn(legacy_source.id, rows)
            self.assertFalse(rows[legacy_source.id]["is_technical_template_source"])
            self.assertEqual(rows[legacy_source.id]["site_type"], "template_catalog_source")
            self.assertTrue(rows[legacy_source.id]["capabilities"]["delete"])

    def test_production_catalog_sources_remain_visible_to_existing_owners(self):
        self.create_template_clone_tables()
        owners, sites, technical_sites = self.create_production_catalog_fixture()

        expectations = (
            (owners["leelabird"], {sites["leelabird"].id}),
            (owners["konakovo"], {sites["konakovo"].id}),
            (owners["tracknode"], {sites["tracknode"].id, sites["portfolio"].id}),
        )
        hidden_ids = {site.id for site in technical_sites.values()}

        for owner, expected_ids in expectations:
            self.client.force_authenticate(owner)
            response = self.client.get(self.list_url())

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            ids = {row["id"] for row in response.data}
            self.assertTrue(expected_ids.issubset(ids))
            self.assertTrue(ids.isdisjoint(hidden_ids))
            for site_id in expected_ids:
                row = next(row for row in response.data if row["id"] == site_id)
                self.assertFalse(row["is_technical_template_source"])
                self.assertIn(row["site_type"], {"template_catalog_source", "system", "site"})

        self.assert_client_site_endpoints_available(owners["leelabird"], sites["leelabird"])
        self.assert_client_site_endpoints_available(owners["konakovo"], sites["konakovo"])
        self.assert_client_site_endpoints_available(owners["tracknode"], sites["tracknode"])
        self.assert_client_site_endpoints_available(owners["tracknode"], sites["portfolio"])

    def test_production_catalog_sources_are_not_visible_to_other_regular_users(self):
        self.create_template_clone_tables()
        owners, sites, _technical_sites = self.create_production_catalog_fixture()
        self.client.force_authenticate(owners["leelabird"])

        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data}
        self.assertIn(sites["leelabird"].id, ids)
        self.assertNotIn(sites["konakovo"].id, ids)
        self.assertNotIn(sites["tracknode"].id, ids)
        self.assertNotIn(sites["portfolio"].id, ids)
        self.assertEqual(self.client.get(self.detail_url(sites["konakovo"])).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": sites["konakovo"].id})).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_global_admins_see_production_real_sites_but_not_technical_sources(self):
        self.create_template_clone_tables()
        _owners, sites, technical_sites = self.create_production_catalog_fixture()
        regular_ids = {site.id for site in sites.values()}
        technical_ids = {site.id for site in technical_sites.values()}

        for admin_user in (self.superuser, self.platform_owner):
            self.client.force_authenticate(admin_user)
            response = self.client.get(self.list_url())

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            ids = {row["id"] for row in response.data}
            self.assertTrue(regular_ids.issubset(ids))
            self.assertTrue(ids.isdisjoint(technical_ids))
            for site in sites.values():
                self.assert_client_site_endpoints_available(admin_user, site)

    def test_empty_regular_user_gets_empty_site_list(self):
        empty_user = get_user_model().objects.create_user(
            "empty-site-owner",
            "empty-site-owner@example.com",
            "secret12345",
        )
        grant_business_analytics(empty_user)
        self.client.force_authenticate(empty_user)

        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_active_template_like_catalog_site_is_not_technical_source(self):
        self.create_template_clone_tables()
        active_source = Site.objects.create(
            name="Active Template Like Site",
            slug="tracknode-template-active-source",
            domain="",
            owner=self.user,
            is_active=True,
        )
        self.mark_technical_template_source(active_source)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [906, active_source.id, active_source.name],
            )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = {row["id"]: row for row in response.data}
        self.assertIn(active_source.id, rows)
        self.assertFalse(rows[active_source.id]["is_technical_template_source"])
        self.assertEqual(rows[active_source.id]["site_type"], "template_catalog_source")

    def test_technical_source_is_hidden_from_client_analytics_and_leads(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [907, source_site.id, "Art Stroy"],
            )
        SiteLead.objects.create(site=source_site, name="Source Lead", phone="+70000000000")

        for user in (self.user, self.superuser, self.platform_owner):
            self.client.force_authenticate(user)
            analytics_response = self.client.get(reverse("admin-site-analytics-summary", kwargs={"site_id": source_site.id}))
            leads_response = self.client.get(reverse("admin-leads-list"), {"site_id": source_site.id})

            self.assertEqual(analytics_response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(leads_response.status_code, status.HTTP_200_OK)
            self.assertEqual(leads_response.data, [])

    def test_template_source_site_get_and_delete_are_hidden_for_regular_owner(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="A Meditation Template Source",
            slug="tracknode-template-a-meditation-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [102, source_site.id, "A Meditation"],
            )

        self.client.force_authenticate(self.user)
        get_response = self.client.get(self.detail_url(source_site))
        delete_response = self.client.delete(self.detail_url(source_site), {"confirmation": source_site.name}, format="json")

        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Site.objects.filter(id=source_site.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [102]), 1)

    def test_superuser_cannot_delete_template_source_through_client_endpoint(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [103, source_site.id, "Art Stroy"],
            )

        for admin_user in (self.superuser, self.platform_owner):
            self.client.force_authenticate(admin_user)
            detail_response = self.client.get(self.detail_url(source_site))
            response = self.client.delete(self.detail_url(source_site), {"confirmation": source_site.name}, format="json")

            self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(detail_response.data["code"], "protected_template_source")
            self.assertEqual(detail_response.data["platform_url"], f"/platform/sites/{source_site.id}")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(response.data["code"], "protected_template_source")
            self.assertEqual(response.data["detail"], "Источник шаблона управляется через каталог шаблонов.")
        self.assertTrue(Site.objects.filter(id=source_site.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [103]), 1)

    def test_platform_admin_sees_template_source_site_separately(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [104, source_site.id, "Art Stroy"],
            )

        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/platform/sites/?search=Art%20Stroy%20Template%20Source")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(source_site.id, [row["id"] for row in response.data["results"]])

        detail_response = self.client.get(f"/api/platform/sites/{source_site.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["template_source"]["id"], 104)
        self.assertEqual(detail_response.data["template_source"]["cloned_sites_count"], 0)
        self.assertTrue(detail_response.data["template_source"]["is_technical_source"])

    def test_platform_admin_cannot_delete_template_used_by_cloned_sites(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="Art Stroy Template Source",
            slug="tracknode-template-art-stroy-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        other_clone_site = Site.objects.create(
            name="Other Clone",
            slug="other-clone",
            domain="other-clone.example.com",
            owner=self.user,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [105, source_site.id, "Art Stroy"],
            )
            cursor.execute(
                "INSERT INTO sites_websitetemplateclonerequest (id, site_id, template_id, idempotency_key) VALUES (%s, %s, %s, %s)",
                [205, self.site.id, 105, "clone-main"],
            )
            cursor.execute(
                "INSERT INTO sites_websitetemplateclonerequest (id, site_id, template_id, idempotency_key) VALUES (%s, %s, %s, %s)",
                [206, other_clone_site.id, 105, "clone-other"],
            )

        self.client.force_authenticate(self.superuser)
        response = self.client.delete("/api/platform/templates/105/", {"confirmation": "Art Stroy"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "template_has_cloned_sites")
        self.assertEqual(response.data["cloned_sites_count"], 2)
        self.assertTrue(Site.objects.filter(id=source_site.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [105]), 1)

    def test_platform_admin_deletes_unused_template_and_source_site(self):
        self.create_template_clone_tables()
        source_site = Site.objects.create(
            name="A Meditation Template Source",
            slug="tracknode-template-a-meditation-source",
            domain="",
            owner=self.user,
            is_active=False,
        )
        self.mark_technical_template_source(source_site)
        SiteSection.objects.create(site=source_site, key="hero", title="Hero", schema={"fields": []})
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [106, source_site.id, "A Meditation"],
            )

        self.client.force_authenticate(self.superuser)
        response = self.client.delete("/api/platform/templates/106/", {"confirmation": "A Meditation"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"]["templates"], 1)
        self.assertEqual(response.data["deleted"]["source_site"], 1)
        self.assertFalse(Site.objects.filter(id=source_site.id).exists())
        self.assertFalse(SiteSection.objects.filter(site_id=source_site.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [106]), 0)
        self.assertTrue(PlatformAuditLog.objects.filter(action="template.delete", object_id="106").exists())
        self.assertTrue(PlatformAuditLog.objects.filter(action="site.delete", object_id=str(source_site.id)).exists())

    def test_platform_admin_deletes_unused_legacy_source_template_without_deleting_site(self):
        self.create_template_clone_tables()
        legacy_source = Site.objects.create(
            name="Leelabird",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.other_user,
            is_active=True,
        )
        self.mark_legacy_public_site(legacy_source)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites_websitetemplate (id, source_site_id, name) VALUES (%s, %s, %s)",
                [108, legacy_source.id, "Leelabird"],
            )

        self.client.force_authenticate(self.superuser)
        response = self.client.delete("/api/platform/templates/108/", {"confirmation": "Leelabird"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"]["templates"], 1)
        self.assertEqual(response.data["deleted"]["source_site"], 0)
        self.assertEqual(response.data["deleted"]["source_site_preserved"], 1)
        self.assertTrue(Site.objects.filter(id=legacy_source.id).exists())
        self.assertEqual(self.raw_count("sites_websitetemplate", "id = %s", [108]), 0)
        self.assertFalse(PlatformAuditLog.objects.filter(action="site.delete", object_id=str(legacy_source.id)).exists())

    def test_unknown_site_dependency_returns_conflict_instead_of_500(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE sites_unknownsitedependency (
                    id integer PRIMARY KEY,
                    site_id integer NOT NULL REFERENCES sites_site(id) ON DELETE NO ACTION
                )
                """
            )
            cursor.execute(
                "INSERT INTO sites_unknownsitedependency (id, site_id) VALUES (%s, %s)",
                [301, self.site.id],
            )
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "site_has_dependencies")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())
        self.assertEqual(self.raw_count("sites_unknownsitedependency", "site_id = %s", [self.site.id]), 1)

    def test_running_background_task_returns_conflict(self):
        CompetitorAnalysis.objects.create(site=self.site, client=self.client_obj, status=CompetitorAnalysis.Status.RUNNING)
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "site_has_active_jobs")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_pending_competitor_task_returns_conflict(self):
        CompetitorAnalysis.objects.create(site=self.site, client=self.client_obj, status=CompetitorAnalysis.Status.PENDING)
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "site_has_active_jobs")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_running_seo_task_returns_conflict(self):
        SiteSEOAudit.objects.create(
            client=self.client_obj,
            requested_by=self.user,
            domain=self.site.domain,
            status=SiteSEOAudit.Status.RUNNING,
        )
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "site_has_active_jobs")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_queued_ai_task_returns_conflict(self):
        AIRecommendationJob.objects.create(
            site=self.site,
            user=self.user,
            recommendation_type=AIRecommendationJob.Type.COMBINED,
            status=AIRecommendationJob.Status.QUEUED,
            period_from=date(2026, 1, 1),
            period_to=date(2026, 1, 31),
        )
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "site_has_active_jobs")
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_delete_without_media_files_succeeds(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())

    def test_missing_physical_media_file_cleanup_does_not_fail_delete(self):
        MediaFile.objects.create(
            site=self.site,
            section_key="hero",
            field_key="image",
            file=SimpleUploadedFile("missing.jpg", b"content", content_type="image/jpeg"),
        )
        self.client.force_authenticate(self.user)

        with patch.object(MediaFile._meta.get_field("file").storage, "delete", side_effect=FileNotFoundError("missing")) as delete_file:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delete_file.assert_called_once()
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())
        self.assertFalse(MediaFile.objects.filter(site_id=self.site.id).exists())

    def test_file_cleanup_error_after_commit_does_not_return_false_500(self):
        MediaFile.objects.create(
            site=self.site,
            section_key="hero",
            field_key="image",
            file=SimpleUploadedFile("cleanup.jpg", b"content", content_type="image/jpeg"),
        )
        self.client.force_authenticate(self.user)

        with patch.object(MediaFile._meta.get_field("file").storage, "delete", side_effect=RuntimeError("storage denied")) as delete_file:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.delete(self.detail_url(), {"confirmation": self.site.name}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delete_file.assert_called_once()
        self.assertFalse(Site.objects.filter(id=self.site.id).exists())

    def test_delete_transaction_rolls_back_when_database_delete_fails(self):
        self.seed_analytics(self.site)
        request = type("Request", (), {"user": self.user, "META": {}})()

        def fail_on_real_delete(queryset):
            if queryset.model is LegacyEvent:
                deleted, _details = queryset.delete()
                self.assertGreater(deleted, 0)
                raise RuntimeError("forced failure")
            deleted, _details = queryset.delete()
            return deleted

        with patch("apps.sites.services._delete_queryset", side_effect=fail_on_real_delete):
            with self.assertRaises(RuntimeError):
                delete_owned_site(site=self.site, request=request)

        self.assertTrue(Site.objects.filter(id=self.site.id).exists())
        self.assertEqual(LegacyEvent.objects.filter(client=self.client_obj, page_url__icontains=self.site.domain).count(), 1)
        self.assertEqual(Visit.objects.filter(site=self.site).count(), 1)
