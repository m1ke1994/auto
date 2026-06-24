from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class DomainValidationError(ValueError):
    pass


LOCAL_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "0.0.0.0",
}
INTERNAL_TLDS = {"local", "localhost", "internal", "lan", "home", "corp", "test"}


def _to_ascii_hostname(hostname: str) -> str:
    host = str(hostname or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host:
        raise DomainValidationError("Укажите домен.")
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise DomainValidationError("Некорректный домен.") from exc


def _validate_hostname_shape(hostname: str) -> None:
    if len(hostname) > 253:
        raise DomainValidationError("Домен слишком длинный.")

    labels = hostname.split(".")
    if len(labels) < 2:
        raise DomainValidationError("Внутренние адреса запрещены.")

    if labels[-1] in INTERNAL_TLDS:
        raise DomainValidationError("Внутренние адреса запрещены.")

    for label in labels:
        if not label or len(label) > 63:
            raise DomainValidationError("Некорректный домен.")
        if label.startswith("-") or label.endswith("-"):
            raise DomainValidationError("Некорректный домен.")
        if not all(ch.isalnum() or ch == "-" for ch in label):
            raise DomainValidationError("Некорректный домен.")


def _validate_ip_address(hostname: str) -> None:
    try:
        ip = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        return

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise DomainValidationError("Внутренние и private IP запрещены.")


def _resolve_public_ips(hostname: str) -> None:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise DomainValidationError("Домен не удалось разрешить через DNS.") from exc

    if not records:
        raise DomainValidationError("Домен не удалось разрешить через DNS.")

    for record in records:
        ip = record[4][0]
        _validate_ip_address(ip)


def normalize_public_domain(value: str, *, resolve_dns: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise DomainValidationError("Укажите домен.")

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    scheme = (parsed.scheme or "").lower()
    if scheme and scheme not in {"http", "https"}:
        raise DomainValidationError("Разрешены только HTTP(S)-домены.")

    hostname = _to_ascii_hostname(parsed.hostname or "")
    if hostname in LOCAL_HOSTNAMES or hostname.endswith(".localhost"):
        raise DomainValidationError("localhost запрещён.")

    _validate_ip_address(hostname)
    _validate_hostname_shape(hostname)

    if resolve_dns:
        _resolve_public_ips(hostname)

    return hostname


def normalize_competitor_domains(values, *, max_count: int = 3) -> list[str]:
    if values is None:
        values = []
    if not isinstance(values, list):
        raise DomainValidationError("Список конкурентов должен быть массивом.")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        raw = str(item or "").strip()
        if not raw:
            continue
        domain = normalize_public_domain(raw, resolve_dns=False)
        if domain in seen:
            continue
        seen.add(domain)
        normalized.append(domain)

    if len(normalized) > max_count:
        raise DomainValidationError(f"Можно указать максимум {max_count} домена конкурентов.")
    if not normalized:
        raise DomainValidationError("Укажите хотя бы один домен конкурента.")

    return normalized


def validate_public_analysis_domain(domain: str) -> str:
    return normalize_public_domain(domain, resolve_dns=True)
