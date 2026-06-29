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


class ChangePasswordApiTests(APITestCase):
    def setUp(self):
        self.url = reverse("change_password")
        self.login_url = reverse("token_obtain_pair")
        self.current_password = "CurrentPass-2026!"
        self.new_password = "UpdatedPass-2026!"
        self.user = get_user_model().objects.create_user(
            username="password-user@example.com",
            email="password-user@example.com",
            password=self.current_password,
        )
        login_response = self.client.post(
            self.login_url,
            {"username": self.user.email, "password": self.current_password},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    def payload(self, **overrides):
        return {
            "current_password": self.current_password,
            "new_password": self.new_password,
            "new_password_confirm": self.new_password,
            **overrides,
        }

    def change_password(self):
        return self.client.post(self.url, self.payload(), format="json")

    def test_authenticated_user_can_change_password(self):
        response = self.change_password()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Пароль успешно изменён."})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

        # Password changes do not interrupt the JWT session currently in use.
        me_response = self.client.get(reverse("user_me"))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)

    def test_old_password_no_longer_allows_login(self):
        self.change_password()
        self.client.credentials()

        response = self.client.post(
            self.login_url,
            {"username": self.user.email, "password": self.current_password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_password_allows_login(self):
        self.change_password()
        self.client.credentials()

        response = self.client.post(
            self.login_url,
            {"username": self.user.email, "password": self.new_password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_authentication_is_required(self):
        self.client.credentials()

        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Необходима авторизация.")

    def test_current_password_must_be_correct(self):
        response = self.client.post(
            self.url,
            self.payload(current_password="WrongPass-2026!"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Текущий пароль указан неверно.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.current_password))

    def test_new_passwords_must_match(self):
        response = self.client.post(
            self.url,
            self.payload(new_password_confirm="AnotherPass-2026!"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Новые пароли не совпадают.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.current_password))

    def test_weak_new_password_is_rejected(self):
        response = self.client.post(
            self.url,
            self.payload(new_password="12345678", new_password_confirm="12345678"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Новый пароль не соответствует требованиям безопасности.",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.current_password))
