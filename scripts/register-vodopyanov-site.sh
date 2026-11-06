#!/usr/bin/env bash
# Standalone non-destructive CMS registration, sharing the same lock as updates.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="--check"
if [[ "$#" -gt 0 ]]; then MODE="$1"; fi
if [[ "$MODE" != "--check" && "$MODE" != "--apply" ]]; then
  echo "Usage: bash scripts/register-vodopyanov-site.sh [--check|--apply]" >&2
  exit 2
fi
if systemctl is-active --quiet yadro-autodeploy.timer; then
  echo "Pause autodeploy first: sudo systemctl stop yadro-autodeploy.timer" >&2
  exit 1
fi
if systemctl is-active --quiet yadro-autodeploy.service; then
  echo "Full autodeploy service is running; refusing simultaneous registration." >&2
  exit 1
fi
cd "$ROOT"
if [[ -n "$(git status --porcelain)" ]]; then
  git status --short
  echo "Git is not clean; review server changes before continuing." >&2
  exit 1
fi
exec 9>/tmp/yadro-autodeploy.lock
if ! flock -w 30 9; then
  echo "Deployment lock is busy. Nothing changed; check the owner:" >&2
  if command -v fuser > /dev/null; then fuser -v /tmp/yadro-autodeploy.lock || true; fi
  exit 1
fi
cd ydro
dc() {
  docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@" 9>&-
}
. "$ROOT/scripts/lib/vodopyanov-cms.sh"
vodopyanov_cms_register "$MODE"
echo "Registration finished; existing containers were not restarted."
