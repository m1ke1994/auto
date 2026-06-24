import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.sites.models import Site
from clients.models import Client
from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.services.pdf_report import _sanitize_text, build_competitor_analysis_pdf
from config.celery import app as celery_app


class CompetitorAnalysisApiTests(TestCase):
    def setUp(self):
        self._media_root = tempfile.mkdtemp()
        self._override = override_settings(MEDIA_ROOT=self._media_root)
        self._override.enable()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="competitor-owner",
            email="competitor-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Competitor Owner")
        self.site = Site.objects.create(
            name="Example Site",
            slug="example-site",
            domain="example.com",
            owner=self.user,
            is_active=True,
        )
        self.other_user = user_model.objects.create_user(
            username="competitor-other",
            email="competitor-other@example.com",
            password="pass12345",
        )
        Client.objects.create(owner=self.other_user, name="Other Owner")

        self.http = APIClient()
        self.http.force_authenticate(user=self.user)

    def tearDown(self):
        self._override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)

    @patch("competitor_analysis.tasks.run_competitor_analysis_task.delay")
    def test_site_owner_can_create_analysis_with_normalized_domains(self, mocked_delay):
        response = self.http.post(
            f"/api/admin/sites/{self.site.id}/competitors/analyze/",
            {
                "user_domain": "https://www.example.com/",
                "competitor_domain": "https://www.competitor-one.ru/path",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        analysis = CompetitorAnalysis.objects.get(id=payload["id"])
        self.assertEqual(analysis.site_id, self.site.id)
        self.assertEqual(analysis.client_id, self.client_obj.id)
        self.assertEqual(analysis.user_domain, "example.com")
        self.assertEqual(analysis.competitor_domain, "competitor-one.ru")
        self.assertEqual(analysis.competitors, ["competitor-one.ru"])
        self.assertEqual(payload["user_domain"], "example.com")
        self.assertEqual(payload["competitor_domain"], "competitor-one.ru")
        mocked_delay.assert_called_once_with(analysis.id)

    @patch("competitor_analysis.tasks.run_competitor_analysis_task.delay")
    def test_create_analysis_supports_legacy_single_competitor(self, mocked_delay):
        response = self.http.post(
            f"/api/admin/sites/{self.site.id}/competitors/analyze/",
            {"competitors": ["https://www.competitor-one.ru/path"]},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        analysis = CompetitorAnalysis.objects.get(id=response.json()["id"])
        self.assertEqual(analysis.user_domain, "example.com")
        self.assertEqual(analysis.competitor_domain, "competitor-one.ru")
        self.assertEqual(analysis.competitors, ["competitor-one.ru"])
        mocked_delay.assert_called_once_with(analysis.id)

    def test_celery_app_registers_competitor_analysis_task(self):
        self.assertIn("competitor_analysis.run", celery_app.tasks)

    def test_create_analysis_rejects_more_than_one_legacy_competitor(self):
        response = self.http.post(
            f"/api/admin/sites/{self.site.id}/competitors/analyze/",
            {"competitors": ["a.ru", "b.ru"]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_create_analysis_rejects_private_and_local_targets(self):
        for value in ("localhost", "127.0.0.1", "0.0.0.0", "file:///tmp/report.html", "ftp://example.com"):
            response = self.http.post(
                f"/api/admin/sites/{self.site.id}/competitors/analyze/",
                {"user_domain": "example.com", "competitor_domain": value},
                format="json",
            )
            self.assertEqual(response.status_code, 400, value)

    def test_create_analysis_requires_both_new_domain_fields(self):
        response = self.http.post(
            f"/api/admin/sites/{self.site.id}/competitors/analyze/",
            {"user_domain": "example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_pdf_download_is_limited_to_site_owner(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.COMPLETED,
        )
        analysis.pdf_file.save("competitor-analysis-test.pdf", ContentFile(b"%PDF-1.4\n%test\n"), save=True)

        own_response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(own_response.status_code, 200)
        self.assertIn("application/pdf", own_response["Content-Type"])
        self.assertTrue(b"".join(own_response.streaming_content).startswith(b"%PDF"))

        self.http.force_authenticate(user=self.other_user)
        foreign_response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(foreign_response.status_code, 404)

    def test_pdf_download_returns_404_when_storage_file_is_missing(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.COMPLETED,
        )
        analysis.pdf_file.name = "competitor-analysis/site-1/missing.pdf"
        analysis.save(update_fields=["pdf_file"])

        response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("PDF", response.json()["detail"])

    def test_pdf_download_waits_for_completed_status(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.RUNNING,
        )
        analysis.pdf_file.save("competitor-analysis-running.pdf", ContentFile(b"%PDF-1.4\n%test\n"), save=True)

        response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )

        self.assertEqual(response.status_code, 409)

    @patch("competitor_analysis.views.current_app.control.revoke")
    def test_site_owner_can_cancel_active_analysis(self, mocked_revoke):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.RUNNING,
            celery_task_id="task-123",
        )

        response = self.http.post(f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/cancel/")

        self.assertEqual(response.status_code, 200)
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, CompetitorAnalysis.Status.CANCELED)
        self.assertIsNotNone(analysis.finished_at)
        mocked_revoke.assert_called_once_with("task-123", terminate=True, signal="SIGTERM")

    def test_other_user_cannot_cancel_foreign_analysis(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.RUNNING,
        )

        self.http.force_authenticate(user=self.other_user)
        response = self.http.post(f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/cancel/")

        self.assertEqual(response.status_code, 404)

    def test_pdf_text_sanitizer_repairs_common_mojibake(self):
        broken_text = "\u00d0\u009d\u00d0\u00be\u00d0\u00b2\u00d0\u00be\u00d0\u00b5 \u00d0\u009a\u00d0\u00be\u00d0\u00bd\u00d0\u00b0\u00d0\u00ba\u00d0\u00be\u00d0\u00b2\u00d0\u00be"
        self.assertEqual(_sanitize_text(broken_text), "Новое Конаково")

    def test_pdf_report_builds_with_cyrillic_text(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            user_domain="example.com",
            competitor_domain="competitor.ru",
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.COMPLETED,
        )
        payload = {
            "user_domain": "example.com",
            "competitor_domain": "competitor.ru",
            "items": [
                {
                    "role": "own",
                    "domain": "example.com",
                    "seo_score": 88,
                    "errors_count": 1,
                    "high_issues": 1,
                    "medium_issues": 0,
                    "low_issues": 0,
                    "title": "Новое Конаково",
                    "description": "Описание проекта",
                    "h1": "",
                    "h2_count": 0,
                    "robots_txt": True,
                    "sitemap_xml": True,
                    "https": True,
                    "issues": [
                        {
                            "type": "missing_h1",
                            "title": "Нет главного заголовка страницы (H1).",
                            "severity": "high",
                            "page_url": "https://example.com/",
                            "recommendation": "Добавьте один понятный H1 на главную страницу.",
                        }
                    ],
                },
                {
                    "role": "competitor",
                    "domain": "competitor.ru",
                    "seo_score": 92,
                    "errors_count": 0,
                    "title": "Конкурент",
                    "description": "Описание конкурента",
                    "h1": "Главный заголовок",
                    "h2_count": 2,
                    "robots_txt": True,
                    "sitemap_xml": True,
                    "https": True,
                    "issues": [],
                },
            ],
            "recommendations": {
                "critical": ["Добавьте один понятный H1 на главную страницу."],
                "important": [],
                "desired": [],
            },
            "improvement_plan": ["Добавить H1.", "Повторить анализ."],
        }

        pdf_bytes, filename = build_competitor_analysis_pdf(analysis=analysis, payload=payload)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertIn("competitor-analysis-example.com", filename)
