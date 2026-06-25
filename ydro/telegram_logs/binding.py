from dataclasses import dataclass

from django.utils import timezone

from apps.sites.telegram_binding import resolve_site_start_payload
from clients.telegram_binding import resolve_secure_start_payload
from subscriptions.models import TelegramLink


@dataclass(frozen=True)
class TelegramBindingResult:
    target_type: str
    target_id: int
    name: str


def _int_or_none(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def upsert_telegram_link(*, sender_id: int, chat_id: int, client) -> TelegramLink:
    link_by_sender = TelegramLink.objects.filter(telegram_user_id=sender_id).select_related("client").first()
    link_by_client = TelegramLink.objects.filter(client=client).select_related("client").first()

    if link_by_sender and link_by_client and link_by_sender.pk != link_by_client.pk:
        link_by_client.delete()

    link = link_by_sender or link_by_client
    if link is None:
        return TelegramLink.objects.create(telegram_user_id=sender_id, telegram_chat_id=chat_id, client=client)

    update_fields = []
    if link.telegram_user_id != sender_id:
        link.telegram_user_id = sender_id
        update_fields.append("telegram_user_id")
    if link.telegram_chat_id != chat_id:
        link.telegram_chat_id = chat_id
        update_fields.append("telegram_chat_id")
    if link.client_id != client.id:
        link.client = client
        update_fields.append("client")
    if update_fields:
        link.save(update_fields=[*update_fields, "updated_at"])
    return link


def bind_telegram_start_payload(
    *,
    start_payload: str,
    chat_id: str | int,
    telegram_user_id: str | int | None = None,
) -> TelegramBindingResult | None:
    chat_id_text = str(chat_id).strip()
    if not start_payload or not chat_id_text:
        return None

    site = resolve_site_start_payload(start_payload)
    if site is not None:
        site.telegram_chat_id = chat_id_text
        site.send_to_telegram = True
        site.telegram_connected_at = timezone.now()
        site.save(update_fields=["telegram_chat_id", "send_to_telegram", "telegram_connected_at", "updated_at"])
        return TelegramBindingResult(target_type="site", target_id=site.id, name=site.name)

    client = resolve_secure_start_payload(start_payload)
    if client is None:
        return None

    client.telegram_chat_id = chat_id_text
    client.send_to_telegram = True
    client.save(update_fields=["telegram_chat_id", "send_to_telegram"])

    sender_id = _int_or_none(telegram_user_id)
    chat_id_int = _int_or_none(chat_id_text)
    if sender_id is not None and chat_id_int is not None:
        upsert_telegram_link(sender_id=sender_id, chat_id=chat_id_int, client=client)

    return TelegramBindingResult(target_type="client", target_id=client.id, name=client.name)
