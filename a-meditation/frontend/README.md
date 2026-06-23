# AMeditation Frontend

Public Vue site connected to Yadro through HTTP API.

## Env

Required values:

```env
VITE_API_URL=http://tracknode.ru/api
VITE_BACKEND_URL=http://tracknode.ru
VITE_SITE_SLUG=a-meditation
VITE_SITE_URL=http://leelabird.ru
VITE_PUBLIC_SITE_URL=http://leelabird.ru
VITE_TRACKER_SITE_KEY=
PUBLIC_SITE_PORT=3000
```

HTTPS values after certificates are installed:

```env
VITE_API_URL=https://tracknode.ru/api
VITE_BACKEND_URL=https://tracknode.ru
VITE_SITE_URL=https://leelabird.ru
VITE_PUBLIC_SITE_URL=https://leelabird.ru
```

`VITE_API_URL`, `VITE_BACKEND_URL`, `VITE_SITE_URL` and `VITE_PUBLIC_SITE_URL` are required at build time. They are public browser values, not secrets.
`VITE_TRACKER_SITE_KEY` must match the Yadro `Site.api_key` for `VITE_SITE_SLUG`.
`robots.txt`, `sitemap.xml`, canonical and OG URLs are generated from `VITE_PUBLIC_SITE_URL`.

## Local Development

```bash
npm ci
npm run dev
```

The dev server listens on `http://localhost:3000` by default.

## Production Docker

```bash
cp .env.example .env
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

The production image builds static Vue assets and serves them with nginx on `${PUBLIC_SITE_PORT:-3000}`.
