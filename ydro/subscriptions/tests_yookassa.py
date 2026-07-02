from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from clients.models import Client
from subscriptions.models import SubscriptionPayment, SubscriptionPlan
from subscriptions.services import YooKassaConfigurationError, _configure_yookassa


class YooKassaConfigurationTests(TestCase):
    @override_settings(
        YOOKASSA_SHOP_ID="shop-from-environment",
        YOOKASSA_SECRET_KEY="secret-from-environment",
    )
    @patch("subscriptions.services.Configuration.configure")
    def test_backend_credentials_are_passed_to_sdk_configuration(self, configure):
        _configure_yookassa()

        configure.assert_called_once_with("shop-from-environment", "secret-from-environment")

    @override_settings(YOOKASSA_SHOP_ID="", YOOKASSA_SECRET_KEY="")
    def test_missing_credentials_are_logged_without_crashing_django(self):
        with self.assertLogs("subscriptions.services", level="ERROR") as captured:
            with self.assertRaises(YooKassaConfigurationError):
                _configure_yookassa()

        log_output = " ".join(captured.output)
        self.assertIn("YOOKASSA_SHOP_ID", log_output)
        self.assertIn("YOOKASSA_SECRET_KEY", log_output)


class YooKassaEndpointTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="yookassa-test@example.com",
            email="yookassa-test@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(owner=user, name="YooKassa Test Client")
        self.plan = SubscriptionPlan.objects.create(
            name="YooKassa Test Plan",
            price="100.00",
            currency="RUB",
            duration_days=30,
        )
        self.api = APIClient()
        self.api.force_authenticate(user=user)

    @override_settings(YOOKASSA_SHOP_ID="", YOOKASSA_SECRET_KEY="")
    def test_create_payment_returns_safe_503_when_credentials_are_missing(self):
        response = self.api.post(
            "/api/mini/subscription/create-payment/",
            {"plan_id": self.plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {"detail": "Платёжный сервис временно недоступен."})
        self.assertNotIn("YOOKASSA", str(response.data))

    @override_settings(
        YOOKASSA_SHOP_ID="shop-from-environment",
        YOOKASSA_SECRET_KEY="secret-from-environment",
    )
    @patch("subscriptions.views.activate_subscription_from_payment")
    @patch("subscriptions.services.Payment.find_one")
    @patch("subscriptions.services.Configuration.configure")
    def test_webhook_confirms_payment_through_authenticated_backend_api(
        self,
        configure,
        find_one,
        activate,
    ):
        payment = SubscriptionPayment.objects.create(
            client=self.client_obj,
            plan=self.plan,
            yookassa_payment_id="provider-payment-id",
            # A previous worker may have confirmed the provider status and
            # stopped before activating the subscription. The webhook must
            # safely resume that incomplete operation.
            status=SubscriptionPayment.Status.SUCCEEDED,
        )
        find_one.return_value = SimpleNamespace(
            id="provider-payment-id",
            status=SubscriptionPayment.Status.SUCCEEDED,
        )
        activate.return_value = SimpleNamespace(
            status="active",
            plan=None,
            paid_until=None,
        )

        response = self.api.post(
            "/api/payments/yookassa/webhook/",
            {
                "event": "payment.succeeded",
                "object": {"id": "provider-payment-id", "status": "succeeded"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        configure.assert_called_once_with("shop-from-environment", "secret-from-environment")
        find_one.assert_called_once_with("provider-payment-id")
        activate.assert_called_once()
        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.Status.SUCCEEDED)
        self.assertNotIn("secret-from-environment", response.content.decode("utf-8"))

    def test_webhook_rejects_invalid_json(self):
        response = self.api.post(
            "/api/payments/yookassa/webhook/",
            data="not-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"status": "invalid_payload"})
