#!/usr/bin/env bash
# Isolated update of the author site only. Existing website services stay up.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Stop full autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
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

cd ydro
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }
dc config --quiet

echo "=== Build the independent public site before changing live services ==="
dc build vodopyanov_site

echo "=== CMS registration dry run (no database writes) ==="
bash "$ROOT/scripts/register-vodopyanov-site.sh" --check

echo "=== Backup and add missing CMS pages (preserve existing data) ==="
bash "$ROOT/scripts/register-vodopyanov-site.sh" --apply

echo "=== Recreate only the author's site ==="
dc up -d --no-deps vodopyanov_site

for attempt in {1..90}; do
  state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' ydro-vodopyanov_site-1 2>/dev/null || true)"
  if [[ "$state" == healthy ]]; then break; fi
  if [[ "$state" == unhealthy ]]; then
    docker logs --tail 80 ydro-vodopyanov_site-1 >&2
    exit 1
  fi
  sleep 2
done
if [[ "${state:-}" != healthy ]]; then
  echo "Author-site container failed to become healthy." >&2
  exit 1
fi

echo "=== Public site checks ==="
for path in / /poems.html /songs.html /favicon.ico; do
  curl --fail --silent --show-error --max-time 20 -o /dev/null "https://stariy-site.ru$path"
  echo "OK: https://stariy-site.ru$path"
done

echo "=== CMS API checks (tracker key is not printed) ==="
curl --fail --silent --show-error --max-time 20 https://tracknode.ru/api/sites/vodopyanov/ \
  | python3 -c '
import json, sys
d = json.load(sys.stdin)
assert d["site"]["slug"] == "vodopyanov"
assert d["site"]["domain"] == "stariy-site.ru"
required = {"hero","word","about","poems","songs","outro","contacts","catalog-poems","catalog-songs","home-seo"}
keys = {row["key"] for row in d["sections"]}
assert required.issubset(keys), "Missing CMS sections: " + str(required-keys)
print("OK: "+str(len(keys))+" CMS sections, including both catalog pages and homepage SEO")
'
echo "Vodopyanov site-only update succeeded. Other sites and backend were not restarted."
