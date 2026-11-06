#!/usr/bin/env bash
# Isolated management command: creates only missing author-site content.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="--check"
if [[ "$#" -gt 0 ]]; then MODE="$1"; fi
if [[ "$MODE" != "--check" && "$MODE" != "--apply" ]]; then
  echo "Usage: bash scripts/register-vodopyanov-site.sh [--check|--apply]" >&2
  exit 2
fi
if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Pause full autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
  exit 1
fi
exec 9>/tmp/yadro-autodeploy.lock
flock -n 9 || { echo "Another deployment is running; stopped." >&2; exit 1; }
cd "$ROOT"
if [ -n "$(git status --porcelain)" ]; then
  git status --short
  echo "Git not clean; review local changes before continuing." >&2
  exit 1
fi
cd ydro
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }

# Rebuild the backend IMAGE; the production backend container keeps running.
dc build backend
if [[ "$MODE" == "--apply" ]]; then
  mkdir -p /home/alex/auto/backups
  backup="/home/alex/auto/backups/before_vodopyanov_cms_$(date +%F_%H-%M-%S).dump"
  dc exec -T postgres pg_dump -U yadro_user -Fc yadro_db > "$backup"
  test -s "$backup"
  dc exec -T postgres pg_restore --list < "$backup" > /dev/null
  echo "Readable backup: $backup"
fi
# Entry point deliberately bypassed: no migration, old-site seed or restart.
dc run --rm --no-deps -T --entrypoint python backend manage.py seed_vodopyanov_site "$MODE"
echo "Existing production containers have not been restarted."
