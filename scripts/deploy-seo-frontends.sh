#!/usr/bin/env bash
# Run after reviewing/pulling the SEO release, with autodeploy paused.
set -Eeuo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Pause the full autodeploy first: sudo systemctl stop yadro-autodeploy.timer"
  exit 1
fi
exec 9>/tmp/yadro-autodeploy.lock
flock -n 9 || { echo "Another deployment is running. Stopped."; exit 1; }
cd "$PROJECT_DIR"
if [ -n "$(git status --porcelain)" ]; then
  echo "Review local changes before deployment. Stopped."
  git status --short
  exit 1
fi
services=(frontend public_site volga_site my_portfolio_site)
domains=(tracknode.ru leelabird.ru novoe-konakovo.ru tishechkinalexandr.ru)
if [ "${1:-}" = "--tracknode-only" ]; then
  services=(frontend)
  domains=(tracknode.ru)
elif [ "$#" -gt 0 ]; then
  echo "Usage: bash scripts/deploy-seo-frontends.sh [--tracknode-only]"
  exit 1
fi
cd ydro
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }
mkdir -p /home/alex/auto/backups
backup="/home/alex/auto/backups/before_seo_$(date +%F_%H-%M-%S).dump"
dc exec -T postgres pg_dump -U yadro_user -Fc yadro_db > "$backup"
test -s "$backup"
dc exec -T postgres pg_restore --list < "$backup" > /dev/null
printf 'Backup readable: %s\n' "$backup"
# Build first: a failed build leaves the currently running sites untouched.
dc build "${services[@]}"
# Validate public-site configs in their newly built images before replacing containers.
for service in "${services[@]}"; do
  [ "$service" != frontend ] || continue
  dc run --rm --no-deps --entrypoint nginx "$service" -t
done
dc up -d --no-deps "${services[@]}"
for service in "${services[@]}"; do
  container="ydro-${service}-1"
  healthy=0
  for attempt in {1..60}; do
    state="$(docker inspect -f '{{.State.Health.Status}}' "$container")"
    if [ "$state" = healthy ]; then healthy=1; break; fi
    sleep 2
  done
  if [ "$healthy" != 1 ]; then echo "Unhealthy: $container. Check logs; nginx was not reloaded."; exit 1; fi
done
# Templates are mounted, but nginx generates its active config only at startup.
dc exec -T nginx sh -ec '
  cp /etc/nginx/conf.d/default.conf /tmp/default.conf.before-seo
  /docker-entrypoint.d/20-envsubst-on-templates.sh
  if ! nginx -t; then
    cp /tmp/default.conf.before-seo /etc/nginx/conf.d/default.conf
    exit 1
  fi
  nginx -s reload
'
for domain in "${domains[@]}"; do
  curl --fail --silent --show-error --max-time 20 -o /dev/null "https://$domain/"
  curl --fail --silent --show-error --max-time 20 -o /dev/null "https://$domain/robots.txt"
  curl --fail --silent --show-error --max-time 20 -o /dev/null "https://$domain/sitemap.xml"
  printf 'HTTP checks passed: %s\n' "$domain"
done
echo 'Frontends updated. PostgreSQL/backend/workers were not restarted; no migrations or seeds ran.'
echo 'Full autodeploy remains paused. Review its migration/seed behavior before enabling it.'
