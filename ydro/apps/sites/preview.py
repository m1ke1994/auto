from django.core import signing


PREVIEW_TOKEN_SALT = "tracknode.site-preview.v1"
PREVIEW_TOKEN_MAX_AGE = 60 * 60 * 24


def build_site_preview_token(site) -> str:
    return signing.dumps(
        {"site_id": site.id, "public_id": str(site.public_id), "owner_id": site.owner_id},
        salt=PREVIEW_TOKEN_SALT,
        compress=True,
    )


def validate_site_preview_token(site, token: str) -> bool:
    if not token:
        return False
    try:
        payload = signing.loads(token, salt=PREVIEW_TOKEN_SALT, max_age=PREVIEW_TOKEN_MAX_AGE)
    except signing.BadSignature:
        return False
    return (
        payload.get("site_id") == site.id
        and payload.get("public_id") == str(site.public_id)
        and payload.get("owner_id") == site.owner_id
    )


def build_site_preview_url(site) -> str:
    token = build_site_preview_token(site)
    return f"/api/public/sites/{site.slug}/html/?preview=1&token={token}"


def site_requires_preview_token(site) -> bool:
    return site.source == site.Source.TEMPLATE and site.status == site.Status.DRAFT
