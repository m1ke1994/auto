from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from clients.models import Client
from config.celery import app
from seo_audit.models import SEOPage, SiteSEOAudit
from seo_audit.tasks import run_site_audit_task


class SEOAuditTaskTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="seo-task-user",
            email="seo-task-user@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=user, name="SEO Task Client")
        self.audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            requested_by=user,
            domain="example.com",
            target_url="https://example.com/",
        )

    def test_task_is_registered_in_celery_worker_imports(self):
        app.loader.import_default_modules()
        self.assertIn("seo_audit.run_site_audit", app.tasks)

    @patch("seo_audit.tasks.recalculate_audit_score")
    @patch("seo_audit.tasks.crawl_site_audit")
    def test_task_moves_pending_to_running_and_done(self, mocked_crawl, mocked_recalculate):
        def crawl(audit, **_kwargs):
            audit.refresh_from_db()
            self.assertEqual(audit.status, SiteSEOAudit.Status.RUNNING)
            SEOPage.objects.create(audit=audit, url="https://example.com/", status_code=200)
            audit.pages_count = 1
            audit.seo_score = 87
            audit.save(update_fields=["pages_count", "seo_score"])

        mocked_crawl.side_effect = crawl
        run_site_audit_task.apply(args=[self.audit.id], task_id="seo-task-success").get()

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, SiteSEOAudit.Status.DONE)
        self.assertEqual(self.audit.celery_task_id, "seo-task-success")
        self.assertEqual(self.audit.pages_count, 1)
        self.assertEqual(self.audit.error_message, "")
        self.assertIsNotNone(self.audit.finished_at)
        mocked_recalculate.assert_called_once()

    @patch("seo_audit.tasks.crawl_site_audit", side_effect=RuntimeError("crawler exploded"))
    def test_crawler_error_moves_running_to_error(self, _mocked_crawl):
        started_before = timezone.now()
        run_site_audit_task.apply(args=[self.audit.id], task_id="seo-task-failure").get()

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, SiteSEOAudit.Status.ERROR)
        self.assertEqual(self.audit.celery_task_id, "seo-task-failure")
        self.assertIn("crawler exploded", self.audit.error_message)
        self.assertIsNotNone(self.audit.finished_at)
        self.assertGreaterEqual(self.audit.finished_at, started_before)
