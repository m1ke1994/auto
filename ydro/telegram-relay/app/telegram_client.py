import logging
from typing import Any

import httpx

from app.settings import Settings

logger = logging.getLogger(__name__)


async def send_message_to_telegram(
    *,
    settings: Settings,
    chat_id: str,
    text: str,
    parse_mode: str | None = "HTML",
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    token = settings.telegram_bot_token
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is empty")
        return {"ok": False, "error": "Telegram bot token is not configured"}

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    if reply_markup:
        payload["reply_markup"] = reply_markup

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_timeout_seconds) as client:
            response = await client.post(endpoint, json=payload)
    except httpx.RequestError as exc:
        logger.warning("Telegram request failed error_type=%s", exc.__class__.__name__)
        return {"ok": False, "error": "Telegram request failed"}

    try:
        body = response.json()
    except ValueError:
        logger.warning("Telegram returned invalid JSON status=%s", response.status_code)
        return {"ok": False, "error": "Telegram returned invalid JSON"}

    if response.status_code >= 400:
        error = body.get("description") or body.get("error") or f"Telegram HTTP {response.status_code}"
        logger.warning("Telegram returned HTTP error status=%s ok=%s", response.status_code, body.get("ok"))
        return {"ok": False, "error": error}

    if not body.get("ok"):
        error = body.get("description") or body.get("error") or "Telegram returned ok=false"
        logger.warning("Telegram returned ok=false")
        return {"ok": False, "error": error}

    return {"ok": True}
