# TrackNode Studio 2.0 — local MVP slice

This branch does not deploy production. Demo uses deterministic escaped static HTML, not AI.
Existing accounts/JWT are reused. Each project and revision is owner-scoped.
Local approval records a revision only; it does not host a site. ZIP contains portable HTML.

## Local Docker
From ydro:
```sh
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml up --build -d postgres redis backend frontend
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml exec backend python manage.py migrate
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml exec backend python manage.py test ai_builder
```
Open http://localhost:8001/studio and sign in/register. Stop using compose down (never -v).
Use a separate checkout and ensure ports 8000/8001 are free. No production credentials.
For native Django set STUDIO_DEMO_ENABLED=1 and SQLITE_NAME=studio-local.sqlite3, migrate and run.

## Pending real integrations
OpenHands SDK + approved Yandex AI model; isolated build runner; GitHub App; protected Vercel previews; own-server static artifact deployment; DNS/TLS; analytics/leads/SEO; credits and payment. No simulated success for these. Do not run arbitrary generated code in the Django container. Keep the feature disabled in production. 
