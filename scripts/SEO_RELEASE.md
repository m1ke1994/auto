# SEO: public sites and TrackNode attribution

Scope: tracknode.ru, leelabird.ru, novoe-konakovo.ru, tishechkinalexandr.ru — the four public domains in the current Compose configuration. No database migrations, seeds, or saved customer data are modified.

Each site's build renders public HTML before JavaScript. Canonical URLs and sitemap entries belong to that site's own domain. The TrackNode organization/application have stable identifiers in JSON-LD, and the other three sites show a visible `by TrackNode` link. Client sites retain their own names and identity; they are not marked as alternate versions (`sameAs`) of TrackNode.

Public content snapshots are fetched from the existing public API at build time. An unavailable/invalid API stops publication rather than publishing empty pages. `SEO_ALLOW_DEFAULT_CONTENT=1` is for local verification only; do not enable it on production. `SEO_CONTENT_FILE` accepts an explicit test fixture for integration tests; do not set it on production. Rebuild the corresponding public site after publishing CMS changes so its initial HTML and sitemap are refreshed. Live client-side API loading and lead forms are unchanged.

## Verification

- Build TrackNode with the existing production environment (`npm run build`) or the committed example environment (`npm run build:local`).
- Build the other three sites with their existing VITE_API_URL, VITE_BACKEND_URL and VITE_PUBLIC_SITE_URL settings.
- From repository root, run `node scripts/check-network-seo.mjs` after all four builds and `python scripts/test-seo-head.py`.
- Run the existing portfolio tests and TrackNode auth/landing/tracker tests.
- Run `nginx -t` against the rendered production configuration before reloading nginx.

## Publishing without database operations

The concrete deployment command after the reviewed release is pulled is `bash scripts/deploy-seo-frontends.sh`. It refuses to run while the full autodeploy timer is active, takes the existing deployment lock, backs up PostgreSQL, builds and checks the four frontend images, waits for health, regenerates/tests nginx configuration and reloads nginx. It never runs migrations, seeds or backend/PostgreSQL restarts.

The current server autodeploy script builds backend services and runs migrations unconditionally. This SEO change does not require migrations or restarting PostgreSQL. For a maintenance release, pause the timer and use the deployment lock; keep the verified PostgreSQL backup procedure. Build frontend, public_site, volga_site and my_portfolio_site first. Leelabird also carries WebSite/creator microdata in its footer, because its existing backend replaces JSON-LD in editable SEO heads. No backend code refresh is needed. Recreate only the four frontend services with `--no-deps`; do not restart backend or workers for this release. Test nginx configuration, reload and verify health.

After publication, check HTTP status, Content-Type and content of /robots.txt, /sitemap.xml, the homepages, a real article/service route, a nonexistent URL and a private TrackNode URL. Confirm that scripts/assets and leads still work. Confirm no `SEO_CONTENT_FILE` or `SEO_ALLOW_DEFAULT_CONTENT` test overrides are configured.

Submit each domain and sitemap separately in Google Search Console and Yandex Webmaster using the actual owners' accounts. Do not invent verification tokens. Inspection and reindexing require those accounts; a code change cannot guarantee indexing, rankings or rich results.
