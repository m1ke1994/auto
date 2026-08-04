import os
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.sites.a_meditation import merge_content_defaults
from apps.sites.models import SectionSchema, Site, SiteSection
from apps.sites.my_portfolio_site import (
    MY_PORTFOLIO_SECTION_SEEDS,
    MY_PORTFOLIO_SITE_DOMAIN,
    MY_PORTFOLIO_SITE_NAME,
    MY_PORTFOLIO_SITE_SEO,
    MY_PORTFOLIO_SITE_SLUG,
    get_my_portfolio_schema_key,
)
from apps.sites.tracknode_site import TRACKNODE_SITE_SLUG
from clients.services import get_or_create_client_for_site


class Command(BaseCommand):
    help = "Create or update the editable Alexandr Tishechkin portfolio public site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-email",
            help="Assign portfolio site to an existing user. Defaults to current portfolio owner, TrackNode owner, or an administrator.",
        )
        parser.add_argument(
            "--reset-content",
            action="store_true",
            help="Replace content edited in admin with current seed values.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        existing_site = Site.objects.select_related("owner").filter(slug=MY_PORTFOLIO_SITE_SLUG).first()
        tracknode_site = Site.objects.select_related("owner").filter(slug=TRACKNODE_SITE_SLUG).first()
        owner = self._resolve_owner(
            existing_site=existing_site,
            tracknode_site=tracknode_site,
            requested_email=options.get("owner_email"),
        )
        reset_content = bool(options.get("reset_content"))

        current_seo = existing_site.seo if existing_site and isinstance(existing_site.seo, dict) else {}
        site, site_created = Site.objects.update_or_create(
            slug=MY_PORTFOLIO_SITE_SLUG,
            defaults={
                "name": MY_PORTFOLIO_SITE_NAME,
                "domain": MY_PORTFOLIO_SITE_DOMAIN,
                "owner": owner,
                "is_active": True,
                "seo": (
                    deepcopy(MY_PORTFOLIO_SITE_SEO)
                    if reset_content or not current_seo
                    else merge_content_defaults(MY_PORTFOLIO_SITE_SEO, current_seo)
                ),
            },
        )
        client, client_created = get_or_create_client_for_site(site)

        created_sections = 0
        updated_sections = 0
        for seed in MY_PORTFOLIO_SECTION_SEEDS:
            schema = deepcopy(seed["schema"])
            seed_content = deepcopy(seed["content"])
            schema_key = get_my_portfolio_schema_key(seed["key"])

            SectionSchema.objects.update_or_create(
                section_key=schema_key,
                defaults={
                    "title": seed["title"],
                    "schema": schema,
                    "description": f"Поля раздела «{seed['title']}» портфолио Александра Тишечкина.",
                },
            )

            existing_section = SiteSection.objects.filter(site=site, key=seed["key"]).first()
            current_content = existing_section.content if existing_section else {}
            content = (
                seed_content
                if reset_content or not isinstance(current_content, dict)
                else merge_content_defaults(seed_content, current_content)
            )
            section, created = SiteSection.objects.update_or_create(
                site=site,
                key=seed["key"],
                defaults={
                    "title": seed["title"],
                    "section_type": seed["key"],
                    "component_key": f"my-portfolio-{seed['key']}",
                    "order": seed["order"],
                    "is_active": True,
                    "schema": schema,
                    "content": content,
                    "settings": (
                        existing_section.settings
                        if existing_section and isinstance(existing_section.settings, dict)
                        else {"source": "my-portfolio"}
                    ),
                    "seo": existing_section.seo if existing_section and isinstance(existing_section.seo, dict) else {},
                },
            )
            section.full_clean()
            if created:
                created_sections += 1
            else:
                updated_sections += 1

        self.stdout.write(self.style.SUCCESS("seed_my_portfolio_site completed."))
        self.stdout.write(f"site={site.slug} created={site_created}")
        self.stdout.write(f"owner={owner.email or owner.username}")
        self.stdout.write(f"client={client.id} created={client_created}")
        self.stdout.write(f"sections_created={created_sections} sections_updated={updated_sections}")

    def _resolve_owner(self, *, existing_site, tracknode_site, requested_email):
        user_model = get_user_model()
        email = str(requested_email or os.getenv("MY_PORTFOLIO_SITE_OWNER_EMAIL", "")).strip().lower()
        if email:
            user = user_model.objects.filter(email__iexact=email).order_by("id").first()
            if user is not None:
                return user
            self.stderr.write(f"Portfolio owner with email {email!r} was not found; using a safe fallback.")

        if existing_site and existing_site.owner_id:
            return existing_site.owner

        if tracknode_site and tracknode_site.owner_id:
            return tracknode_site.owner

        user = (
            user_model.objects.filter(is_superuser=True, is_active=True).order_by("id").first()
            or user_model.objects.filter(is_staff=True, is_active=True).order_by("id").first()
        )
        if user is not None:
            return user

        raise CommandError(
            "No owner found for my_portfolio. Create TrackNode site first, pass --owner-email, or create an admin user."
        )
