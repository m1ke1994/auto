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

## Stage 2: structured AI generation (local only)
The local demo now creates thematic design specifications and Vue/Vite ZIP exports. Navigation is section-based, not separate routes. Existing projects remain readable; edit to migrate a legacy revision to the new format. AI provider uses direct REST; it is not OpenHands. No arbitrary model-generated code executes on Django. The 3D style is a visual direction only.

Copy .env.studio.example to .env.studio.local. Set STUDIO_AI_PROVIDER=yandex, STUDIO_AI_KEY, STUDIO_AI_FOLDER, STUDIO_AI_MODEL to the exact model ID available in your catalog. Or use deepseek with key and model. Never commit the file. Recreate backend with docker compose --env-file .env.studio.local -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml up -d --build postgres redis backend frontend. For no keys keep demo. Run python manage.py test ai_builder inside backend. Generation is synchronous for local testing, timeout ~75s. No automatic remote deployment.

Optional offline build check: extract the generated ZIP into a fresh source directory (no node_modules); create a fresh output directory. Build the trusted runner image with docker build -t tracknode-studio-build -f docker/studio-build/Dockerfile docker/studio-build. Run docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 768m --cpus 1 --pids-limit 128 --tmpfs /work:rw,exec,size=192m,uid=1000,gid=1000 --tmpfs /tmp:rw,size=64m --mount type=bind,source=ABS_SOURCE,target=/source,readonly --mount type=bind,source=ABS_OUTPUT,target=/output tracknode-studio-build. Use writable output directory for uid 1000. This manual build check is not yet integrated in the UI or a hostile-code sandbox. Do not mount secrets or the main repository. No Docker socket in backend.

Next: separate OpenHands worker with ephemeral sandbox and scoped credentials, async queue, build artifacts and visual checks, GitHub App and Vercel preview.

## Windows startup / troubleshooting

From the ydro directory run:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-studio.ps1
```
Use `-SkipBuild` to reuse the current images, or `-Test` to run Studio tests after startup. The script uses the existing tracknode20 project and database volumes, optionally reads .env.studio.local, validates Compose, builds images, waits for the HTTP healthcheck, checks Django and prints migration status. Failure prints service logs and healthcheck output. No destructive cleanup is performed.

Dockerfile.studio is separate from production Dockerfile.backend. It normalizes the entrypoint inside the image, checks shell and Python syntax, installs dependencies from official PyPI, and checks package consistency. Studio health checks target localhost inside the backend container, allow time for real migrations, and do not conceal failed application startup. The local override disables example site seeding. Docker Desktop with Compose supporting --wait is required.

If a previous local Git patch conflicts during pull, keep a backup and resolve the conflicting files before building. Do not delete database volumes or run git reset --hard. A successful build alone does not guarantee that migrations or runtime checks pass. Inspect logs if any check fails.
