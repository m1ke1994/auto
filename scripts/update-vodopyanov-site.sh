#!/usr/bin/env bash
# Update only stariy-site.ru while retaining the working TrackNode and other sites.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Stop full autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
  exit 1
fi
if systemctl is-active --quiet yadro-autodeploy.service; then
  echo "Full autodeploy service is running; not updating another site concurrently." >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Uncommitted server changes detected; not continuing." >&2
  git status --short
  exit 1
fi
if ! sudo test -s /etc/letsencrypt/live/stariy-site.ru/fullchain.pem; then
  echo "Existing stariy-site.ru certificate not found; stopped without changes." >&2
  exit 1
fi

# ONE lock for the entire update, shared with the standalone registration script
# and normal deployments. The CMS operations below do not try to reacquire it.
exec 9>/tmp/yadro-autodeploy.lock
if ! flock -w 30 9; then
  echo "Deployment lock remains busy. No database or running site was changed." >&2
  if command -v fuser > /dev/null; then fuser -v /tmp/yadro-autodeploy.lock || true; fi
  exit 1
fi

cd ydro
dc() {
  # Do not leak the lock file descriptor into Docker/BuildKit child processes.
  docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@" 9>&-
}
dc config --quiet
. "$ROOT/scripts/lib/vodopyanov-cms.sh"

echo "=== Build the independent public site before changing live services ==="
dc build vodopyanov_site

echo "=== CMS registration dry run (no database writes) ==="
vodopyanov_cms_register --check

echo "=== Verified backup and creation of missing CMS pages ==="
vodopyanov_cms_register --apply

echo "=== Recreate only the author's site (other containers untouched) ==="
dc up -d --no-deps vodopyanov_site

state=""
for attempt in {1..90}; do
  state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' ydro-vodopyanov_site-1 2>/dev/null || true)"
  if [[ "$state" == healthy ]]; then break; fi
  if [[ "$state" == unhealthy ]]; then
    docker logs --tail 80 ydro-vodopyanov_site-1 >&2
    exit 1
  fi
  sleep 2
done
if [[ "$state" != healthy ]]; then
  echo "Author-site container failed to become healthy." >&2
  exit 1
fi

echo "=== Public author site checks ==="
for path in / /poems.html /songs.html /favicon.ico /favicon-16.png /favicon-32.png; do
  curl --fail --silent --show-error --max-time 20 -o /dev/null "https://stariy-site.ru$path"
  echo "OK: https://stariy-site.ru$path"
done

echo "=== Verify separate CMS pages and existing site identity ==="
curl --fail --silent --show-error --max-time 20 https://tracknode.ru/api/sites/vodopyanov/ \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
site=data["site"]
assert site["slug"] == "vodopyanov" and site["domain"] == "stariy-site.ru"
required={"hero","word","about","poems","songs","outro","contacts","catalog-poems","catalog-songs","home-seo"}
keys={item["key"] for item in data["sections"]}
assert required.issubset(keys), "Missing CMS sections: " + str(required-keys)
print("OK: "+str(len(keys))+" CMS sections, including catalog pages and home SEO")
'
echo "Vodopyanov update succeeded. Production backend, PostgreSQL and other sites were not restarted."
