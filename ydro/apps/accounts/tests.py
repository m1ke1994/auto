from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ClientProfile


class RegisterApiTests(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.payload = {
            "name": "Иван Петров",
            "email": "ivan@example.com",
            "password": "SafePass-2026!",
            "password_confirm": "SafePass-2026!",
            "company_name": "Новый проект",
            "contact": "@ivan",
            "accepted_terms": True,
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotIn("password", response.data)

        user = get_user_model().objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))

    def test_existing_email_cannot_be_registered(self):
        get_user_model().objects.create_user(
            username="existing@example.com",
            email="Existing@Example.com",
            password="SafePass-2025!",
        )
        payload = {**self.payload, "email": "existing@example.com"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "Пользователь с таким email уже зарегистрирован.")

    def test_passwords_must_match(self):
        payload = {**self.payload, "password_confirm": "AnotherPass-2026!"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password_confirm"][0], "Пароли не совпадают.")
        self.assertFalse(get_user_model().objects.filter(email=self.payload["email"]).exists())

    def test_terms_must_be_accepted(self):
        for accepted_terms in (None, False):
            payload = dict(self.payload)
            if accepted_terms is None:
                payload.pop("accepted_terms")
            else:
                payload["accepted_terms"] = accepted_terms

            with self.subTest(accepted_terms=accepted_terms):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("accepted_terms", response.data)

    def test_registered_user_can_log_in(self):
        register_response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": self.payload["email"], "password": self.payload["password"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_registered_user_gets_client_profile_without_site(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload["email"])
        profile = ClientProfile.objects.get(user=user)
        self.assertEqual(profile.display_name, self.payload["name"])
        self.assertEqual(profile.company_name, self.payload["company_name"])
        self.assertEqual(profile.phone, self.payload["contact"])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.sites.exists())
