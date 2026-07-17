from copy import deepcopy
import logging
import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from .models import Site, SiteSection, WebsiteTemplate, WebsiteTemplateCloneRequest

logger = logging.getLogger(__name__)


class WebsiteTemplateCloneError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


SENSITIVE_TEXT_KEYS = {
    "address",
    "api_key",
    "chat_id",
    "contact",
    "contacts",
    "email",
    "map",
    "phone",
    "telegram",
    "token",
    "whatsapp",
}


def normalize_template_snapshot(template: WebsiteTemplate, snapshot: dict) -> dict:
    normalized = deepcopy(snapshot) if isinstance(snapshot, dict) else {}
    site_config = normalized.get("site") if isinstance(normalized.get("site"), dict) else {}

    preset = site_config.get("design_preset") or normalized.get("design_preset")
    allowed_presets = {value for value, _label in Site.DesignPreset.choices}
    if preset not in allowed_presets:
        source_preset = getattr(template.source_site, "design_preset", "")
        preset = source_preset if source_preset in allowed_presets else Site.DesignPreset.CLEAN_BUSINESS

    builder_config = site_config.get("builder_config", normalized.get("builder_config", {}))
    if not isinstance(builder_config, dict):
        builder_config = {}
    builder_template_key = site_config.get("builder_template_key", normalized.get("builder_template_key", ""))

    normalized["site"] = {
        **site_config,
        "design_preset": preset,
        "builder_config": deepcopy(builder_config),
        "builder_template_key": str(builder_template_key or "")[:120],
    }
    normalized.setdefault("pages", [])
    return normalized


def build_template_site_fields(
    *,
    template: WebsiteTemplate,
    target_user,
    name: str,
    company_name: str,
    slug: str,
    snapshot: dict,
) -> dict:
    site_config = snapshot["site"]
    snapshot_source = snapshot.get("source") if isinstance(snapshot.get("source"), dict) else {}
    source_name = str(snapshot_source.get("site_name") or template.source_site.name or "").strip()
    return {
        "owner": target_user,
        "name": name,
        "slug": slug,
        "domain": "",
        "source": Site.Source.TEMPLATE,
        "render_mode": Site.RenderMode.BUILDER,
        "status": Site.Status.DRAFT,
        "generation_status": Site.GenerationStatus.COMPLETED,
        "generation_progress": 100,
        "generation_error": "",
        "design_preset": site_config["design_preset"],
        "generation_job_id": None,
        "generation_started_at": None,
        "generation_completed_at": None,
        "public_id": uuid.uuid4(),
        "builder_template_key": site_config["builder_template_key"],
        "builder_config": deepcopy(site_config["builder_config"]),
        "is_active": False,
        "send_to_telegram": False,
        "telegram_chat_id": None,
        "telegram_connected_at": None,
        "seo": _replace_company_name(_snapshot_site_seo(snapshot), source_name, company_name or name),
    }


def validate_required_site_fields(site: Site) -> None:
    missing = []
    for field in Site._meta.concrete_fields:
        if field.primary_key or field.auto_created or getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False) or field.null:
            continue
        if getattr(site, field.attname, None) is None:
            missing.append(field.name)
    if missing:
        logger.error("Template clone has missing required Site fields: %s", ", ".join(missing))
        raise WebsiteTemplateCloneError("template_clone_invalid", "Template site configuration is invalid.")


def unique_site_slug(base_value: str) -> str:
    base_slug = slugify(base_value)[:80] or "site"
    slug = base_slug
    suffix = 2
    while Site.objects.filter(slug=slug).exists():
        suffix_text = f"-{suffix}"
        slug = f"{base_slug[: 100 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return slug


def build_site_snapshot(source_site: Site) -> dict:
    sections = []
    for section in SiteSection.objects.filter(site=source_site).order_by("order", "title", "id"):
        sections.append(
            {
                "title": section.title,
                "key": section.key,
                "section_type": section.section_type,
                "order": section.order,
                "is_active": section.is_active,
                "schema": deepcopy(section.schema),
                "content": _sanitize_snapshot_value(deepcopy(section.content)),
                "component_key": section.component_key,
                "settings": deepcopy(section.settings),
                "seo": _sanitize_seo(section.seo),
            }
        )

    return {
        "version": 1,
        "source": {
            "site_id": source_site.id,
            "site_slug": source_site.slug,
            "site_name": source_site.name,
        },
        "site": {
            "seo": _sanitize_seo(source_site.seo),
            "design_preset": source_site.design_preset or Site.DesignPreset.CLEAN_BUSINESS,
            "builder_template_key": source_site.builder_template_key,
            "builder_config": deepcopy(source_site.builder_config),
            "site_settings": {},
            "theme": {},
            "design": {},
            "navigation": _extract_section_payload(sections, "navigation"),
            "header": _extract_section_payload(sections, "header"),
            "footer": _extract_section_payload(sections, "footer"),
            "menu": _extract_section_payload(sections, "navigation"),
        },
        "pages": [],
        "sections": sections,
    }


def refresh_template_snapshot(template: WebsiteTemplate) -> WebsiteTemplate:
    template.snapshot_config = build_site_snapshot(template.source_site)
    template.save(update_fields=["snapshot_config", "updated_at"])
    return template


