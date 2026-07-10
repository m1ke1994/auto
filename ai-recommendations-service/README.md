# TrackNode AI Recommendations Service

Автономный сервис формирования SEO- и conversion-рекомендаций для TrackNode. Django Core передаёт по HTTPS только агрегированные обезличенные данные, сервис сохраняет задание в PostgreSQL, Celery worker вызывает OpenAI Responses API со строгой Pydantic-схемой, а Core получает результат фоновым polling. Ключ OpenAI хранится только здесь.

## Требования и быстрый запуск

Нужны Linux x86_64/arm64, Docker Engine 24+, Compose v2, 2 CPU, 4 ГБ RAM и 20 ГБ диска. PostgreSQL и Redis наружу не публикуются.

```bash
cp .env.example .env
python3 scripts/generate_service_secret.py
# перенесите выведенные значения в .env и добавьте OPENAI_API_KEY
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/health/ready
```

Обязательные настройки: `OPENAI_API_KEY`, `CORE_SERVICE_TOKEN`, `AI_RECOMMENDATIONS_SIGNING_SECRET`, `POSTGRES_PASSWORD`, корректный `DATABASE_URL`. Модели выбираются через `OPENAI_MODEL_SEO` и `OPENAI_MODEL_CONVERSION`. После изменения `.env` перезапустите контейнеры. Миграции выполняются API-контейнером перед стартом; вручную: `docker compose run --rm api alembic upgrade head`.

## Безопасность и сеть

Рабочие endpoints требуют Bearer token и HMAC-SHA256 от `timestamp + request_id + raw_body`. Допустимое отклонение времени — 5 минут, UUID запроса нельзя использовать повторно. `CORE_ALLOWED_IPS` принимает разделённые запятыми IP/CIDR. CORS не включён: браузер не должен обращаться к сервису. Для production публикуйте только 443 через внешний reverse proxy, ограничьте 8080 localhost/firewall и никогда не публикуйте 5432/6379.

Пример UFW:

```bash
sudo ufw default deny incoming
sudo ufw allow OpenSSH
sudo ufw allow 443/tcp
sudo ufw enable
```

Пример Caddy (`ai.example.com` замените на домен):

```caddy
ai.example.com {
    reverse_proxy 127.0.0.1:8080
    request_body { max_size 1MB }
}
```

## API

- `GET /health`, `GET /health/ready`
- `POST /api/v1/recommendations/jobs`
- `GET /api/v1/recommendations/jobs/{job_id}`
- `GET /api/v1/recommendations/jobs/by-external-id/{external_job_id}`
- `POST /api/v1/recommendations/jobs/{job_id}/retry`
- `DELETE /api/v1/recommendations/jobs/{job_id}`

Создание идемпотентно по `external_job_id`. Типы: `seo`, `conversion`, `combined`; статусы: `queued`, `processing`, `completed`, `failed`, `cancelled`. OpenAPI доступен на `/docs` (ограничьте его firewall/reverse proxy при необходимости).

Подписанный запрос на Python:

```python
import hashlib, hmac, json, time, uuid, requests
body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
timestamp, request_id = str(int(time.time())), str(uuid.uuid4())
signature = hmac.new(SIGNING_SECRET.encode(), timestamp.encode() + request_id.encode() + body, hashlib.sha256).hexdigest()
requests.post("https://ai.example.com/api/v1/recommendations/jobs", data=body, timeout=15, headers={
    "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
    "X-Timestamp": timestamp, "X-Request-Id": request_id, "X-Signature": signature,
})
```

## Эксплуатация

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose restart
docker compose down
docker compose down -v  # удаляет данные, только осознанно
```

Обновление: сделайте backup, замените содержимое каталога без `.env`, затем `docker compose up -d --build`. Перенос: скопируйте каталог и отдельно `.env`, восстановите БД, выполните ту же команду запуска.

Backup и restore PostgreSQL:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > ai-recommendations.dump
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < ai-recommendations.dump
```

Тесты и качество: `pip install -e '.[dev]'`, затем `pytest` и `ruff check .`. OpenAI в тестах не вызывается.

## Диагностика

- `ready` возвращает 503: проверьте обязательные переменные, PostgreSQL, Redis и `docker compose logs worker`.
- 401: синхронизируйте время (NTP), token/signing secret и сериализацию raw body.
- 409: нельзя повторно использовать `X-Request-Id`; создавайте новый UUID на каждый HTTP-запрос.
- 422: payload не соответствует схеме или содержит неверный домен/период.
- задания остаются queued: проверьте worker и broker; после восстановления безопасно используйте retry только для `failed`.
- OpenAI timeout/rate limit повторяются с backoff; пользователю возвращается безопасная ошибка без prompt, ключей и stack trace.

