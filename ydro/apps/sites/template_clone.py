from copy import deepcopy

from django.db import IntegrityError, transaction
from django.utils.text import slugify

from .models import Site, SiteSection, SiteTemplate, SiteTemplateCloneRequest


COPY_SITE_FIELDS = ("seo",)
SKIP_SITE_FIELDS = (
    "id",
    "pk",
    "owner",
    "domain",
    "api_key",
    "telegram_chat_id",
    "send_to_telegram",
    "telegram_connected_at",
    "created_at",
    "updated_at",
)
COPY_SECTION_FIELDS = (
    "title",
    "key",
    "section_type",
    "order",
    "is_active",
    "schema",
    "content",
    "component_key",
    "settings",
    "seo",
)


def unique_site_slug(base_value: str) -> str:
    base_slug = slugify(base_value)[:80] or "site"
    slug = base_slug
    suffix = 2
    while Site.objects.filter(slug=slug).exists():
        suffix_text = f"-{suffix}"
        slug = f"{base_slug[: 100 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return slug


def clone_site_for_user(*, template: SiteTemplate, target_user, company_name: str, idempotency_key: str = "") -> Site:
    key = str(idempotency_key or "").strip()
    if key:
        existing = SiteTemplateCloneRequest.objects.filter(user=target_user, idempotency_key=key).select_related("site").first()
        if existing is not None:
            return existing.site

    source_site = template.source_site
    name = str(company_name or "").strip() or template.name or source_site.name
    slug = unique_site_slug(name)

    with transaction.atomic():
        site = Site.objects.create(
            owner=target_user,
            name=name,
            slug=slug,
            domain="",
            is_active=False,
            seo=_clone_seo(source_site.seo, name),
        )

        sections = [
            SiteSection(
                site=site,
                title=section.title,
                key=section.key,
                section_type=section.section_type,
                order=section.order,
                is_active=section.is_active,
                schema=deepcopy(section.schema),
                content=_replace_company_name(deepcopy(section.content), source_site.name, name),
                component_key=section.component_key,
                settings=deepcopy(section.settings),
                seo=_replace_company_name(deepcopy(section.seo), source_site.name, name),
            )
            for section in SiteSection.objects.filter(site=source_site).order_by("order", "title", "id")
        ]
        SiteSection.objects.bulk_create(sections)

        if key:
            try:
                SiteTemplateCloneRequest.objects.create(user=target_user, template=template, idempotency_key=key, site=site)
            except IntegrityError:
                site.delete()
                return SiteTemplateCloneRequest.objects.select_related("site").get(
                    user=target_user,
                    idempotency_key=key,
                ).site

    return site


def _clone_seo(source_seo, company_name: str) -> dict:
    seo = deepcopy(source_seo) if isinstance(source_seo, dict) else {}
    for key in ("title", "og_title", "site_name"):
        if key in seo:
            seo[key] = company_name
    return seo


def _replace_company_name(value, source_name: str, target_name: str):
    if not source_name or not target_name:
        return value
    if isinstance(value, str):
        return value.replace(source_name, target_name)
    if isinstance(value, list):
        return [_replace_company_name(item, source_name, target_name) for item in value]
    if isinstance(value, dict):
        return {key: _replace_company_name(item, source_name, target_name) for key, item in value.items()}
    return value