def clone_site_for_user(
    *,
    template: WebsiteTemplate,
    target_user,
    company_name: str,
    site_name: str = "",
    idempotency_key: str = "",
) -> Site:
    try:
        key = str(idempotency_key or "").strip()
        if key:
            existing = WebsiteTemplateCloneRequest.objects.filter(user=target_user, idempotency_key=key).select_related("site").first()
            if existing is not None:
                return existing.site

        snapshot = template.snapshot_config if isinstance(template.snapshot_config, dict) else {}
        _validate_snapshot(snapshot)
        snapshot = normalize_template_snapshot(template, snapshot)
        snapshot_source = snapshot.get("source") if isinstance(snapshot.get("source"), dict) else {}
        source_name = str(snapshot_source.get("site_name") or template.source_site.name or "").strip()
        company = str(company_name or "").strip()
        name = str(site_name or "").strip() or company or template.name
        slug = unique_site_slug(name)

        with transaction.atomic():
            site_fields = build_template_site_fields(
                template=template,
                target_user=target_user,
                name=name,
                company_name=company,
                slug=slug,
                snapshot=snapshot,
            )
            site = Site(**site_fields)
            validate_required_site_fields(site)
            site.full_clean()
            site.save(force_insert=True)

            for index, section_data in enumerate(_snapshot_sections(snapshot), start=1):
                content = _replace_company_name(deepcopy(section_data.get("content") or {}), source_name, company or name)
                section = SiteSection(
                    site=site,
                    title=str(section_data.get("title") or section_data.get("key") or f"Section {index}"),
                    key=_section_key(section_data, index),
                    section_type=str(section_data.get("section_type") or ""),
                    order=_safe_int(section_data.get("order"), index),
                    is_active=bool(section_data.get("is_active", True)),
                    schema=deepcopy(section_data.get("schema") or {}),
                    content=content,
                    component_key=str(section_data.get("component_key") or ""),
                    settings=deepcopy(section_data.get("settings") or {}),
                    seo=_replace_company_name(deepcopy(section_data.get("seo") or {}), source_name, company or name),
                )
                try:
                    SiteSection.objects.bulk_create([section])
                except Exception as exc:
                    raise WebsiteTemplateCloneError(
                        "section_clone_failed",
                        f"Section clone failed for '{section.key or section.title}': {_safe_exception_text(exc)}",
                    ) from exc

            if key:
                try:
                    with transaction.atomic():
                        WebsiteTemplateCloneRequest.objects.create(
                            user=target_user,
                            template=template,
                            idempotency_key=key,
                            site=site,
                        )
                except IntegrityError:
                    existing = WebsiteTemplateCloneRequest.objects.select_related("site").filter(
                        user=target_user,
                        idempotency_key=key,
                    ).first()
                    if existing is not None:
                        raise WebsiteTemplateCloneError(
                            "idempotency_conflict",
                            "Такой запрос уже был обработан. Повторите загрузку созданного сайта.",
                        )
                    raise

        return site
    except WebsiteTemplateCloneError:
        raise
    except Exception as exc:
        logger.exception("Unexpected website template clone failure template_id=%s user_id=%s", template.id, target_user.id)
        raise WebsiteTemplateCloneError(
            "template_clone_failed",
            "Не удалось создать сайт из шаблона. Проверьте снимок шаблона и повторите попытку.",
        ) from exc


def _validate_snapshot(snapshot: dict) -> None:
    if not snapshot:
        raise WebsiteTemplateCloneError("template_snapshot_missing", "Template snapshot missing.")
    if not isinstance(snapshot, dict):
        raise WebsiteTemplateCloneError("template_snapshot_invalid", "Template snapshot invalid.")
    if not isinstance(snapshot.get("sections"), list) or not snapshot["sections"]:
        raise WebsiteTemplateCloneError("template_snapshot_missing", "Template snapshot has no sections.")
    for index, section in enumerate(snapshot["sections"], start=1):
        if not isinstance(section, dict):
            raise WebsiteTemplateCloneError("template_snapshot_invalid", f"Section #{index} is invalid.")


def _snapshot_sections(snapshot: dict) -> list:
    sections = snapshot.get("sections", [])
    return sections if isinstance(sections, list) else []


def _extract_section_payload(sections: list, key: str) -> dict:
    for section in sections:
        if section.get("key") == key:
            return deepcopy(section.get("content") or {})
    return {}


def _section_key(section_data: dict, index: int) -> str:
    raw_key = str(section_data.get("key") or section_data.get("section_type") or f"section-{index}")
    return slugify(raw_key)[:100] or f"section-{index}"


def _safe_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _safe_exception_text(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return "no details"
    return text[:500]




def _snapshot_site_seo(snapshot: dict) -> dict:
    site_config = snapshot.get("site") if isinstance(snapshot.get("site"), dict) else {}
    seo = site_config.get("seo") if isinstance(site_config.get("seo"), dict) else {}
    return deepcopy(seo)


def _sanitize_seo(value) -> dict:
    seo = deepcopy(value) if isinstance(value, dict) else {}
    for key in ("canonical", "canonical_url", "url", "og_url", "og:url"):
        seo.pop(key, None)
    return _sanitize_snapshot_value(seo)


def _sanitize_snapshot_value(value, parent_key: str = ""):
    key = str(parent_key or "").lower()
    if any(marker in key for marker in SENSITIVE_TEXT_KEYS):
        if isinstance(value, list):
            return []
        if isinstance(value, dict):
            return {}
        return ""
    if isinstance(value, list):
        return [_sanitize_snapshot_value(item, parent_key=parent_key) for item in value]
    if isinstance(value, dict):
        return {item_key: _sanitize_snapshot_value(item, parent_key=item_key) for item_key, item in value.items()}
    return value


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
