import logging

from django.conf import settings
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class SubscriptionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "subscriptions"

    def ready(self):
        if not getattr(settings, "ENABLE_BILLING", False):
            return

        missing = [
            name
            for name in ("YOOKASSA_SHOP_ID", "YOOKASSA_SECRET_KEY")
            if not getattr(settings, name, "")
        ]
        if missing:
            logger.error(
                "YooKassa billing is enabled but backend environment variables are missing: %s",
                ", ".join(missing),
            )
