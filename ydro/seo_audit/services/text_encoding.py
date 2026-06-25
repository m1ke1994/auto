from __future__ import annotations

import codecs
import logging
import re
from typing import Any


logger = logging.getLogger(__name__)

MOJIBAKE_MARKERS = ("Ð", "Ñ", "Â", "�")
LATIN1_ALIASES = {"iso-8859-1", "iso8859-1", "latin-1", "latin1"}
_META_CHARSET_RE = re.compile(br"<meta\s+[^>]*charset\s*=\s*['\"]?\s*([A-Za-z0-9._-]+)", re.IGNORECASE)
_META_CONTENT_CHARSET_RE = re.compile(
    br"<meta\s+[^>]*content\s*=\s*['\"][^'\"]*charset\s*=\s*([A-Za-z0-9._-]+)",
    re.IGNORECASE,
)
_XML_ENCODING_RE = re.compile(br"<\?xml\s+[^>]*encoding\s*=\s*['\"]\s*([A-Za-z0-9._-]+)", re.IGNORECASE)
_HEADER_CHARSET_RE = re.compile(r"charset\s*=\s*['\"]?\s*([A-Za-z0-9._-]+)", re.IGNORECASE)


def _normalize_encoding(value: Any) -> str:
    candidate = str(value or "").strip().strip("\"'")
    if not candidate:
        return ""
    try:
        return codecs.lookup(candidate).name
    except LookupError:
        return candidate.lower()


def _content_bytes(response: Any) -> bytes:
    content = getattr(response, "content", b"") or b""
    if isinstance(content, bytes):
        return content
    if isinstance(content, bytearray):
        return bytes(content)
    if isinstance(content, str):
        return content.encode("utf-8", errors="replace")
    return bytes(content)


def _encoding_from_content(content: bytes) -> str:
    head = bytes(content[:4096])
    for pattern in (_XML_ENCODING_RE, _META_CHARSET_RE, _META_CONTENT_CHARSET_RE):
        match = pattern.search(head)
        if match:
            return _normalize_encoding(match.group(1).decode("ascii", errors="ignore"))
    return ""


def _encoding_from_headers(response: Any) -> str:
    content_type = str((getattr(response, "headers", {}) or {}).get("Content-Type") or "")
    match = _HEADER_CHARSET_RE.search(content_type)
    if not match:
        return ""
    return _normalize_encoding(match.group(1))


def has_mojibake(value: Any) -> bool:
    text = "" if value is None else str(value)
    return any(ch in text for ch in MOJIBAKE_MARKERS)


def _snippet(value: Any, *, limit: int = 180) -> str:
    text = "" if value is None else str(value)
    return " ".join(text.split())[:limit]


def log_text_diagnostics(diagnostics_logger: logging.Logger, stage: str, value: Any, **context: Any) -> None:
    text = "" if value is None else str(value)
    suspicious = has_mojibake(text)
    diagnostics_logger.debug(
        "%s mojibake=%s sample=%r context=%s",
        stage,
        suspicious,
        _snippet(text),
        context,
    )


def log_response_diagnostics(
    diagnostics_logger: logging.Logger,
    stage: str,
    response: Any,
    *,
    chosen_encoding: str,
    decoded_text: str,
    raw_text: str = "",
    original_encoding: str = "",
) -> None:
    content = _content_bytes(response)
    diagnostics_logger.debug(
        "%s url=%s status=%s content_type=%r content_bytes=%s response_encoding=%r "
        "apparent_encoding=%r chosen_encoding=%r raw_text_mojibake=%s decoded_mojibake=%s "
        "decoded_sample=%r",
        stage,
        getattr(response, "url", ""),
        getattr(response, "status_code", ""),
        (getattr(response, "headers", {}) or {}).get("Content-Type"),
        len(content),
        original_encoding,
        getattr(response, "apparent_encoding", ""),
        chosen_encoding,
        has_mojibake(raw_text),
        has_mojibake(decoded_text),
        _snippet(decoded_text),
    )


def response_encoding(response: Any) -> str:
    encoding = _normalize_encoding(getattr(response, "encoding", "")) or _encoding_from_headers(response)
    apparent = _normalize_encoding(getattr(response, "apparent_encoding", ""))
    declared = _encoding_from_content(_content_bytes(response))

    if encoding and encoding.lower() not in LATIN1_ALIASES:
        return encoding
    if declared:
        return declared
    if apparent:
        return apparent
    return encoding or "utf-8"


def response_text(response: Any, *, diagnostics_logger: logging.Logger | None = None, stage: str = "response_text") -> str:
    original_encoding = str(getattr(response, "encoding", "") or "").strip()
    try:
        raw_text = str(getattr(response, "text", "") or "")
    except Exception:
        raw_text = ""

    encoding = response_encoding(response)
    try:
        response.encoding = encoding
    except Exception:
        pass

    content = _content_bytes(response)
    try:
        decoded = content.decode(encoding, errors="replace")
    except Exception:
        decoded = content.decode("utf-8", errors="replace")

    log_response_diagnostics(
        diagnostics_logger or logger,
        stage,
        response,
        chosen_encoding=encoding,
        decoded_text=decoded,
        raw_text=raw_text,
        original_encoding=original_encoding,
    )
    return decoded
