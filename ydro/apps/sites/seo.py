import json
from html import escape
from django.conf import settings


PUBLIC_SITE_BRAND = "Leelabird"
PUBLIC_SITE_DEFAULT_TITLE = "Leelabird — трансформационная игра Лила и практики медитации"
PUBLIC_SITE_DEFAULT_DESCRIPTION = (
    "Индивидуальные сессии, трансформационная игра Лила, медитации и практики "
    "осознанного развития с Ольгой."
)
PUBLIC_SITE_DEFAULT_IMAGE = "/images/Lila_Olga_2.2.poster.jpg"

_OLD_PUBLIC_BRANDS = (
    "A" + " Meditation",
    "A" + " meditation",
    "a" + " meditation",
    "A" + "Meditation",
)


def replace_legacy_public_brand(value):
    if isinstance(value, str):
        next_value = value
        for old_brand in _OLD_PUBLIC_BRANDS:
            next_value = next_value.replace(old_brand, PUBLIC_SITE_BRAND)
        return next_value
    if isinstance(value, list):
        return [replace_legacy_public_brand(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_legacy_public_brand(item) for key, item in value.items()}
    return value


def _clean(value):
    if value is None:
        return ""
    return replace_legacy_public_brand(str(value)).strip()


def _first_text(source, keys):
    if not isinstance(source, dict):
        return ""
    for key in keys:
        value = _clean(source.get(key))
        if value:
            return value
    return ""


def _site_public_url(site):
    raw_seo = site.seo if isinstance(site.seo, dict) else {}
    explicit_url = _first_text(raw_seo, ("canonical", "canonical_url", "url", "og_url"))
    if explicit_url:
        return explicit_url.rstrip("/")

    domain = _clean(getattr(site, "domain", ""))
    if not domain:
        return settings.PUBLIC_SITE_DEFAULT_URL.rstrip("/")

    if domain.startswith(("http://", "https://")):
        return domain.rstrip("/")

    default_domain = str(getattr(settings, "PUBLIC_SITE_DEFAULT_DOMAIN", "") or "").strip()
    if default_domain and domain.lower() == default_domain.lower():
        return settings.PUBLIC_SITE_DEFAULT_URL.rstrip("/")

    scheme = "https" if getattr(settings, "IS_PRODUCTION", False) else "http"
    return f"{scheme}://{domain}".rstrip("/")


def _absolute_url(value, *, site_url):
    value = _clean(value)
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/media/"):
        return f"{settings.SITE_BASE_URL.rstrip('/')}/{value.lstrip('/')}"
    if value.startswith("/"):
        return f"{site_url.rstrip('/')}/{value.lstrip('/')}"
    return value


def _default_json_ld(*, title, description, site_name, canonical_url):
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name or PUBLIC_SITE_BRAND,
        "url": canonical_url,
        "headline": title,
        "description": description,
        "inLanguage": "ru-RU",
    }


def _json_ld_from_raw(raw_value):
    if isinstance(raw_value, (dict, list)):
        return replace_legacy_public_brand(raw_value)
    if isinstance(raw_value, str) and raw_value.strip():
        try:
            return replace_legacy_public_brand(json.loads(raw_value))
        except json.JSONDecodeError:
            return replace_legacy_public_brand(raw_value)
    return None


def build_public_site_seo(site):
    raw_seo = replace_legacy_public_brand(site.seo if isinstance(site.seo, dict) else {})
    site_url = _site_public_url(site)
    canonical_url = _absolute_url(site_url or "/", site_url=site_url).rstrip("/") + "/"

    title = _first_text(raw_seo, ("title", "seo_title")) or PUBLIC_SITE_DEFAULT_TITLE
    description = (
        _first_text(raw_seo, ("description", "meta_description", "seo_description"))
        or PUBLIC_SITE_DEFAULT_DESCRIPTION
    )
    site_name = _first_text(raw_seo, ("site_name", "og_site_name")) or _clean(site.name) or PUBLIC_SITE_BRAND

    image = _first_text(raw_seo, ("image", "image_url", "og_image", "og:image", "twitter_image"))
    image = _absolute_url(image or PUBLIC_SITE_DEFAULT_IMAGE, site_url=site_url)

    og_title = _first_text(raw_seo, ("og_title", "og:title")) or title
    og_description = _first_text(raw_seo, ("og_description", "og:description")) or description
    og_url = _absolute_url(_first_text(raw_seo, ("og_url", "og:url")) or canonical_url, site_url=site_url)
    og_type = _first_text(raw_seo, ("og_type", "og:type")) or "website"

    twitter_title = _first_text(raw_seo, ("twitter_title", "twitter:title")) or title
    twitter_description = _first_text(raw_seo, ("twitter_description", "twitter:description")) or description
    twitter_card = _first_text(raw_seo, ("twitter_card", "twitter:card")) or "summary_large_image"

    raw_json_ld = raw_seo.get("json_ld", raw_seo.get("jsonLd", raw_seo.get("schema")))
    json_ld = _json_ld_from_raw(raw_json_ld)
    if json_ld is None:
        json_ld = _default_json_ld(
            title=title,
            description=description,
            site_name=site_name,
            canonical_url=canonical_url,
        )

    return {
        "title": title,
        "description": description,
        "site_name": site_name,
        "canonical": canonical_url,
        "url": canonical_url,
        "image": image,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": image,
        "og_url": og_url,
        "og_type": og_type,
        "twitter_title": twitter_title,
        "twitter_description": twitter_description,
        "twitter_image": image,
        "twitter_card": twitter_card,
        "json_ld": json_ld,
    }


def _meta_tag(name, content):
    return f'<meta name="{escape(name, quote=True)}" content="{escape(content, quote=True)}">'


def _property_tag(property_name, content):
    return (
        f'<meta property="{escape(property_name, quote=True)}" '
        f'content="{escape(content, quote=True)}">'
    )


def render_public_site_seo_head(seo):
    json_ld_payload = json.dumps(seo["json_ld"], ensure_ascii=False, separators=(",", ":"))
    json_ld_payload = json_ld_payload.replace("</", "<\\/")

    tags = [
        f"<title>{escape(seo['title'])}</title>",
        _meta_tag("description", seo["description"]),
        f'<link rel="canonical" href="{escape(seo["canonical"], quote=True)}">',
        _property_tag("og:type", seo["og_type"]),
        _property_tag("og:site_name", seo["site_name"]),
        _property_tag("og:title", seo["og_title"]),
        _property_tag("og:description", seo["og_description"]),
        _property_tag("og:image", seo["og_image"]),
        _property_tag("og:url", seo["og_url"]),
        _meta_tag("twitter:card", seo["twitter_card"]),
        _meta_tag("twitter:title", seo["twitter_title"]),
        _meta_tag("twitter:description", seo["twitter_description"]),
        _meta_tag("twitter:image", seo["twitter_image"]),
        (
            '<script type="application/ld+json" id="public-site-json-ld">'
            f"{json_ld_payload}</script>"
        ),
    ]
    return "\n    ".join(tags)
