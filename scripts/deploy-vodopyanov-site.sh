#!/usr/bin/env bash
# Stage 1: deploy the independent site and HTTP ACME validation without touching DB services.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Pause autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
  exit 1
fi
exec 9>/tmp/yadro-autodeploy.lock
flock -n 9 || { echo "Another deployment is running; stopped." >&2; exit 1; }
cd "$ROOT"
if [ -n "$(git status --porcelain)" ]; then
  echo "Local Git changes found; review before deploying." >&2
  git status --short
  exit 1
fi
# An already-enabled HTTPS template is valid only with a real certificate.
if [ -e ydro/docker/nginx/templates-https/stariy-site-https.conf.template ]; then
  if ! sudo test -s /etc/letsencrypt/live/stariy-site.ru/fullchain.pem; then
    echo "HTTPS configuration exists but its certificate is missing. Stopped before touching Nginx." >&2
    exit 1
  fi
fi
cd ydro
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }
dc config --quiet

mkdir -p /home/alex/auto/backups
backup="/home/alex/auto/backups/before_vodopyanov_$(date +%F_%H-%M-%S).dump"
dc exec -T postgres pg_dump -U yadro_user -Fc yadro_db > "$backup"
test -s "$backup"
dc exec -T postgres pg_restore --list < "$backup" >/dev/null
echo "Backup readable: $backup"

# Build and start the author site FIRST; running services are left untouched on build failure.
dc build vodopyanov_site
dc up -d --no-deps vodopyanov_site
for attempt in {1..90}; do
  state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' ydro-vodopyanov_site-1 2>/dev/null || true)"
  if [ "$state" = healthy ]; then break; fi
  if [ "$state" = unhealthy ]; then
    docker logs --tail 70 ydro-vodopyanov_site-1 >&2
    exit 1
  fi
  sleep 2
done
if [ "${state:-}" != healthy ]; then
  echo "Author site is not healthy; proxy was not changed." >&2
  exit 1
fi
# Nginx already has templates-https bind-mounted. Reload in place, without
# restarting the proxy or interrupting existing site containers.
dc exec -T nginx sh -ec '
  /docker-entrypoint.d/20-envsubst-on-templates.sh
  nginx -t
  nginx -s reload
'

for domain in tracknode.ru leelabird.ru novoe-konakovo.ru tishechkinalexandr.ru; do
  curl --fail --silent --show-error --max-time 15 -o /dev/null "https://$domain/"
  echo "Existing website verified: $domain"
done
echo "HTTP ACME phase ready. Request certificate before enabling the HTTPS config."
echo "No migrations, seeds, volume removals or database writes were performed."
