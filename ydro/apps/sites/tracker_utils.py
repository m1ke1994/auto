from urllib.parse import urlparse

from django.conf import settings
from django.utils.html import escape


LOCAL_TRACKING_HOSTS = {"localhost", "127.0.0.1", "::1", "testserver"}


def mask_tracker_token(token: str) -> str:
    raw = str(token or "").strip()
    if len(raw) < 10:
        return "***"
    return f"{raw[:6]}***{raw[-4:]}"


def normalize_tracking_host(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    host = parsed.hostname or raw.split("/", 1)[0].split(":", 1)[0]
    host = host.strip("[]").rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def request_tracking_origin_host(request) -> str:
    origin = request.headers.get("Origin") or request.META.get("HTTP_ORIGIN") or ""
    referer = request.headers.get("Referer") or request.META.get("HTTP_REFERER") or ""
    return normalize_tracking_host(origin) or normalize_tracking_host(referer)


def is_local_tracking_host(host: str) -> bool:
    normalized = normalize_tracking_host(host)
    return normalized in LOCAL_TRACKING_HOSTS or normalized.endswith(".localhost")


def site_allows_tracking_origin(site, request) -> bool:
    request_host = request_tracking_origin_host(request)
    site_host = normalize_tracking_host(getattr(site, "domain", ""))
    if not request_host or not site_host:
        return True
    if is_local_tracking_host(request_host) or is_local_tracking_host(site_host):
        return True
    return request_host == site_host


def tracker_script_url() -> str:
    base_url = getattr(settings, "PUBLIC_BASE_URL", "").rstrip("/")
    return f"{base_url}/tracker.js"


def build_tracker_script_tag(api_key: str) -> str:
    return f'<script src="{escape(tracker_script_url())}" data-site-key="{escape(api_key)}"></script>'
