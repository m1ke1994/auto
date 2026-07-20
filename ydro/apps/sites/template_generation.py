from copy import deepcopy
import secrets

from django.db import transaction

from .models import Site, SiteSection, WebsiteTemplate, WebsiteTemplateCategory, WebsiteTemplateCloneRequest
from .preview import build_site_preview_url
from .website_templates import (
    WebsiteTemplateCloneError,
    clone_site_for_user,
    normalize_template_snapshot,
    validate_template_snapshot,
)


SUPPORTED_BUILDER_TEMPLATE_KEYS = {
    "business-landing",
    "services-landing",
    "tourism-landing",
    "saas-digital-service",
    "expert-practice-consulting",
    "country-retreat-events",
    "art-troy",
    "a-meditation",
}

COMPANY_DATA_KEYS = {
    "company_name": ("company_name", "company", "name", "site_name", "brand_name", "title"),
    "description": ("description", "subtitle", "lead", "intro", "about"),
    "phone": ("phone", "phone_number", "tel", "contact_phone"),
    "email": ("email", "mail", "contact_email"),
    "city": ("city", "location"),
}


def build_generation_response(site: Site, template: WebsiteTemplate) -> dict:
    return {
        "site": {
            "id": site.id,
            "public_id": str(site.public_id),
            "name": site.name,
            "status": site.status,
            "builder_template_key": site.builder_template_key,
        },
        "selected_template": {
            "id": template.id,
            "name": template.name,
            "category_id": template.category_id,
        },
        "preview_url": build_site_preview_url(site),
        "editor_url": f"/sites/{site.id}/sections",
    }


def select_random_template(*, category: WebsiteTemplateCategory, exclude_template_ids=None) -> WebsiteTemplate:
    exclude_template_ids = {int(value) for value in (exclude_template_ids or []) if str(value).isdigit()}
    queryset = WebsiteTemplate.objects.filter(
        category=category,
        category__is_active=True,
        is_active=True,
        is_published=True,
    ).exclude(id__in=exclude_template_ids)
    ids = list(queryset.values_list("id", flat=True))
    if not ids:
        raise WebsiteTemplateCloneError(
            "category_has_no_templates",
            "Для выбранной категории пока нет доступных дизайнов.",
        )
    secrets.SystemRandom().shuffle(ids)
    for template_id in ids:
        template = WebsiteTemplate.objects.select_related("category", "source_site").get(id=template_id)
        snapshot = normalize_template_snapshot(template, template.snapshot_config if isinstance(template.snapshot_config, dict) else {})
        try:
            validate_template_snapshot(snapshot)
        except WebsiteTemplateCloneError:
            continue
        site_config = snapshot.get("site", {})
        builder_key = site_config.get("builder_template_key", "")
        builder_config = site_config.get("builder_config", {})
        if (
            builder_key
            and isinstance(builder_config, dict)
            and builder_config
            and (not SUPPORTED_BUILDER_TEMPLATE_KEYS or builder_key in SUPPORTED_BUILDER_TEMPLATE_KEYS)
        ):
            return template
    raise WebsiteTemplateCloneError(
        "category_has_no_templates",
        "Для выбранной категории пока нет доступных дизайнов.",
    )


def generate_site_from_category(*, user, category_id, company_data, idempotency_key) -> tuple[Site, WebsiteTemplate]:
    key = str(idempotency_key or "").strip()
    if key:
        existing = WebsiteTemplateCloneRequest.objects.filter(user=user, idempotency_key=key).select_related(
            "site",
            "template",
            "template__category",
        ).first()
        if existing is not None:
            return existing.site, existing.template

    category = WebsiteTemplateCategory.objects.filter(id=category_id, is_active=True).first()
    if category is None:
        raise WebsiteTemplateCloneError("category_not_found", "Категория не найдена.")

    template = select_random_template(category=category)
    site = clone_site_for_user(
        template=template,
        target_user=user,
        company_name=company_data.get("company_name", ""),
        site_name=company_data.get("company_name", ""),
        idempotency_key=key,
    )
    apply_company_data(site, company_data)
    return site, template


