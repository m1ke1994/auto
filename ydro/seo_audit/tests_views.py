# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.sites.models import Site, SiteLead
from clients.models import Client
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from subscriptions.test_utils import grant_business_analytics


class SEOAuditViewsExtendedTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="seo-view-owner",
            email="seo-view-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="SEO Views Client")
        self.site = Site.objects.create(
            name="Leelabird",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.user,
            is_active=True,
        )
        grant_business_analytics(self.user, client=self.client_obj)
        self.staff_user = user_model.objects.create_user(
            username="seo-staff",
            email="seo-staff@example.com",
            password="pass12345",
            is_staff=True,
        )
        self.superuser = user_model.objects.create_superuser(
            username="seo-admin",
            email="seo-admin@example.com",
            password="pass12345",
        )
        self.platform_owner = user_model.objects.create_user(
            username="seo-platform-owner",
            email="seo-platform-owner@example.com",
            password="pass12345",
        )
        self.platform_owner.user_permissions.add(Permission.objects.get(codename="access_platform", content_type__app_label="platform_admin"))
        self.other_user = user_model.objects.create_user(
            username="seo-other",
            email="seo-other@example.com",
            password="pass12345",
        )
        self.other_client = Client.objects.create(owner=self.other_user, name="Other SEO Client")
        grant_business_analytics(self.other_user, client=self.other_client)
        self.inactive_user = user_model.objects.create_user(
            username="seo-inactive",
            email="seo-inactive@example.com",
            password="pass12345",
        )
        self.inactive_client = Client.objects.create(owner=self.inactive_user, name="Inactive SEO Client", is_active=False)
        self.inactive_site = Site.objects.create(
            name="Inactive Client Site",
            slug="inactive-client-site",
            domain="inactive.example.com",
            owner=self.inactive_user,
            is_active=True,
        )
        self.http = APIClient()
        self.http.force_authenticate(user=self.user)

    def _create_done_audit(self, *, domain: str, has_robots: bool, has_sitemap: bool, issue_type: str, severity: str):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain=domain,
            status=SiteSEOAudit.Status.DONE,
            has_robots_txt=has_robots,
            has_sitemap_xml=has_sitemap,
            pages_count=1,
            pages_with_speed_issues=1,
            pages_with_indexing_issues=1,
            seo_score=60,
            finished_at=timezone.now(),
        )
        page = SEOPage.objects.create(
            audit=audit,
            url=f"https://{domain}/",
            status_code=200,
            ttfb_ms=900,
            performance_score=55,
            speed_status=SEOPage.SpeedStatus.WARNING,
            indexability_status=SEOPage.IndexabilityStatus.UNKNOWN,
            title="Example title",
            description="Example description",
            h1="Example",
            h1_count=1,
            word_count=400,
            has_form=True,
            has_cta=True,
            has_phone_or_contact=False,
            has_messenger=False,
            has_offer_like_heading=True,
            has_benefits_block=False,
            has_faq=False,
            commercial_readiness_score=52,
            commercial_status=SEOPage.CommercialStatus.WARNING,
        )
        SEOIssue.objects.create(
            page=page,
            issue_type=issue_type,
            severity=severity,
            recommendation="-",
        )
        return audit

    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_active_site_owner_can_start_seo_audit_for_own_site(self, mocked_delay):
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.site.id, "domain": "https://leelabird.ru/"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.client_id, self.client_obj.id)
        self.assertEqual(audit.domain, "leelabird.ru")
        mocked_delay.assert_called_once_with(audit.id)

    @override_settings(ENABLE_BILLING=False)
    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_site_owner_without_client_gets_client_and_can_start_seo_audit(self, mocked_delay):
        user_model = get_user_model()
        owner_without_client = user_model.objects.create_user(
            username="seo-owner-without-client",
            email="seo-owner-without-client@example.com",
            password="pass12345",
        )
        site_without_client = Site.objects.create(
            name="Leelabird",
            slug="a-meditation-no-client",
            domain="leelabird.ru",
            owner=owner_without_client,
            is_active=True,
        )
        self.http.force_authenticate(user=owner_without_client)

        payload = {"site_id": site_without_client.id, "domain": "https://leelabird.ru/"}
        denied_response = self.http.post(
            "/api/mini/seo/start/",
            payload,
            format="json",
        )
        self.assertEqual(denied_response.status_code, 403)

        created_client = Client.objects.get(owner=owner_without_client)
        grant_business_analytics(owner_without_client, client=created_client)
        response = self.http.post("/api/mini/seo/start/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(created_client.is_active)
        self.assertEqual(created_client.name, site_without_client.name)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.client_id, created_client.id)
        mocked_delay.assert_called_once_with(audit.id)

    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_superuser_can_start_seo_audit_for_selected_site(self, mocked_delay):
        self.http.force_authenticate(user=self.superuser)
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.site.id, "domain": "leelabird.ru"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.client_id, self.client_obj.id)
        mocked_delay.assert_called_once_with(audit.id)

    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_staff_user_can_start_seo_audit_for_selected_site(self, mocked_delay):
        self.http.force_authenticate(user=self.staff_user)
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.site.id, "domain": "www.leelabird.ru"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.client_id, self.client_obj.id)
        self.assertEqual(audit.domain, "leelabird.ru")
        mocked_delay.assert_called_once_with(audit.id)

    def test_inactive_client_user_cannot_start_seo_audit(self):
        self.http.force_authenticate(user=self.inactive_user)
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.inactive_site.id, "domain": "inactive.example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_user_without_site_access_cannot_start_seo_audit(self):
        self.http.force_authenticate(user=self.other_user)
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.site.id, "domain": "leelabird.ru"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))])
    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_platform_owner_can_start_external_url_audit(self, mocked_delay, _mocked_dns):
        self.http.force_authenticate(user=self.platform_owner)

        response = self.http.post(
            "/api/mini/seo/start/",
            {"target_url": "https://example.com/path/?q=1"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.requested_by_id, self.platform_owner.id)
        self.assertEqual(audit.domain, "example.com")
        self.assertEqual(audit.target_url, "https://example.com/path/?q=1")
        self.assertEqual(audit.client.owner_id, self.platform_owner.id)
        mocked_delay.assert_called_once_with(audit.id)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("95.31.22.162", 0))])
    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_each_platform_owner_identity_can_start_novoe_konakovo_external_audit(self, mocked_delay, _mocked_dns):
        for user in (self.superuser, self.staff_user, self.platform_owner):
            with self.subTest(user=user.username):
                mocked_delay.reset_mock()
                self.http.force_authenticate(user=user)
                response = self.http.post(
                    "/api/mini/seo/start/",
                    {"target_url": "https://novoe-konakovo.ru/"},
                    format="json",
                )

                self.assertEqual(response.status_code, 201)
                payload = response.json()
                audit = SiteSEOAudit.objects.get(id=payload["audit_id"])
                self.assertEqual(payload["target_url"], "https://novoe-konakovo.ru/")
                self.assertEqual(audit.requested_by_id, user.id)
                self.assertEqual(audit.target_url, "https://novoe-konakovo.ru/")
                self.assertEqual(audit.domain, "novoe-konakovo.ru")
                self.assertNotEqual(audit.domain, self.site.domain)
                self.assertEqual(audit.client.owner_id, user.id)
                mocked_delay.assert_called_once_with(audit.id)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))])
    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_platform_owner_can_start_external_audit_through_regular_seo_endpoint(self, mocked_delay, _mocked_dns):
        self.http.force_authenticate(user=self.platform_owner)
        response = self.http.post(
            "/api/seo/start/",
            {"target_url": "https://external-not-in-sites.example/path"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
        self.assertEqual(audit.target_url, "https://external-not-in-sites.example/path")
        self.assertEqual(audit.domain, "external-not-in-sites.example")
        self.assertFalse(Site.objects.filter(domain="external-not-in-sites.example").exists())
        mocked_delay.assert_called_once_with(audit.id)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))])
    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_platform_owner_external_url_inputs_are_normalized_without_domain_requirement(self, mocked_delay, _mocked_dns):
        self.http.force_authenticate(user=self.platform_owner)
        cases = (
            ("https://craftum.com/", "https://craftum.com/", "craftum.com"),
            ("http://craftum.com/", "http://craftum.com/", "craftum.com"),
            ("craftum.com", "https://craftum.com/", "craftum.com"),
            ("www.craftum.com", "https://www.craftum.com/", "craftum.com"),
            ("https:/craftum.com/", "https://craftum.com/", "craftum.com"),
            ("http:/craftum.com/", "http://craftum.com/", "craftum.com"),
            ("https://novoe-konakovo.ru/", "https://novoe-konakovo.ru/", "novoe-konakovo.ru"),
        )
        for raw_url, normalized_url, domain in cases:
            with self.subTest(raw_url=raw_url):
                mocked_delay.reset_mock()
                payload = {"target_url": raw_url}
                if raw_url == "https:/craftum.com/":
                    payload["domain"] = ""
                response = self.http.post("/api/mini/seo/start/", payload, format="json")

                self.assertEqual(response.status_code, 201)
                self.assertNotIn("errors", response.json())
                audit = SiteSEOAudit.objects.get(id=response.json()["audit_id"])
                self.assertEqual(response.json()["target_url"], normalized_url)
                self.assertEqual(audit.target_url, normalized_url)
                self.assertEqual(audit.domain, domain)
                mocked_delay.assert_called_once_with(audit.id)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))])
    def test_regular_user_cannot_start_external_url_audit(self, _mocked_dns):
        response = self.http.post(
            "/api/mini/seo/start/",
            {"target_url": "https://example.com/"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    @patch("seo_audit.tasks.run_site_audit_task.delay")
    def test_platform_owner_external_url_rejects_localhost_with_clear_error_without_audit(self, mocked_delay):
        self.http.force_authenticate(user=self.platform_owner)
        response = self.http.post("/api/mini/seo/start/", {"target_url": "http://localhost/"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertIn("detail", response.json())
        self.assertFalse(SiteSEOAudit.objects.filter(target_url="http://localhost/").exists())
        mocked_delay.assert_not_called()

    def test_platform_owner_external_url_rejects_loopback_ip(self):
        self.http.force_authenticate(user=self.platform_owner)
        response = self.http.post("/api/mini/seo/start/", {"target_url": "http://127.0.0.1/"}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_platform_owner_external_url_rejects_private_ipv4_ranges(self):
        self.http.force_authenticate(user=self.platform_owner)
        for url in ("http://10.1.2.3/", "http://172.16.2.3/", "http://192.168.1.10/"):
            with self.subTest(url=url):
                response = self.http.post("/api/mini/seo/start/", {"target_url": url}, format="json")
                self.assertEqual(response.status_code, 400)

    def test_platform_owner_external_url_rejects_link_local_metadata_ip(self):
        self.http.force_authenticate(user=self.platform_owner)
        response = self.http.post("/api/mini/seo/start/", {"target_url": "http://169.254.169.254/"}, format="json")

        self.assertEqual(response.status_code, 400)

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.5", 0))])
    def test_platform_owner_external_url_rejects_dns_to_private_ip(self, _mocked_dns):
        self.http.force_authenticate(user=self.platform_owner)
        response = self.http.post("/api/mini/seo/start/", {"target_url": "https://private.example.com/"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())
        self.assertIn("target_url", response.json()["errors"])

    def test_regular_user_does_not_see_platform_owner_external_audits(self):
        platform_client = Client.objects.create(owner=self.platform_owner, name="Platform SEO")
        SiteSEOAudit.objects.create(
            client=platform_client,
            requested_by=self.platform_owner,
            domain="example.com",
            target_url="https://example.com/",
            status=SiteSEOAudit.Status.DONE,
        )

        response = self.http.get("/api/seo/audits/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"], [])

    def test_platform_owner_sees_own_external_audits(self):
        platform_client = Client.objects.create(owner=self.platform_owner, name="Platform SEO")
        audit = SiteSEOAudit.objects.create(
            client=platform_client,
            requested_by=self.platform_owner,
            domain="example.com",
            target_url="https://example.com/",
            status=SiteSEOAudit.Status.DONE,
        )
        self.http.force_authenticate(user=self.platform_owner)

        response = self.http.get("/api/seo/audits/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"][0]["audit_id"], audit.id)

    def test_selected_site_context_does_not_allow_other_domain(self):
        response = self.http.post(
            "/api/mini/seo/start/",
            {"site_id": self.site.id, "domain": "other.example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("выбранного сайта", response.json()["detail"])

    def test_site_context_limits_existing_audit_detail_to_selected_site_domain(self):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain="other.example.com",
            status=SiteSEOAudit.Status.DONE,
        )

        response = self.http.get(f"/api/mini/seo/{audit.id}/", {"site_id": self.site.id})

        self.assertEqual(response.status_code, 404)

    def test_analytics_and_site_leads_still_work_for_site_owner(self):
        SiteLead.objects.create(site=self.site, name="Lead", phone="+79990000000")

        analytics_response = self.http.get(f"/api/admin/my-sites/{self.site.id}/analytics/summary/")
        leads_response = self.http.get("/api/admin/leads/", {"site_id": self.site.id})

        self.assertEqual(analytics_response.status_code, 200)
        self.assertEqual(leads_response.status_code, 200)
        self.assertEqual(len(leads_response.json()), 1)

    def test_detail_payload_contains_product_sections(self):
        audit = self._create_done_audit(
            domain="details.example.com",
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )

        response = self.http.get(f"/api/seo/{audit.id}/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("fix_plan", payload)
        self.assertIn("issue_groups", payload)
        self.assertIn("commercial_summary", payload)
        self.assertIn("audit_history", payload)
        self.assertIn("comparison_preview", payload)
        self.assertIn("recommendations", payload)
        self.assertEqual(payload["recommendations"]["source"], "local")
        pages = payload.get("commercial_summary", {}).get("pages") or []
        self.assertTrue(len(pages) >= 1)
        page = pages[0]
        self.assertIn("has_conversion_path", page)
        self.assertIn("conversion_path_type", page)
        self.assertIn("conversion_signals", page)
        self.assertIn("commercial_explanation", page)
        self.assertIn("commercial_business_status", page)

    def test_history_endpoint_returns_done_rows_and_default_compare_id(self):
        domain = "history.example.com"
        old_audit = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current_audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        response = self.http.get(f"/api/seo/{current_audit.id}/history/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["audit_id"], current_audit.id)
        self.assertEqual(payload["domain"], domain)
        self.assertEqual(len(payload["rows"]), 1)
        self.assertEqual(payload["rows"][0]["audit_id"], old_audit.id)
        self.assertEqual(payload["default_compare_audit_id"], old_audit.id)

    def test_audits_list_pages_and_issues_endpoints(self):
        audit = self._create_done_audit(
            domain="list.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        list_response = self.http.get("/api/seo/audits/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["rows"][0]["audit_id"], audit.id)

        pages_response = self.http.get(f"/api/seo/{audit.id}/pages/")
        self.assertEqual(pages_response.status_code, 200)
        self.assertGreaterEqual(pages_response.json()["count"], 1)

        issues_response = self.http.get(f"/api/seo/{audit.id}/issues/?severity=medium")
        self.assertEqual(issues_response.status_code, 200)
        self.assertEqual(issues_response.json()["severity"], "medium")
        self.assertGreaterEqual(issues_response.json()["count"], 1)

    def test_compare_endpoint_returns_stub_when_previous_is_missing(self):
        audit = self._create_done_audit(
            domain="single-compare.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/compare/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["has_data"])
        self.assertIn("reason", payload)

    def test_compare_endpoint_returns_data_for_selected_audits(self):
        domain = "compare.example.com"
        previous = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{current.id}/compare/", {"with_audit_id": previous.id})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["has_data"])
        self.assertEqual(payload["with_audit_id"], previous.id)
        self.assertIn("score", payload)
        self.assertIn("new_issues_count", payload)
        self.assertIn("fixed_issues_count", payload)

    def test_ai_recommendations_endpoint_returns_local_payload(self):
        audit = self._create_done_audit(
            domain="ai-seo.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        response = self.http.get(f"/api/seo/{audit.id}/ai-recommendations/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["source"], "local")
        self.assertIn("items", payload)
        self.assertIn("summary", payload)

    def test_ai_recommendations_endpoint_ignores_force_refresh_and_returns_local_payload(self):
        audit = self._create_done_audit(
            domain="ai-refresh.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/ai-recommendations/?refresh=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "local")
        self.assertIn("items", payload)

    def test_export_endpoint_returns_pdf_report(self):
        domain = "export.example.com"
        previous = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(
            f"/api/seo/{current.id}/export/",
            {"with_audit_id": previous.id},
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn(".pdf", response["Content-Disposition"].lower())
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_endpoint_works_with_json_accept_too(self):
        domain = "export-json.example.com"
        audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/export/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_endpoint_works_with_browser_like_accept_header(self):
        domain = "export-browser.example.com"
        audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(
            f"/api/seo/{audit.id}/export/",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertTrue(response.content.startswith(b"%PDF"))
