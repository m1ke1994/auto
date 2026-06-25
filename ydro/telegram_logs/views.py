import logging

from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from telegram_logs.binding import bind_telegram_start_payload
from telegram_logs.sender import send_telegram_message
from telegram_logs.services import extract_message, save_telegram_update

logger = logging.getLogger(__name__)


def _process_start_payload(update: dict) -> None:
    message = extract_message(update)
    if not isinstance(message, dict):
        return
    text = (message.get("text") or message.get("caption") or "").strip()
    if not text.lower().startswith("/start"):
        return

    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    sender = message.get("from") if isinstance(message.get("from"), dict) else {}
    result = bind_telegram_start_payload(
        start_payload=parts[1].strip(),
        chat_id=str(chat_id),
        telegram_user_id=sender.get("id"),
    )
    if result is None:
        return

    if result.target_type == "site":
        send_telegram_message(str(chat_id), f'Telegram connected to site "{result.name}".')
    else:
        send_telegram_message(str(chat_id), f'Telegram connected to Mini CRM "{result.name}".')


class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "public_telegram_webhook"

    def post(self, request, *args, **kwargs):
        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if secret:
            incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if incoming_secret != secret:
                logger.warning("Telegram webhook rejected: invalid secret token")
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        update = request.data if isinstance(request.data, dict) else {}
        update_id = update.get("update_id")
        if update_id is None:
            logger.warning("Telegram webhook rejected: missing update_id")
            return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            _, created = save_telegram_update(update)
            if not created:
                logger.info("Telegram webhook duplicate update ignored: update_id=%s", update_id)
            else:
                _process_start_payload(update)
        except Exception:
            logger.exception("Failed to save telegram update log")
            return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"ok": True}, status=status.HTTP_200_OK)


class TelegramRelayBindView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "public_telegram_webhook"

    def post(self, request, *args, **kwargs):
        expected_token = (
            getattr(settings, "TELEGRAM_RELAY_BIND_TOKEN", "")
            or getattr(settings, "TELEGRAM_RELAY_TOKEN", "")
            or ""
        )
        if not expected_token:
            logger.error("Telegram relay bind rejected: relay bind token is not configured")
            return Response(
                {"ok": False, "error": "Relay bind token is not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        incoming_token = request.headers.get("X-Relay-Token", "")
        if not incoming_token or not constant_time_compare(incoming_token, expected_token):
            logger.warning("Telegram relay bind rejected: invalid relay token")
            return Response({"ok": False, "error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data if isinstance(request.data, dict) else {}
        start_payload = str(payload.get("start_payload") or payload.get("payload") or "").strip()
        chat_id = str(payload.get("chat_id") or "").strip()
        telegram_user_id = payload.get("telegram_user_id")
        if not start_payload or not chat_id:
            return Response(
                {"ok": False, "error": "start_payload and chat_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = bind_telegram_start_payload(
            start_payload=start_payload,
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
        )
        if result is None:
            logger.warning("Telegram relay bind failed: invalid start payload")
            return Response({"ok": False, "error": "Invalid start payload"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            "Telegram relay bind success target_type=%s target_id=%s chat_id=%s",
            result.target_type,
            result.target_id,
            chat_id,
        )
        return Response(
            {
                "ok": True,
                "target_type": result.target_type,
                "target_id": result.target_id,
                "name": result.name,
            },
            status=status.HTTP_200_OK,
        )
