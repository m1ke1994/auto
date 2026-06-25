import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_SEND_TIMEOUT = 10
DELIVERY_MODE_DIRECT = "direct"
DELIVERY_MODE_RELAY = "relay"


def _telegram_delivery_mode() -> str:
    mode = str(getattr(settings, "TELEGRAM_DELIVERY_MODE", DELIVERY_MODE_DIRECT) or "").strip().lower()
    if mode in {DELIVERY_MODE_DIRECT, DELIVERY_MODE_RELAY}:
        return mode
    logger.warning("Invalid TELEGRAM_DELIVERY_MODE=%r, falling back to direct", mode)
    return DELIVERY_MODE_DIRECT


def _build_payload(
    *,
    chat_id: str | int,
    text: str,
    parse_mode: str | None,
    reply_markup: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "chat_id": str(chat_id),
        "text": str(text),
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return payload


def _send_direct(payload: dict[str, Any]) -> bool:
    token = str(getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token:
        logger.info("Telegram token is not configured, skipping message.")
        return False

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    chat_id = payload.get("chat_id")
    try:
        response = requests.post(endpoint, json=payload, timeout=TELEGRAM_SEND_TIMEOUT)
        response.raise_for_status()
        body = response.json() if response.content else {}
        if not body.get("ok"):
            logger.warning("Telegram sendMessage not ok: chat_id=%s payload=%s", chat_id, body)
            return False
        return True
    except requests.RequestException:
        logger.exception("Failed to send telegram message for chat_id=%s", chat_id)
        return False
    except ValueError:
        logger.exception("Telegram sendMessage returned invalid JSON for chat_id=%s", chat_id)
        return False


def _send_relay(payload: dict[str, Any]) -> bool:
    relay_url = str(getattr(settings, "TELEGRAM_RELAY_URL", "") or "").strip()
    relay_token = str(getattr(settings, "TELEGRAM_RELAY_TOKEN", "") or "").strip()
    chat_id = payload.get("chat_id")

    if not relay_url:
        logger.error("TELEGRAM_DELIVERY_MODE=relay but TELEGRAM_RELAY_URL is empty")
        return False
    if not relay_token:
        logger.error("TELEGRAM_DELIVERY_MODE=relay but TELEGRAM_RELAY_TOKEN is empty")
        return False

    headers = {
        "Content-Type": "application/json",
        "X-Relay-Token": relay_token,
    }
    try:
        response = requests.post(relay_url, json=payload, headers=headers, timeout=TELEGRAM_SEND_TIMEOUT)
        if response.status_code in {401, 403}:
            logger.error("Telegram relay authorization failed status=%s chat_id=%s", response.status_code, chat_id)
            return False

        response.raise_for_status()
        body = response.json() if response.content else {}
        if not body.get("ok"):
            logger.warning(
                "Telegram relay returned non-ok response: chat_id=%s error=%s",
                chat_id,
                body.get("error", "unknown"),
            )
            return False
        return True
    except requests.RequestException:
        logger.exception("Failed to send telegram message through relay for chat_id=%s", chat_id)
        return False
    except ValueError:
        logger.exception("Telegram relay returned invalid JSON for chat_id=%s", chat_id)
        return False


def send_telegram_message(
    chat_id: str | int,
    text: str,
    parse_mode: str | None = "HTML",
    reply_markup: dict[str, Any] | None = None,
) -> bool:
    payload = _build_payload(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    if _telegram_delivery_mode() == DELIVERY_MODE_RELAY:
        return _send_relay(payload)
    return _send_direct(payload)
