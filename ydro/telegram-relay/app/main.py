import asyncio
import hmac
import ipaddress
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.settings import Settings, get_settings
from app.telegram_client import send_message_to_telegram
from app.update_receiver import run_update_polling

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    current_settings = get_settings()
    stop_event = asyncio.Event()
    polling_task = None
    if current_settings.telegram_updates_enabled:
        polling_task = asyncio.create_task(run_update_polling(current_settings, stop_event))
    try:
        yield
    finally:
        stop_event.set()
        if polling_task is not None:
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="TrackNode Telegram Relay", version="1.0.0", lifespan=lifespan)


class SendMessagePayload(BaseModel):
    chat_id: str = Field(..., min_length=1, max_length=64)
    text: str = Field(..., min_length=1, max_length=4096)
    parse_mode: str | None = Field(default="HTML", max_length=32)
    reply_markup: dict[str, Any] | None = None


def _source_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else ""


def _ip_allowed(source_ip: str, settings: Settings) -> bool:
    if not settings.allowed_source_ips:
        return True
    try:
        parsed_ip = ipaddress.ip_address(source_ip)
    except ValueError:
        logger.warning("Relay request rejected because source IP is invalid")
        return False

    for allowed in settings.allowed_source_ips:
        try:
            network = ipaddress.ip_network(allowed, strict=False)
        except ValueError:
            logger.warning("Ignoring invalid ALLOWED_SOURCE_IPS item")
            continue
        if parsed_ip in network:
            return True
    return False


def _json_error(error: str, http_status: int) -> JSONResponse:
    return JSONResponse({"ok": False, "error": error}, status_code=http_status)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/send-message")
async def send_message(
    payload: SendMessagePayload,
    request: Request,
    x_relay_token: str | None = Header(default=None, alias="X-Relay-Token"),
) -> JSONResponse:
    current_settings = get_settings()
    source_ip = _source_ip(request)
    if not _ip_allowed(source_ip, current_settings):
        logger.warning("Relay request rejected by source IP allowlist source_ip=%s", source_ip)
        return _json_error("Forbidden", status.HTTP_403_FORBIDDEN)

    if not current_settings.relay_token:
        logger.error("RELAY_TOKEN is empty")
        return _json_error("Relay token is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not x_relay_token or not hmac.compare_digest(x_relay_token, current_settings.relay_token):
        logger.warning("Relay request rejected: invalid token source_ip=%s", source_ip)
        return _json_error("Unauthorized", status.HTTP_401_UNAUTHORIZED)

    result = await send_message_to_telegram(
        settings=current_settings,
        chat_id=payload.chat_id,
        text=payload.text,
        parse_mode=payload.parse_mode,
        reply_markup=payload.reply_markup,
    )
    return JSONResponse(result, status_code=status.HTTP_200_OK)
