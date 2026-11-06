"""Idempotent, non-destructive registration of the editable author site."""
from copy import deepcopy

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.sites.models import SectionSchema, Site, SiteSection
from apps.sites.vodopyanov_site import SITE_DOMAIN, SITE_NAME, SITE_SEO, SITE_SLUG, SECTION_SEEDS
from clients.services import get_or_create_client_for_site


class Command(BaseCommand):
    help = "Register the separate Vodopyanov website and missing editable sections; preserve existing edits."

    def add_arguments(self, parser):
        parser.add_argument("--check", action="store_true", help="Verify plan without database writes.")
        parser.add_argument("--apply", action="store_true", help="Create only missing site and sections.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["apply"] == options["check"]:
            raise CommandError("Choose exactly one of --check or --apply.")

        conflict = Site.objects.filter(domain__iexact=SITE_DOMAIN).exclude(slug=SITE_SLUG).exists()
        if conflict:
            raise CommandError("stariy-site.ru is assigned to another site: no changes were made.")

        tracknode = Site.objects.select_related("owner").filter(slug="tracknode").first()
        if not tracknode or not tracknode.owner_id:
            raise CommandError("TrackNode owner is not available: no changes were made.")

        existing = Site.objects.select_for_update().filter(slug=SITE_SLUG).first()
        if existing and (
            existing.domain.strip().lower() != SITE_DOMAIN
            or existing.owner_id != tracknode.owner_id
        ):
            raise CommandError("Existing Vodopyanov slug has a different domain or owner; manual review required.")

        missing = [seed for seed in SECTION_SEEDS if not existing or not SiteSection.objects.filter(site=existing, key=seed["key"]).exists()]
        self.stdout.write(
            f"site={'existing' if existing else 'new'}, missing_sections={len(missing)}, "
            f"existing_sections={(existing.sections.count() if existing else 0)}"
        )

        if options["check"]:
            self.stdout.write("DRY RUN: database was not modified.")
            return

        if existing:
            site = existing
            self.stdout.write("Existing site preserved (SEO, owner, token and settings unchanged).")
        else:
            site = Site.objects.create(
                slug=SITE_SLUG, name=SITE_NAME, domain=SITE_DOMAIN,
                owner=tracknode.owner, is_active=True, seo=deepcopy(SITE_SEO),
            )
            self.stdout.write(f"Created site id={site.id}.")

        # This only creates a client for the same owner if the account had none.
        get_or_create_client_for_site(site)
        created = 0
        for item in SECTION_SEEDS:
            key = item["key"]
            schema_key = f"{SITE_SLUG}-{key}"
            SectionSchema.objects.get_or_create(
                section_key=schema_key,
                defaults={
                    "title": item["title"],
                    "schema": deepcopy(item["schema"]),
                    "description": f"Поля сайта Водопьянова: {item['title']}.",
                },
            )
            section, was_created = SiteSection.objects.get_or_create(
                site=site, key=key,
                defaults={
                    "title": item["title"], "section_type": key,
                    "component_key": f"{SITE_SLUG}-{key}", "order": item["order"],
                    "is_active": True,
                    "schema": deepcopy(item["schema"]),
                    "content": deepcopy(item["content"]),
                    "settings": {"source": SITE_SLUG},
                },
            )
            if was_created:
                section.full_clean()
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Vodopyanov registration complete: site_id={site.id}, "
            f"sections_created={created}, sections_preserved={len(SECTION_SEEDS)-created}."
        ))
