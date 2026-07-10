# Интеграция AI-рекомендаций

Поток данных: Vue Admin → Django Core → HTTPS → автономный AI-сервис → OpenAI. Браузер не знает адрес, token или signing secret AI-сервиса. Core формирует агрегированный snapshot без IP, cookie, session/visitor ID, контактов и содержимого заявок.

Добавьте в `.env` российского сервера:

```env
AI_RECOMMENDATIONS_ENABLED=True
AI_RECOMMENDATIONS_SERVICE_URL=https://ai.example.com
AI_RECOMMENDATIONS_SERVICE_TOKEN=<совпадает с CORE_SERVICE_TOKEN AI-сервиса>
AI_RECOMMENDATIONS_SIGNING_SECRET=<совпадает с секретом AI-сервиса>
AI_RECOMMENDATIONS_TIMEOUT_SECONDS=15
AI_RECOMMENDATIONS_POLL_INTERVAL_SECONDS=10
AI_RECOMMENDATIONS_MAX_POLL_ATTEMPTS=60
```

Затем:

```bash
docker compose up -d --build backend celery_worker frontend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py check
```

Проверка связи из Core-контейнера: `docker compose exec backend curl -fsS https://ai.example.com/health`. Рабочие endpoints нельзя проверять простым curl без HMAC; используйте клиент `ai_recommendations.client.AIRecommendationsClient`.

Локальные endpoints Vue:

- `POST/GET /api/client/ai-recommendations/`
- `GET/DELETE /api/client/ai-recommendations/{id}/`
- `POST /api/client/ai-recommendations/{id}/retry/`

Доступ разрешён только тарифу «Бизнес-аналитика» и только владельцу сайта. Результат синхронизирует Celery, HTTP-запрос Vue не ждёт OpenAI.
