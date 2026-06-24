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
            {"competitors": ["https://www.competitor-one.ru/path", "", "competitor-two.ru"]},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        analysis = CompetitorAnalysis.objects.get(id=payload["id"])
        self.assertEqual(analysis.site_id, self.site.id)
        self.assertEqual(analysis.client_id, self.client_obj.id)
        self.assertEqual(analysis.competitors, ["competitor-one.ru", "competitor-two.ru"])
        mocked_delay.assert_called_once_with(analysis.id)

    def test_create_analysis_rejects_more_than_three_domains(self):
        response = self.http.post(
            f"/api/admin/sites/{self.site.id}/competitors/analyze/",
            {"competitors": ["a.ru", "b.ru", "c.ru", "d.ru"]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("competitors", response.json())

    def test_create_analysis_rejects_private_and_local_targets(self):
        for value in ("localhost", "127.0.0.1", "0.0.0.0", "file:///tmp/report.html", "ftp://example.com"):
            response = self.http.post(
                f"/api/admin/sites/{self.site.id}/competitors/analyze/",
                {"competitors": [value]},
                format="json",
            )
            self.assertEqual(response.status_code, 400, value)

    def test_pdf_download_is_limited_to_site_owner(self):
        analysis = CompetitorAnalysis.objects.create(
            site=self.site,
            client=self.client_obj,
            competitors=["competitor.ru"],
            status=CompetitorAnalysis.Status.DONE,
        )
        analysis.pdf_file.save("competitor-analysis-test.pdf", ContentFile(b"%PDF-1.4\n%test\n"), save=True)

        own_response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(own_response.status_code, 200)
        self.assertIn("application/pdf", own_response["Content-Type"])
        self.assertTrue(own_response.content.startswith(b"%PDF"))

        self.http.force_authenticate(user=self.other_user)
        foreign_response = self.http.get(
            f"/api/admin/sites/{self.site.id}/competitors/{analysis.id}/pdf/",
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(foreign_response.status_code, 404)
