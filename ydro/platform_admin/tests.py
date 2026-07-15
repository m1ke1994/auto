from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics.models import Visit
from apps.sites.models import Site, SiteLead
from tracker.models import Site as LegacySite, Visit as LegacyVisit


class PlatformAccessTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user("platform", password="pass")
        self.client_user = users.objects.create_user("client", password="pass")
        self.other_user = users.objects.create_user("other", password="pass")
        self.staff = users.objects.create_user("staff", password="pass", is_staff=True)
        self.site = Site.objects.create(name="Client site", slug="client-site", domain="client.test", owner=self.client_user)
        self.other_site = Site.objects.create(name="Other site", slug="other-site", domain="other.test", owner=self.other_user)
        self.owner.user_permissions.add(Permission.objects.get(codename="access_platform", content_type__app_label="platform_admin"))
        self.api = APIClient()

    def test_unauthenticated_gets_401(self):
        self.assertEqual(self.api.get("/api/platform/overview/").status_code, 401)

    def test_client_and_plain_staff_get_403(self):
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.get("/api/platform/sites/").status_code, 403)
        self.api.force_authenticate(self.staff)
        self.assertEqual(self.api.get("/api/platform/sites/").status_code, 403)

    def test_platform_owner_sees_all_sites_with_pagination(self):
        self.api.force_authenticate(self.owner)
        response = self.api.get("/api/platform/sites/?page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)

    def test_platform_owner_can_open_any_site_without_impersonation(self):
        self.api.force_authenticate(self.owner)
        response = self.api.get(f"/api/platform/sites/{self.other_site.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["view_as_owner"]["read_only"])
        self.assertIsNone(response.data["tracker_key"])

    def test_period_filter_changes_analytics(self):
        Visit.objects.create(site=self.site, session_id="today", visitor_id="one")
        Visit.objects.create(site=self.site, session_id="old", visitor_id="two", started_at=timezone.now() - timedelta(days=10))
        self.api.force_authenticate(self.owner)
        response = self.api.get("/api/platform/analytics/?period=7d")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["totals"]["visits"], 1)

    def test_legacy_tracker_traffic_is_not_reported_as_no_traffic(self):
        legacy_site = LegacySite.objects.create(token=self.site.api_key, domain=self.site.domain)
        LegacyVisit.objects.create(site=legacy_site, session_id="legacy", visitor_id="legacy-user")
        self.api.force_authenticate(self.owner)
        response = self.api.get("/api/platform/analytics/?period=7d")
        self.assertNotIn(self.site.id, [item["id"] for item in response.data["sites_without_traffic"]])

    def test_site_filter_scopes_sites_without_traffic(self):
        self.api.force_authenticate(self.owner)
        response = self.api.get(f"/api/platform/analytics/?period=7d&site={self.site.id}")
        self.assertEqual([item["id"] for item in response.data["sites_without_traffic"]], [self.site.id])

    def test_personal_leads_need_separate_permission(self):
        SiteLead.objects.create(site=self.site, name="Person", phone="+70000000000")
        self.api.force_authenticate(self.owner)
        self.assertEqual(self.api.get("/api/platform/leads/").status_code, 403)
        self.owner.user_permissions.add(Permission.objects.get(codename="view_platform_personal_data", content_type__app_label="platform_admin"))
        self.owner = get_user_model().objects.get(pk=self.owner.pk)
        self.api.force_authenticate(self.owner)
        self.assertEqual(self.api.get("/api/platform/leads/").status_code, 200)

    def test_me_exposes_permissions_not_identity_rules(self):
        self.api.force_authenticate(self.owner)
        response = self.api.get("/api/auth/me/")
        self.assertTrue(response.data["permissions"]["platform_access"])
        self.assertFalse(response.data["permissions"]["view_all_leads"])

    def test_tracker_key_needs_separate_permission(self):
        self.api.force_authenticate(self.owner)
        self.assertIsNone(self.api.get(f"/api/platform/sites/{self.site.id}/").data["tracker_key"])
        self.owner.user_permissions.add(Permission.objects.get(codename="view_platform_tracker_key", content_type__app_label="platform_admin"))
        self.owner = get_user_model().objects.get(pk=self.owner.pk)
        self.api.force_authenticate(self.owner)
        self.assertEqual(self.api.get(f"/api/platform/sites/{self.site.id}/").data["tracker_key"], self.site.api_key)

    def test_grant_and_revoke_command_is_idempotent(self):
        call_command("grant_platform_owner", self.client_user.username)
        call_command("grant_platform_owner", self.client_user.username)
        self.client_user = get_user_model().objects.get(pk=self.client_user.pk)
        self.assertTrue(self.client_user.has_perm("platform_admin.access_platform"))
        call_command("grant_platform_owner", self.client_user.username, revoke=True)
        self.client_user = get_user_model().objects.get(pk=self.client_user.pk)
        self.assertFalse(self.client_user.has_perm("platform_admin.access_platform"))
