import logging

from django.db import IntegrityError, transaction

from clients.models import Client

logger = logging.getLogger(__name__)


def default_client_name_for_site(site) -> str:
    site_name = str(getattr(site, "name", "") or "").strip()
    if site_name:
        return site_name

    domain = str(getattr(site, "domain", "") or "").strip()
    if domain:
        return domain

    owner = getattr(site, "owner", None)
    email = str(getattr(owner, "email", "") or "").strip()
    if email:
        return email

    username = str(getattr(owner, "username", "") or "").strip()
    return username or "Site owner"


def get_user_client(user):
    if user is None:
        return None
    try:
        return user.client
    except (Client.DoesNotExist, AttributeError):
        return None


def get_or_create_client_for_site(site):
    if site is None or not getattr(site, "owner_id", None):
        return None, False

    existing = get_user_client(getattr(site, "owner", None))
    if existing is not None:
        return existing, False

    defaults = {
        "name": default_client_name_for_site(site),
        "is_active": True,
    }
    try:
        with transaction.atomic():
            client, created = Client.objects.get_or_create(owner=site.owner, defaults=defaults)
    except IntegrityError:
        client = Client.objects.filter(owner=site.owner).first()
        created = False

    if client is None:
        return None, False

    if created:
        logger.info(
            "Created missing Mini CRM client for site owner owner_id=%s site_id=%s client_id=%s",
            site.owner_id,
            site.id,
            client.id,
        )
    return client, created
