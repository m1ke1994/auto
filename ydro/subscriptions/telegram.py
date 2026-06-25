from typing import Any

from telegram_logs.sender import send_telegram_message as send_telegram_text_message


def send_telegram_message(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> bool:
    return send_telegram_text_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
