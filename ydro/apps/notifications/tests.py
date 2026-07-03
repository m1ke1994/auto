from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DashboardNews, UserNewsRead


class DashboardNewsApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="news-user@example.com",
            email="news-user@example.com",
            password="SafePass-2026!",
        )
        self.client.force_authenticate(self.user)

    def create_news(self, title, **overrides):
        values = {
            "title": title,
            "body": f"Полный текст: {title}",
            "is_published": True,
            "published_at": timezone.now(),
        }
        values.update(overrides)
        return DashboardNews.objects.create(**values)

    def test_authentication_is_required(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("dashboard_news:list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_contains_only_published_news_and_orders_important_first(self):
        regular = self.create_news("Обычная")
        important = self.create_news("Важная", is_important=True, published_at=timezone.now() - timedelta(days=1))
        DashboardNews.objects.create(title="Черновик", body="Не показывать")
        self.create_news("Будущая", published_at=timezone.now() + timedelta(days=1))

        response = self.client.get(reverse("dashboard_news:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [important.id, regular.id])
        self.assertFalse(response.data[0]["is_read"])
        self.assertIn("short_body", response.data[0])

    def test_read_endpoint_is_idempotent_and_updates_unread_count(self):
        news = self.create_news("Новость")
        count_url = reverse("dashboard_news:unread-count")

        self.assertEqual(self.client.get(count_url).data, {"count": 1})
        first = self.client.post(reverse("dashboard_news:read", args=[news.id]))
        second = self.client.post(reverse("dashboard_news:read", args=[news.id]))

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(UserNewsRead.objects.filter(user=self.user, news=news).count(), 1)
        self.assertEqual(self.client.get(count_url).data, {"count": 0})

    def test_detail_returns_full_body_and_read_state(self):
        news = self.create_news("Детальная")
        UserNewsRead.objects.create(user=self.user, news=news)

        response = self.client.get(reverse("dashboard_news:detail", args=[news.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["body"], news.body)
        self.assertTrue(response.data["is_read"])
        self.assertIsNotNone(response.data["read_at"])

    def test_unpublished_news_cannot_be_read(self):
        news = DashboardNews.objects.create(title="Черновик", body="Не показывать")
        response = self.client.post(reverse("dashboard_news:read", args=[news.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