def regenerate_site_design(*, site: Site, exclude_template_ids, idempotency_key) -> tuple[Site, WebsiteTemplate]:
    if site.status != Site.Status.DRAFT:
        raise WebsiteTemplateCloneError("site_not_draft", "Менять дизайн можно только для черновика.")

    existing_request = WebsiteTemplateCloneRequest.objects.filter(site=site).select_related("template", "template__category").first()
    if existing_request is None:
        raise WebsiteTemplateCloneError("source_template_not_found", "Не удалось определить категорию текущего дизайна.")

    excluded = set(exclude_template_ids or [])
    excluded.add(existing_request.template_id)
    try:
        template = select_random_template(category=existing_request.template.category, exclude_template_ids=excluded)
    except WebsiteTemplateCloneError as exc:
        if exc.code == "category_has_no_templates":
            raise WebsiteTemplateCloneError("no_alternative_templates", "В этой категории пока нет другого доступного дизайна.") from exc
        raise

    company_data = extract_company_data(site)
    snapshot = normalize_template_snapshot(template, template.snapshot_config if isinstance(template.snapshot_config, dict) else {})
    validate_template_snapshot(snapshot)

    with transaction.atomic():
        site.builder_template_key = snapshot["site"]["builder_template_key"]
        site.builder_config = deepcopy(snapshot["site"]["builder_config"])
        site.design_preset = snapshot["site"]["design_preset"]
        site.generation_status = Site.GenerationStatus.COMPLETED
        site.generation_progress = 100
        site.generation_error = ""
        site.save(
            update_fields=[
                "builder_template_key",
                "builder_config",
                "design_preset",
                "generation_status",
                "generation_progress",
                "generation_error",
                "updated_at",
            ]
        )
        sync_sections_from_snapshot(site=site, snapshot=snapshot)
        existing_request.template = template
        existing_request.idempotency_key = str(idempotency_key or existing_request.idempotency_key or "")
        existing_request.save(update_fields=["template", "idempotency_key"])

    apply_company_data(site, company_data)
    return site, template


def extract_company_data(site: Site) -> dict:
    data = {}
    _extract_known_values(site.builder_config, data)
    for section in site.sections.filter(is_active=True).order_by("order"):
        _extract_known_values(section.content, data)
        _extract_known_values(section.settings, data)
    data.setdefault("company_name", site.name)
    return data


def apply_company_data(site: Site, company_data: dict) -> None:
    normalized = {key: str(value or "").strip() for key, value in (company_data or {}).items()}
    with transaction.atomic():
        config = deepcopy(site.builder_config if isinstance(site.builder_config, dict) else {})
        site.builder_config = _apply_known_values(config, normalized)
        if normalized.get("company_name"):
            site.name = normalized["company_name"][:255]
        site.save(update_fields=["name", "builder_config", "updated_at"])
        for section in site.sections.filter(is_active=True):
            changed = False
            content = _apply_known_values(deepcopy(section.content or {}), normalized)
            settings = _apply_known_values(deepcopy(section.settings or {}), normalized)
            if content != section.content:
                section.content = content
                changed = True
            if settings != section.settings:
                section.settings = settings
                changed = True
            if changed:
                section.save(update_fields=["content", "settings", "updated_at"])


def sync_sections_from_snapshot(*, site: Site, snapshot: dict) -> None:
    existing = {section.key: section for section in site.sections.all()}
    active_keys = set()
    for index, section_data in enumerate(snapshot.get("sections", []), start=1):
        key = str(section_data.get("key") or f"section-{index}")[:100]
        active_keys.add(key)
        section = existing.get(key) or SiteSection(site=site, key=key)
        section.title = str(section_data.get("title") or key)
        section.section_type = str(section_data.get("section_type") or key)
        section.order = int(section_data.get("order") or index)
        section.is_active = bool(section_data.get("is_active", True))
        section.schema = deepcopy(section_data.get("schema") or {})
        section.content = deepcopy(section_data.get("content") or {})
        section.component_key = str(section_data.get("component_key") or "")
        section.settings = deepcopy(section_data.get("settings") or {})
        section.seo = deepcopy(section_data.get("seo") or {})
        section.save()
    site.sections.exclude(key__in=active_keys).update(is_active=False)


def _apply_known_values(value, company_data):
    if isinstance(value, list):
        return [_apply_known_values(item, company_data) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            replacement = _company_value_for_key(key, company_data)
            result[key] = replacement if replacement else _apply_known_values(item, company_data)
        return result
    return value


def _extract_known_values(value, data):
    if isinstance(value, list):
        for item in value:
            _extract_known_values(item, data)
    if isinstance(value, dict):
        for key, item in value.items():
            canonical = _canonical_company_key(key)
            if canonical and isinstance(item, str) and item.strip():
                data.setdefault(canonical, item.strip())
            _extract_known_values(item, data)


def _canonical_company_key(key):
    normalized = str(key or "").strip().lower().replace("-", "_")
    for canonical, aliases in COMPANY_DATA_KEYS.items():
        if normalized in aliases:
            return canonical
    return ""


def _company_value_for_key(key, company_data):
    canonical = _canonical_company_key(key)
    if not canonical:
        return ""
    return company_data.get(canonical, "")
