from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings

from competitor_analysis.security import DomainValidationError, validate_public_analysis_domain

REQUEST_TIMEOUT_SECONDS = 8
MAX_REDIRECTS = 5


def _normalized_host(hostname: str) -> str:
    host = str(hostname or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _extract_text(value) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _meta_content(soup: BeautifulSoup | None, name: str) -> str:
    if not soup:
        return ""
    target = str(name or "").strip().lower()
    tag = soup.find("meta", attrs={"name": lambda v: str(v or "").strip().lower() == target})
    return _extract_text(tag.get("content")) if tag else ""


def _canonical_url(soup: BeautifulSoup | None, page_url: str) -> str:
    if not soup:
        return ""
    tag = soup.find(
        "link",
        attrs={"rel": lambda v: "canonical" in [str(item).lower() for item in (v if isinstance(v, list) else [v])]},
    )
    if not tag:
        return ""
    href = _extract_text(tag.get("href"))
    if not href:
        return ""
    absolute = urljoin(page_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return href
    return absolute


def _has_open_graph(soup: BeautifulSoup | None) -> bool:
    if not soup:
        return False
    return bool(soup.find("meta", attrs={"property": lambda v: str(v or "").lower().startswith("og:")}))


def _safe_get(session: requests.Session, initial_url: str) -> requests.Response:
    current_url = initial_url
    for _ in range(MAX_REDIRECTS + 1):
        parsed = urlparse(current_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise DomainValidationError("Редирект ведёт на недопустимый URL.")

        validate_public_analysis_domain(parsed.hostname)
        response = session.get(current_url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=False)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return response

        location = response.headers.get("Location")
        if not location:
            return response
        current_url = urljoin(current_url, location)

    raise DomainValidationError("Слишком много редиректов.")


def _count_links(soup: BeautifulSoup | None, *, page_url: str, root_host: str) -> tuple[int, int]:
    if not soup:
        return 0, 0

    internal = 0
    external = 0
    root = _normalized_host(root_host)
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        if href.lower().startswith(("javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if _normalized_host(parsed.hostname) == root:
            internal += 1
        else:
            external += 1
    return internal, external


def collect_domain_snapshot(domain: str) -> dict[str, Any]:
    safe_domain = validate_public_analysis_domain(domain)
    session = requests.Session()
    session.headers.setdefault("User-Agent", getattr(settings, "SEO_AUDIT_USER_AGENT", "Yadro SEO Audit/1.0"))

    last_error = ""
    response = None
    for scheme in ("https", "http"):
        try:
            response = _safe_get(session, f"{scheme}://{safe_domain}/")
            break
        except Exception as exc:
            last_error = str(exc)
            response = None

    if response is None:
        return {
            "domain": safe_domain,
            "status_code": 0,
            "https": False,
            "title": "",
            "description": "",
            "h1": "",
            "h2_count": 0,
            "canonical": "",
            "lang": "",
            "viewport": "",
            "open_graph": False,
            "internal_links_count": 0,
            "external_links_count": 0,
            "html_size_bytes": 0,
            "error": last_error or "Сайт недоступен.",
        }

    final_url = str(response.url or f"https://{safe_domain}/")
    content = getattr(response, "content", b"") or b""
    html_size = len(content) if isinstance(content, (bytes, bytearray)) else len(str(content).encode("utf-8"))
    text = response.text or ""
    soup = BeautifulSoup(text, "lxml") if text else None
    title = _extract_text(soup.title.get_text(" ", strip=True)) if soup and soup.title else ""
    h1_tags = soup.find_all("h1") if soup else []
    h2_tags = soup.find_all("h2") if soup else []
    html_tag = soup.find("html") if soup else None
    internal_links, external_links = _count_links(soup, page_url=final_url, root_host=safe_domain)

    return {
        "domain": safe_domain,
        "status_code": int(getattr(response, "status_code", 0) or 0),
        "final_url": final_url,
        "https": urlparse(final_url).scheme == "https",
        "title": title,
        "description": _meta_content(soup, "description"),
        "h1": _extract_text(h1_tags[0].get_text(" ", strip=True)) if h1_tags else "",
        "h1_count": len(h1_tags),
        "h2_count": len(h2_tags),
        "canonical": _canonical_url(soup, final_url),
        "lang": _extract_text(html_tag.get("lang")) if html_tag else "",
        "viewport": _meta_content(soup, "viewport"),
        "open_graph": _has_open_graph(soup),
        "internal_links_count": internal_links,
        "external_links_count": external_links,
        "html_size_bytes": html_size,
        "error": "",
    }
