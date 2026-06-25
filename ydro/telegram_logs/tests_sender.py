from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from telegram_logs.sender import send_telegram_message


def _response(*, status_code=200, body=None):
    response = Mock()
    response.status_code = status_code
    response.content = b"{}"
    response.json.return_value = body if body is not None else {"ok": True}
    response.raise_for_status.return_value = None
    return response


class TelegramSenderTests(TestCase):
    @override_settings(
        TELEGRAM_DELIVERY_MODE="direct",
        TELEGRAM_BOT_TOKEN="telegram-secret",
        TELEGRAM_RELAY_URL="https://relay.example/send-message",
        TELEGRAM_RELAY_TOKEN="relay-secret",
    )
    @patch("telegram_logs.sender.requests.post")
    def test_direct_mode_uses_telegram_bot_api(self, mocked_post):
        mocked_post.return_value = _response()

        delivered = send_telegram_message("123456", "Hello")

        self.assertTrue(delivered)
        url = mocked_post.call_args.args[0]
        self.assertEqual(url, "https://api.telegram.org/bottelegram-secret/sendMessage")
        self.assertEqual(mocked_post.call_args.kwargs["json"]["chat_id"], "123456")
        self.assertEqual(mocked_post.call_args.kwargs["json"]["text"], "Hello")
        self.assertEqual(mocked_post.call_args.kwargs["json"]["parse_mode"], "HTML")

    @override_settings(
        TELEGRAM_DELIVERY_MODE="relay",
        TELEGRAM_BOT_TOKEN="telegram-secret",
        TELEGRAM_RELAY_URL="https://relay.example/send-message",
        TELEGRAM_RELAY_TOKEN="relay-secret",
    )
    @patch("telegram_logs.sender.requests.post")
    def test_relay_mode_posts_to_relay_with_token_header(self, mocked_post):
        mocked_post.return_value = _response()
        keyboard = {"inline_keyboard": [[{"text": "Open", "callback_data": "open"}]]}

        delivered = send_telegram_message("123456", "Hello", reply_markup=keyboard)

        self.assertTrue(delivered)
        self.assertEqual(mocked_post.call_args.args[0], "https://relay.example/send-message")
        self.assertEqual(
            mocked_post.call_args.kwargs["headers"],
            {
                "Content-Type": "application/json",
                "X-Relay-Token": "relay-secret",
            },
        )
        self.assertEqual(
            mocked_post.call_args.kwargs["json"],
            {
                "chat_id": "123456",
                "text": "Hello",
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": keyboard,
            },
        )

    @override_settings(
        TELEGRAM_DELIVERY_MODE="relay",
        TELEGRAM_RELAY_URL="https://relay.example/send-message",
        TELEGRAM_RELAY_TOKEN="relay-secret",
    )
    @patch("telegram_logs.sender.requests.post")
    def test_relay_non_ok_response_returns_false(self, mocked_post):
        mocked_post.return_value = _response(body={"ok": False, "error": "Telegram failed"})

        delivered = send_telegram_message("123456", "Hello")

        self.assertFalse(delivered)

    @override_settings(
        TELEGRAM_DELIVERY_MODE="relay",
        TELEGRAM_RELAY_URL="https://relay.example/send-message",
        TELEGRAM_RELAY_TOKEN="relay-secret",
    )
    @patch("telegram_logs.sender.requests.post")
    def test_relay_auth_error_returns_false(self, mocked_post):
        mocked_post.return_value = _response(status_code=401, body={"ok": False, "error": "Unauthorized"})

        delivered = send_telegram_message("123456", "Hello")

        self.assertFalse(delivered)

    @override_settings(TELEGRAM_DELIVERY_MODE="relay", TELEGRAM_RELAY_URL="", TELEGRAM_RELAY_TOKEN="")
    @patch("telegram_logs.sender.requests.post")
    def test_relay_missing_config_does_not_fall_back_to_direct(self, mocked_post):
        delivered = send_telegram_message("123456", "Hello")

        self.assertFalse(delivered)
        mocked_post.assert_not_called()

    @override_settings(TELEGRAM_DELIVERY_MODE="relay", TELEGRAM_USE_WEBHOOK=False, TELEGRAM_BOT_TOKEN="telegram-secret")
    @patch("telegram_logs.management.commands.run_telegram_polling.requests.post")
    @patch("telegram_logs.management.commands.run_telegram_polling.requests.get")
    def test_polling_exits_without_bot_api_calls_in_relay_mode(self, mocked_get, mocked_post):
        call_command("run_telegram_polling")

        mocked_get.assert_not_called()
        mocked_post.assert_not_called()
