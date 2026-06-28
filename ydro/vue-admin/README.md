# Vue Admin

Клиентская админка Mini CRM на Vue 3 и Vite.

## Локальный запуск

```bash
npm ci
npm run dev
```

Админка откроется на `http://localhost:5173`. Команда использует
`vue-admin/.env.example`.

Переменные:

- `VITE_API_URL` — API с префиксом `/api`
- `VITE_BACKEND_URL` — origin backend для media и абсолютных URL
- `VITE_SITE_URL` — публичный URL frontend
- `VITE_PUBLIC_SITE_URL` — предпочтительный публичный URL для canonical и внешних ссылок
- `VITE_API_BASE_URL` — совместимый alias старой конфигурации

Production-сборка использует `vue-admin/.env`:

```bash
npm run build
```

Production-значения для TrackNode:

```env
VITE_API_URL=https://tracknode.ru/api
VITE_BACKEND_URL=https://tracknode.ru
VITE_SITE_URL=https://tracknode.ru
VITE_PUBLIC_SITE_URL=https://tracknode.ru
```

Локальная проверка сборки:

```bash
npm run build:local
```

## Docker

Запуск backend и Vue Admin:

```bash
docker compose --env-file .env.example up --build -d backend frontend
```

После запуска:

- Vue Admin: `http://localhost:8001`
- Backend API: `http://localhost:8000`

Для разработки каталог `vue-admin` подключён в контейнер как bind mount.
Изменения подхватываются Vite автоматически.

Полная пересборка frontend:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

Проверка конфигурации:

```bash
docker compose --env-file .env.example config
```

## Проверка

```bash
npm run build
```

Проверьте адаптивность в инструментах разработчика браузера на ширинах
1440 px, 768 px и 390 px.

## PWA и push-уведомления

Dashboard устанавливается как `TrackNode Dashboard`. Service worker не кэширует
`/api/`, использует network-first для SPA-навигации и cache-first только для
версионированных Vite-ассетов.

Сгенерируйте VAPID-пару из каталога backend:

```bash
python manage.py generate_vapid_keys
```

Добавьте выведенные `WEB_PUSH_VAPID_PUBLIC_KEY`,
`WEB_PUSH_VAPID_PRIVATE_KEY` и `WEB_PUSH_VAPID_SUBJECT` в серверный `.env`, затем
выполните миграции и перезапустите backend, Celery worker и frontend. Приватный
ключ нельзя передавать во frontend или сохранять в git.

Уведомления включаются пользователем вручную в верхней части страницы заявок
`/sites/:siteId/leads`. Для проверки разрешите уведомления, оставьте вкладку
закрытой и отправьте тестовую заявку с соответствующего публичного сайта.

Web Push требует HTTPS; исключение браузеров для локальной разработки —
`localhost`. На iOS приложение сначала нужно добавить на главный экран.
