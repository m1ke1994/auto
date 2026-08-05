# -*- coding: utf-8 -*-
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


class UnsafeURL(ValueError):
    pass


@dataclass(frozen=True)
class SafeURL:
    url: str
    hostname: str
    domain: str


def _hostname_is_blocked(hostname: str) -> bool:
    host = str(hostname or "").strip().lower().rstrip(".")
    return host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost")


def _ip_is_public(ip: str) -> bool:
    address = ipaddress.ip_address(ip)
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _resolved_ips(hostname: str) -> set[str]:
    try:
        rows = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURL("Не удалось проверить адрес сайта.") from exc
    return {row[4][0] for row in rows if row and row[4]}


def _validate_public_hostname(hostname: str) -> None:
    if not hostname or _hostname_is_blocked(hostname):
        raise UnsafeURL("Укажите публичный домен сайта.")

    try:
        if not _ip_is_public(hostname):
            raise UnsafeURL("Внутренние IP-адреса недоступны для SEO-аудита.")
        return
    except ValueError:
        pass

    ips = _resolved_ips(hostname)
    if not ips:
        raise UnsafeURL("Не удалось проверить адрес сайта.")
    for ip in ips:
        if not _ip_is_public(ip):
            raise UnsafeURL("Внутренние IP-адреса недоступны для SEO-аудита.")


def normalize_public_url(raw_url: str, *, resolve_dns: bool = True) -> SafeURL:
    raw = str(raw_url or "").strip()
    if not raw:
        raise UnsafeURL("Укажите URL сайта.")
    raw = re.sub(r"^(https?):/([^/])", r"\1://\2", raw, flags=re.IGNORECASE)
    if "://" not in raw:
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        raise UnsafeURL("Разрешены только http:// и https:// URL.")
    if parsed.username or parsed.password:
        raise UnsafeURL("URL с учетными данными недоступны для SEO-аудита.")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    try:
        hostname = hostname.encode("idna").decode("ascii") if hostname else ""
    except UnicodeError as exc:
        raise UnsafeURL("Invalid URL. Use https://example.com/ format.") from exc
    if resolve_dns:
        _validate_public_hostname(hostname)
    elif not hostname or _hostname_is_blocked(hostname):
        raise UnsafeURL("Укажите публичный домен сайта.")

    try:
        port = f":{parsed.port}" if parsed.port else ""
    except ValueError as exc:
        raise UnsafeURL("Invalid URL. Use https://example.com/ format.") from exc
    path = parsed.path or "/"
    netloc = f"{hostname}{port}"
    normalized = urlunparse((scheme, netloc, path, "", parsed.query, ""))
    domain = hostname[4:] if hostname.startswith("www.") else hostname
    return SafeURL(url=normalized, hostname=hostname, domain=domain)


def assert_public_url(raw_url: str) -> str:
    return normalize_public_url(raw_url).url
