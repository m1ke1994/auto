from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.sites.models import Site
from ai_recommendations.models import AIRecommendationJob
from ai_recommendations.payload import PERSONAL_KEYS, build_payload


@override_settings(AI_RECOMMENDATIONS_ENABLED=True, ENABLE_BILLING=False)
class AIRecommendationAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="test-pass-123")
        self.other = get_user_model().objects.create_user(username="other", password="test-pass-123")
        self.user.is_staff = True; self.user.save(update_fields=("is_staff",))
        self.other.is_staff = True; self.other.save(update_fields=("is_staff",))
        self.site = Site.objects.create(name="Test", slug="test-ai", domain="example.test", owner=self.user)
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_payload_contains_no_personal_keys(self):
        job = AIRecommendationJob.objects.create(site=self.site, user=self.user, recommendation_type="combined", period_from=date(2026, 6, 1), period_to=date(2026, 6, 30))
        payload = build_payload(job=job)
        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items(): yield key.lower(); yield from keys(child)
            elif isinstance(value, list):
                for child in value: yield from keys(child)
        assert not (set(keys(payload)) & PERSONAL_KEYS)

    def test_cannot_read_another_users_job(self):
        job = AIRecommendationJob.objects.create(site=self.site, user=self.user, recommendation_type="seo", period_from=date(2026, 6, 1), period_to=date(2026, 6, 30))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/client/ai-recommendations/{job.id}/").status_code, 404)

    @patch("ai_recommendations.views.sync_job.apply_async")
    @patch("ai_recommendations.views.AIRecommendationsClient.create_job")
    def test_create_job(self, remote_create, apply_async):
        remote_create.return_value = {"job_id": "66fa3146-9f43-4a5c-b3bd-13129efe1514", "status": "queued"}
        response = self.client.post("/api/client/ai-recommendations/", {"site_id": self.site.id, "recommendation_type": "combined", "period_from": "2026-06-01", "period_to": "2026-06-30"}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "queued")
        apply_async.assert_called_once()
