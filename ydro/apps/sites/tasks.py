import logging

from celery import shared_task

from clients.push_services import send_site_lead_push_notifications

from .models import SiteLead


logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def send_site_lead_push_notification_task(lead_id: int) -> None:
    try:
        lead = SiteLead.objects.select_related("site", "site__owner").get(pk=lead_id)
    except SiteLead.DoesNotExist:
        logger.warning("Site lead does not exist for push delivery; lead_id=%s", lead_id)
        return
    send_site_lead_push_notifications(lead)
