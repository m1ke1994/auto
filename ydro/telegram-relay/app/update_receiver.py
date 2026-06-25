import asyncio
import json
import logging
from typing import Any

import httpx

from app.settings import Settings
from app.telegram_client import send_message_to_telegram

logger = logging.getLogger(__name__)


def _extract_message(update: dict[str, Any]) -> dict[str, Any]:
    for key in ("message", "edited_message"):
        message = update.get(key)
        if isinstance(message, dict):
            return message
    return {}


def _extract_start_payload(text: str | None) -> str:
    if not text:
        return ""
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return ""
    command = parts[0].lower()
    if not command.startswith("/start"):
        return ""
    return parts[1].strip()


def _bind_success_text(result: dict[str, Any]) -> str:
    name = str(result.get("name") or "").strip()
    if result.get("target_type") == "site":
        return f'Telegram connected to site "{name}".'
    return f'Telegram connected to Mini CRM "{name}".'


async def _post_bind_to_tracknode(
    *,
    settings: Settings,
    start_payload: str,
    chat_id: str,
    telegram_user_id: int | None,
    username: str,
) -> dict[str, Any]:
    if not settings.tracknode_relay_bind_url:
        logger.error("TRACKNODE_RELAY_BIND_URL is empty")
        return {"ok": False, "error": "TrackNode bind URL is not configured"}
    if not settings.tracknode_relay_token:
        logger.error("TRACKNODE_RELAY_TOKEN is empty")
        return {"ok": False, "error": "TrackNode relay token is not configured"}

    payload = {
        "start_payload": start_payload,
        "chat_id": chat_id,
        "telegram_user_id": telegram_user_id,
        "username": username,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Relay-Token": settings.tracknode_relay_token,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_timeout_seconds) as client:
            response = await client.post(settings.tracknode_relay_bind_url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.warning("TrackNode relay bind request failed error_type=%s", exc.__class__.__name__)
        return {"ok": False, "error": "TrackNode bind request failed"}

    try:
        body = response.json()
    except ValueError:
        logger.warning("TrackNode relay bind returned invalid JSON status=%s", response.status_code)
        return {"ok": False, "error": "TrackNode bind returned invalid JSON"}

    if response.status_code >= 400:
        logger.warning("TrackNode relay bind failed status=%s ok=%s", response.status_code, body.get("ok"))
        return {"ok": False, "error": body.get("error") or f"TrackNode HTTP {response.status_code}"}
    return body if isinstance(body, dict) else {"ok": False, "error": "Invalid TrackNode response"}


async def _handle_update(settings: Settings, update: dict[str, Any]) -> None:
    message = _extract_message(update)
    if not message:
        return

    text = message.get("text") or message.get("caption")
    start_payload = _extract_start_payload(text)
    if not start_payload:
        return

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    sender = message.get("from") if isinstance(message.get("from"), dict) else {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    result = await _post_bind_to_tracknode(
        settings=settings,
        start_payload=start_payload,
        chat_id=str(chat_id),
        telegram_user_id=sender.get("id"),
        username=str(sender.get("username") or ""),
    )
    if result.get("ok"):
        logger.info(
            "Telegram bind update processed target_type=%s target_id=%s chat_id=%s",
            result.get("target_type"),
            result.get("target_id"),
            chat_id,
        )
        await send_message_to_telegram(settings=settings, chat_id=str(chat_id), text=_bind_success_text(result))
        return

    logger.warning("Telegram bind update failed chat_id=%s error=%s", chat_id, result.get("error"))
    await send_message_to_telegram(
        settings=settings,
        chat_id=str(chat_id),
        text="Telegram connect token is invalid or expired. Open the dashboard and try again.",
    )


async def run_update_polling(settings: Settings, stop_event: asyncio.Event) -> None:
    if not settings.telegram_updates_enabled:
        logger.info("Telegram update polling is disabled")
        return
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is empty, update polling cannot start")
        return

    base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    offset: int | None = None
    logger.info("Telegram update polling started")

    async with httpx.AsyncClient(timeout=settings.telegram_polling_timeout_seconds + 10) as client:
        try:
            await client.post(f"{base_url}/deleteWebhook", json={"drop_pending_updates": False})
        except httpx.RequestError:
            logger.warning("Failed to disable Telegram webhook before polling start")

        while not stop_event.is_set():
            params: dict[str, Any] = {
                "timeout": settings.telegram_polling_timeout_seconds,
                "allowed_updates": json.dumps(["message", "edited_message"]),
            }
            if offset is not None:
                params["offset"] = offset

            try:
                response = await client.get(f"{base_url}/getUpdates", params=params)
                body = response.json()
                if response.status_code >= 400 or not body.get("ok"):
                    logger.warning("Telegram getUpdates failed status=%s", response.status_code)
                    await asyncio.sleep(settings.telegram_polling_retry_delay_seconds)
                    continue

                for update in body.get("result", []):
                    update_id = update.get("update_id")
                    try:
                        await _handle_update(settings, update)
                    except Exception:
                        logger.exception("Failed to process Telegram update_id=%s", update_id)
                    finally:
                        if update_id is not None:
                            offset = int(update_id) + 1
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Telegram update polling loop error")
                await asyncio.sleep(settings.telegram_polling_retry_delay_seconds)
