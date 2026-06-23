# Production deploy: TrackNode + A Meditation

This deploy expects two sibling folders on the server:

```bash
~/projects/v2/ydro
~/projects/v2/a-meditation
```

Upload both folders with WinSCP preserving this layout. The recommended production entry point is `ydro`; its nginx serves both domains:

- `tracknode.ru` and `www.tracknode.ru`: TrackNode/Vue Admin plus Django `/admin/`, `/api/`, `/static/`, `/media/`, `/tracker.js`.
- `leelabird.ru` and `www.leelabird.ru`: only the A Meditation public site. It requests API data from `tracknode.ru`.

## 1. Prepare env files

On the server:

```bash
cd ~/projects/v2/ydro
cp production.env.example .env
cp vue-admin/production.env.example vue-admin/.env
```

Edit `ydro/.env` and replace every `CHANGE_ME...` value. Keep first-launch HTTP values:

```env
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tracknode.ru,www.tracknode.ru
DJANGO_REQUIRE_HTTPS=False
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DOMAIN=tracknode.ru
SITE_BASE_URL=https://tracknode.ru
PUBLIC_BASE_URL=https://tracknode.ru
FRONTEND_URL=https://tracknode.ru
API_URL=https://tracknode.ru/api
ADMIN_URL=https://tracknode.ru/admin
PUBLIC_SITE_DEFAULT_DOMAIN=leelabird.ru
PUBLIC_SITE_DEFAULT_URL=https://leelabird.ru
CORS_ALLOWED_ORIGINS=https://tracknode.ru,https://www.tracknode.ru,https://leelabird.ru,https://www.leelabird.ru
CSRF_TRUSTED_ORIGINS=https://tracknode.ru,https://www.tracknode.ru,https://leelabird.ru,https://www.leelabird.ru
PUBLIC_SITE_VITE_API_URL=https://tracknode.ru/api
PUBLIC_SITE_VITE_BACKEND_URL=https://tracknode.ru
PUBLIC_SITE_VITE_SITE_URL=https://leelabird.ru
PUBLIC_SITE_VITE_PUBLIC_SITE_URL=https://leelabird.ru
```

Edit `ydro/vue-admin/.env` with HTTP values from `vue-admin/production.env.example`.

For standalone A Meditation builds, use:

```bash
cd ~/projects/v2/a-meditation/frontend
cp .env.example .env
```

The unified `ydro` compose does not require standalone A Meditation compose.

## 2. First HTTP launch

```bash
cd ~/projects/v2/ydro
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml config
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml ps
```

Check:

```bash
curl -I https://tracknode.ru
curl -I https://tracknode.ru/admin/
curl -I https://tracknode.ru/api/
curl -I https://tracknode.ru/tracker.js
curl -I https://leelabird.ru
curl -I https://leelabird.ru/admin/
```

`leelabird.ru/admin/` must not open Django Admin.

Logs:

```bash
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx backend frontend public_site celery_worker celery_beat
```

## 3. Switch to HTTPS

Install certificates on the host first. The HTTPS compose expects:

```text
/etc/letsencrypt/live/tracknode.ru/fullchain.pem
/etc/letsencrypt/live/tracknode.ru/privkey.pem
/etc/letsencrypt/live/leelabird.ru/fullchain.pem
/etc/letsencrypt/live/leelabird.ru/privkey.pem
```

Then update `ydro/.env`:

```env
DJANGO_REQUIRE_HTTPS=True
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
SITE_BASE_URL=https://tracknode.ru
PUBLIC_BASE_URL=https://tracknode.ru
FRONTEND_URL=https://tracknode.ru
API_URL=https://tracknode.ru/api
ADMIN_URL=https://tracknode.ru/admin
PUBLIC_SITE_DEFAULT_URL=https://leelabird.ru
CORS_ALLOWED_ORIGINS=https://tracknode.ru,https://www.tracknode.ru,https://leelabird.ru,https://www.leelabird.ru
CSRF_TRUSTED_ORIGINS=https://tracknode.ru,https://www.tracknode.ru,https://leelabird.ru,https://www.leelabird.ru
NUXT_PUBLIC_TRACKNODE_TRACKER_SRC=https://tracknode.ru/tracker.js
PUBLIC_SITE_VITE_API_URL=https://tracknode.ru/api
PUBLIC_SITE_VITE_BACKEND_URL=https://tracknode.ru
PUBLIC_SITE_VITE_SITE_URL=https://leelabird.ru
PUBLIC_SITE_VITE_PUBLIC_SITE_URL=https://leelabird.ru
```

Update `ydro/vue-admin/.env`: change every `https://tracknode.ru` to `https://tracknode.ru`.

Run HTTPS compose:

```bash
cd ~/projects/v2/ydro
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml config
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml up -d --build
```

Check:

```bash
curl -I https://tracknode.ru
curl -I https://tracknode.ru/admin/
curl -I https://tracknode.ru/api/
curl -I https://leelabird.ru
```

Reload nginx after config-only changes:

```bash
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml exec nginx nginx -s reload
```

Restart nginx if reload is not enough:

```bash
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml restart nginx
```

## 4. Database and safety

PostgreSQL and Redis use named Docker volumes:

- `postgres_data`
- `redis_data`
- `static_data`
- `media_data`

Do not run `docker compose down -v` on production unless you intentionally want to delete data.

The backend entrypoint waits for PostgreSQL, runs migrations, and runs `collectstatic` by default.

## 5. Optional standalone A Meditation

Only use this if you do not want `ydro` nginx to serve `leelabird.ru`:

```bash
cd ~/projects/v2/a-meditation/frontend
cp .env.example .env
docker compose --env-file .env config
docker compose --env-file .env up -d --build
```

In the recommended unified deploy, do not expose PostgreSQL, Redis or Django backend directly. Externally open only ports `80` and `443` through nginx.
