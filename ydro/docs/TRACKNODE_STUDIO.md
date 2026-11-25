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

## DeepSeek local setup
Create .env.studio.local with STUDIO_AI_PROVIDER=deepseek, STUDIO_AI_KEY=<your private key>, STUDIO_AI_MODEL=deepseek-v4-pro (or deepseek-flash), STUDIO_AI_FOLDER empty. Obtain a key and API balance from https://platform.deepseek.com/. Use --env-file .env.studio.local with all Compose commands, in particular up -d --build postgres redis backend frontend. The provider sends non-thinking JSON mode requests to the official API. No API key is required for the mocked tests. Live requests incur provider charges and send the project prompt and prior design to DeepSeek. This remains a structured design generator, not arbitrary code generation.

## Stage 3a: OpenHands SDK local proof of integration
Separate Compose project, no changes to the running Django/Vue app and no new migrations.
Pinned OpenHands SDK 1.63.1, DeepSeek Chat Completions (non-thinking). The SDK agent has a custom, bounded in-memory project-file tool; no terminal, file editor, shell, Docker socket, app DB or repo mount. Only the final ZIP is written to a fresh host output directory. The agent's network has outbound access; this is not a hostile multi-tenant sandbox. No generated code is run in the agent. Keep artifacts untrusted. Budget target $0.30 per run is SDK-estimated, not a guaranteed hard billing cap; iteration limit 12 and wall limit 600s. Prompt is sent to DeepSeek. Use trusted local prompts only.
Windows PowerShell from ydro:
```powershell
docker compose --env-file .env.studio.local -p tracknode20-agent -f docker-compose.openhands.yml build openhands
docker compose --env-file .env.studio.local -p tracknode20-agent -f docker-compose.openhands.yml run --rm --no-deps openhands --check
$out = (New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/" + [guid]::NewGuid().ToString())) -Force).FullName
docker compose --env-file .env.studio.local -p tracknode20-agent -f docker-compose.openhands.yml run --rm --no-deps -v "${out}:/output" openhands --prompt "Create a premium architecture studio website in Russian with original editorial design, responsive navigation, portfolio concepts and subtle animation."
Get-ChildItem $out
```
This is a CLI proof; Studio UI still uses the structured design provider. Next stage: isolated offline build, async jobs, revision import/preview and per-project context. No arbitrary generated dependencies or automated deployment yet.

## Stage 3b: quality profiles and motion toolkit
The standalone OpenHands runner accepts --profile standard, premium (default), or cinema. It must save an art-direction plan before writing and a source self-review after the final write. Both are included in the ZIP and are AI-generated, not independently verified. Vue, Three.js r180, GSAP 3.13 and Lenis 1.3.20 are preinstalled in the trusted offline builder and pinned in the exported package manifest. No generated package installation, shell or network tools. GSAP's standard license FAQ allows AI-generated code; revisit the license before expanding into a competing visual animation editor. https://gsap.com/standard-license/
SDK custom cost estimates use official peak cache-miss rates as of 2026-11-25 (Pro $1.32 input/$3.96 output per million; Flash $0.30/$1.20). Target $0.60/run, 18 iterations, 900 second wall timeout; not a hard billing cap and pricing may change. Check actual DeepSeek usage. No separate paid art-director request, and no visual critic or automatic repair yet.
Rebuild BOTH agent and builder before using new exports. Use studio-quality.ps1 to generate in a fresh directory then run the trusted build without networking or credentials. Output source and dist are kept separate; do not mount main repo or secrets. Build success does not mean visual quality is verified. Studio web UI unchanged.

## Pexels photo integration (local)
Set PEXELS_API_KEY only in ignored .env.studio.local. Never commit a real key or include it in a generated project. Run the standalone agent's --check-media to verify a search and one optimized photo download without any DeepSeek request. The agent can search up to five times and download up to six photos from the Pexels CDN per generation. Selection is based on search metadata, not image vision. Images are re-encoded to local WebP at up to 1920px, with credits in MEDIA_CREDITS.json and a visible Pexels/photographer link in exported index.html. No remote image dependency at runtime. Stock images must not be misrepresented as actual client work or real people from a brief. Review Pexels API terms before commercial launch. If no key is configured, the generator can use procedural imagery. Video and other stock providers are not implemented.

## Landing page reading progress
Every new agent export includes a trusted src/landing-progress.js module invoked by main.js. It renders a fixed 3px horizontal indicator at the viewport top, scales left to right by native document scroll progress, and updates on scroll and resize. Set :root --tn-progress-color to the design accent. Agent-generated duplicate progress bars and nested full-page scrolling are prohibited by the design prompt. Existing exported ZIPs are unchanged; their old custom progress elements need to be removed separately. Browser validation remains pending.
