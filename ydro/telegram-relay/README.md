# TrackNode Telegram Relay

Отдельный FastAPI-сервис для отправки Telegram-сообщений через сервер, где доступен Telegram Bot API.

## Запуск

1. Скопируйте папку `telegram-relay/` на сервер в Голландии.
2. Создайте `.env`:

   ```bash
   cp .env.example .env
   nano .env
   ```

3. Заполните `TELEGRAM_BOT_TOKEN` токеном Telegram-бота.
4. Заполните `RELAY_TOKEN` длинным случайным секретом. Этот же секрет укажите в основном TrackNode как `TELEGRAM_RELAY_TOKEN`.
5. При необходимости заполните `ALLOWED_SOURCE_IPS` IP-адресом основного сервера TrackNode. Можно указать несколько значений через запятую или CIDR:

   ```env
   ALLOWED_SOURCE_IPS=203.0.113.10,203.0.113.0/24
   ```

   Также рекомендуется на firewall открыть порт relay только для IP основного сервера.

6. Запустите сервис:

   ```bash
   docker compose up -d --build
   ```

## Проверка

Healthcheck:

```bash
curl http://localhost:8080/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Проверка отправки:

```bash
curl -X POST http://localhost:8080/send-message \
  -H "Content-Type: application/json" \
  -H "X-Relay-Token: YOUR_RELAY_TOKEN" \
  -d '{"chat_id":"YOUR_CHAT_ID","text":"Тестовое сообщение","parse_mode":"HTML"}'
```

Ожидаемый успешный ответ:

```json
{"ok":true}
```

Логи:

```bash
docker compose logs -f
```

## Подключение основного TrackNode

На основном сервере TrackNode оставьте старые Telegram-переменные и добавьте:

```env
TELEGRAM_DELIVERY_MODE=relay
TELEGRAM_RELAY_URL=https://relay-domain.com/send-message
TELEGRAM_RELAY_TOKEN=тот_же_секрет_что_в_RELAY_TOKEN
```

Для возврата к старому режиму:

```env
TELEGRAM_DELIVERY_MODE=direct
```
