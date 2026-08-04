from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
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
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("danger-owner", "owner@example.com", "secret12345")
        self.other_user = user_model.objects.create_user("danger-other", "other@example.com", "secret12345")
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

    def clear_url(self, site=None):
        return reverse("admin-my-site-analytics-clear", kwargs={"site_id": (site or self.site).id})

    def detail_url(self, site=None):
        return reverse("admin-my-site-detail", kwargs={"site_id": (site or self.site).id})

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

    def test_substituted_site_id_returns_not_found(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            self.detail_url(self.foreign_site),
            {"confirmation": self.site.name, "site_id": self.site.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
