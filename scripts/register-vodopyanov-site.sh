#!/usr/bin/env bash
# Add only the author site to the existing database. No migrations or resets.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:---check}" in
  --check) APPLY=False ;;
  --apply) APPLY=True ;;
  *) echo "Usage: bash scripts/register-vodopyanov-site.sh [--check|--apply]" >&2; exit 2 ;;
esac
cd "$ROOT/ydro"
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml "$@"; }
read -r -d '' PYTHON_CODE <<'PY' || true
from django.db import transaction
from apps.sites.models import Site
from clients.services import get_or_create_client_for_site

slug = "vodopyanov"
domain = "stariy-site.ru"
name = "Александр Водопьянов — автор песен и стихов"
apply = __APPLY__

with transaction.atomic():
    if Site.objects.filter(domain__iexact=domain).exclude(slug=slug).exists():
        raise RuntimeError("Domain stariy-site.ru is already assigned to another site. Aborted.")
    tracknode = Site.objects.select_related("owner").filter(slug="tracknode").first()
    if tracknode is None:
        raise RuntimeError("TrackNode site/owner is missing. Aborted.")
    existing = Site.objects.select_for_update().filter(slug=slug).first()
    if existing is not None:
        if existing.domain.lower().strip() != domain or existing.owner_id != tracknode.owner_id:
            raise RuntimeError("Existing site has a different domain or owner. Manual review required.")
        print("Site already registered: id=%s slug=%s domain=%s (no changes)" % (existing.pk, slug, domain))
    elif not apply:
        print("DRY RUN: would create a new site with slug=%s domain=%s using TrackNode owner" % (slug, domain))
    else:
        site = Site.objects.create(
            name=name, slug=slug, domain=domain,
            owner=tracknode.owner, is_active=True,
            seo={
                "title": "Александр Водопьянов — стихи и песни",
                "description": "Стихи и песни Александра Водопьянова. Кинематографическая история автора.",
                "canonical": "https://stariy-site.ru/",
            },
        )
        get_or_create_client_for_site(site)
        print("CREATED: id=%s slug=%s domain=%s owner_id=%s" % (site.pk, site.slug, site.domain, site.owner_id))
PY
PYTHON_CODE="${PYTHON_CODE/__APPLY__/$APPLY}"
dc exec -T backend python manage.py shell -c "$PYTHON_CODE"
