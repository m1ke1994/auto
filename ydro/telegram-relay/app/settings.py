import os
from dataclasses import dataclass
from functools import lru_cache


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _env_int(key: str, default: int) -> int:
    value = _env(key, str(default))
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    value = _env(key, str(default))
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, "true" if default else "false").lower() in {"1", "true", "yes", "on"}


def _env_csv(key: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in _env(key).split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    relay_token: str
    allowed_source_ips: tuple[str, ...]
    port: int
    log_level: str
    tracknode_relay_bind_url: str
    tracknode_relay_token: str
    telegram_updates_enabled: bool
    telegram_polling_timeout_seconds: int
    telegram_polling_retry_delay_seconds: float
    telegram_timeout_seconds: float = 10.0
    max_text_length: int = 4096


@lru_cache
def get_settings() -> Settings:
    return Settings(
        telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
        relay_token=_env("RELAY_TOKEN"),
        allowed_source_ips=_env_csv("ALLOWED_SOURCE_IPS"),
        port=_env_int("PORT", 8080),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
        tracknode_relay_bind_url=_env("TRACKNODE_RELAY_BIND_URL"),
        tracknode_relay_token=_env("TRACKNODE_RELAY_TOKEN", _env("RELAY_TOKEN")),
        telegram_updates_enabled=_env_bool("TELEGRAM_UPDATES_ENABLED", True),
        telegram_polling_timeout_seconds=_env_int("TELEGRAM_POLLING_TIMEOUT", 30),
        telegram_polling_retry_delay_seconds=_env_float("TELEGRAM_POLLING_RETRY_DELAY", 2.0),
    )
