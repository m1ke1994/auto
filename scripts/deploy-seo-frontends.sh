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
# Check the real reverse-proxy rules on the host, not inside the frontend image.
nginx_template="$PROJECT_DIR/ydro/docker/nginx/templates-https/default.conf.template"
for path in sozdanie-saitov seo-audit analitika-saita upravlenie-zayavkami; do
  if ! grep -Fq "$path" "$nginx_template"; then
    echo "Nginx indexability rule is missing for $path. Stopped."
    exit 1
  fi
done
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
# Do not trust a pre-existing index.html in the shared volume: verify the new
# prerendered pages and sitemap before declaring the frontend healthy.
for service in "${services[@]}"; do
  container="ydro-${service}-1"
  healthy=0
  for attempt in {1..90}; do
    status="$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || true)"
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null || true)"
    if [ "$status" = running ] && [ "$state" = healthy ]; then
      if [ "$service" != frontend ]; then
        healthy=1
        break
      fi
      if dc exec -T nginx sh -ec '
        set -eu
        test -s /var/www/frontend/sitemap.xml
        for route in sozdanie-saitov seo-audit analitika-saita upravlenie-zayavkami; do
          test -s "/var/www/frontend/$route/index.html"
          grep -Fq "https://tracknode.ru/$route" /var/www/frontend/sitemap.xml
        done
        grep -Fq "Технический SEO-аудит сайта и поиск ошибок" /var/www/frontend/seo-audit/index.html
      '; then
        healthy=1
        break
      fi
    fi
    sleep 2
  done
  if [ "$healthy" != 1 ]; then
    echo "Deployment not ready: $container. Check 'docker logs --tail 100 $container'."
    echo "The previous public files may still be served; nginx was not reloaded."
    exit 1
  fi
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
  if [ "$domain" = tracknode.ru ]; then
    public_html="$(curl --fail --silent --show-error --max-time 20 -H 'Cache-Control: no-cache' "https://tracknode.ru/seo-audit")"
    case "$public_html" in
      *'<title>Технический SEO-аудит сайта и поиск ошибок | TrackNode</title>'*) ;;
      *) echo "Published SEO title is missing on tracknode.ru/seo-audit. Stopped."; exit 1 ;;
    esac
  fi
  printf 'HTTP checks passed: %s\n' "$domain"
done
echo 'Frontends updated. PostgreSQL/backend/workers were not restarted; no migrations or seeds ran.'
echo 'Full autodeploy remains paused. Review its migration/seed behavior before enabling it.'
