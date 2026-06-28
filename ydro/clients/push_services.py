import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from clients.models import PushSubscription


logger = logging.getLogger(__name__)


def build_site_lead_push_payload(lead) -> dict:
    site = lead.site
    return {
        "title": "Новая заявка в TrackNode",
        "body": f"Сайт: {site.name}\nОткройте дашборд, чтобы посмотреть детали.",
        "icon": "/pwa-icon-192.svg",
        "badge": "/pwa-icon-192.svg",
        "tag": f"site-lead-{lead.id}",
        "data": {"url": f"/sites/{site.id}/leads?lead={lead.id}"},
    }


def send_site_lead_push_notifications(lead) -> int:
    public_key = str(getattr(settings, "WEB_PUSH_VAPID_PUBLIC_KEY", "") or "")
    private_key = str(getattr(settings, "WEB_PUSH_VAPID_PRIVATE_KEY", "") or "")
    subject = str(getattr(settings, "WEB_PUSH_VAPID_SUBJECT", "") or "")
    if not (public_key and private_key and subject):
        logger.warning("Web push is not configured; lead_id=%s", lead.id)
        return 0

    payload = json.dumps(build_site_lead_push_payload(lead), ensure_ascii=False)
    subscriptions = PushSubscription.objects.filter(user=lead.site.owner, is_active=True)
    delivered = 0

    for subscription in subscriptions.iterator():
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
                ttl=300,
            )
            delivered += 1
        except WebPushException as exc:
            PushSubscription.objects.filter(pk=subscription.pk).update(is_active=False)
            response_status = getattr(getattr(exc, "response", None), "status_code", None)
            logger.warning(
                "Web push delivery failed; lead_id=%s subscription_id=%s status=%s",
                lead.id,
                subscription.id,
                response_status,
            )
        except Exception:
            PushSubscription.objects.filter(pk=subscription.pk).update(is_active=False)
            logger.exception(
                "Unexpected web push delivery error; lead_id=%s subscription_id=%s",
                lead.id,
                subscription.id,
            )

    return delivered
