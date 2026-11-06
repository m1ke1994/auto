#!/usr/bin/env bash
# Stage 2: enable HTTPS only after certbot has successfully issued the certificate.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Pause autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
  exit 1
fi
sudo test -s /etc/letsencrypt/live/stariy-site.ru/fullchain.pem
sudo test -s /etc/letsencrypt/live/stariy-site.ru/privkey.pem
cd "$ROOT"
exec 9>/tmp/yadro-autodeploy.lock
flock -n 9 || { echo "Another deployment is running; stopped." >&2; exit 1; }
src="ydro/docker/nginx/templates-https/stariy-site-https.conf.template.example"
dst="ydro/docker/nginx/templates-https/stariy-site-https.conf.template"
test -s "$src"
if [ -e "$dst" ]; then
  cmp -s "$src" "$dst" || { echo "Existing HTTPS template differs; manual review required." >&2; exit 1; }
else
  cp "$src" "$dst"
fi
# A generated environment-specific Nginx template is excluded only on this server.
grep -qxF "/$dst" .git/info/exclude || printf '/%s\n' "$dst" >> .git/info/exclude
cd ydro
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }
if ! dc exec -T nginx sh -ec '
  /docker-entrypoint.d/20-envsubst-on-templates.sh
  nginx -t
'; then
  echo "HTTPS config failed validation; existing Nginx workers were not reloaded." >&2
  exit 1
fi
dc exec -T nginx nginx -s reload
curl --fail --silent --show-error --max-time 20 -o /dev/null https://stariy-site.ru/
curl --fail --silent --show-error --max-time 20 -o /dev/null https://stariy-site.ru/poems.html
curl --fail --silent --show-error --max-time 20 -o /dev/null https://stariy-site.ru/songs.html
echo "HTTPS author site verified. Certificate renewal remains managed by certbot."
