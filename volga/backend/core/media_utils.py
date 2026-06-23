from django.conf import settings


FALLBACK_HERO_IMAGE = "pages/hero/placeholder.jpg"
FALLBACK_GALLERY_IMAGE = "pages/gallery/placeholder-1.jpg"
FALLBACK_AVATAR_IMAGE = "pages/gallery/placeholder-2.jpg"


def _absolute_url(url: str, request):
    if request is None:
        return url
    return request.build_absolute_uri(url)


def media_url_or_fallback(media_field, request=None, fallback_path: str | None = None):
    if media_field and getattr(media_field, "name", ""):
        try:
            if media_field.storage.exists(media_field.name):
                return _absolute_url(media_field.url, request)
        except Exception:
            pass

    if not fallback_path:
        return None

    media_base = settings.MEDIA_URL.rstrip("/")
    fallback = f"{media_base}/{fallback_path.lstrip('/')}"
    return _absolute_url(fallback, request)
