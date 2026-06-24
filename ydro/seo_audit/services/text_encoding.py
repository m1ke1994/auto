from __future__ import annotations

from typing import Any


MOJIBAKE_MARKERS = ("Ð", "Ñ", "�")
LATIN1_ALIASES = {"iso-8859-1", "latin-1", "latin1"}


def repair_mojibake(value: Any) -> str:
    text = "" if value is None else str(value)
    if any(ch in text for ch in MOJIBAKE_MARKERS):
        candidates = []
        try:
            candidates.append(text.encode("latin1").decode("utf-8"))
        except Exception:
            pass
        try:
            candidates.append(text.encode("cp1252").decode("utf-8"))
        except Exception:
            pass

        for candidate in candidates:
            if candidate and candidate != text and not any(marker in candidate for marker in MOJIBAKE_MARKERS):
                return candidate
    return text


def has_mojibake(value: Any) -> bool:
    text = "" if value is None else str(value)
    return any(ch in text for ch in MOJIBAKE_MARKERS)


def response_encoding(response: Any) -> str:
    encoding = str(getattr(response, "encoding", "") or "").strip()
    apparent = str(getattr(response, "apparent_encoding", "") or "").strip()
    if (not encoding or encoding.lower() in LATIN1_ALIASES) and apparent:
        return apparent
    return encoding or apparent or "utf-8"


def response_text(response: Any) -> str:
    encoding = response_encoding(response)
    try:
        response.encoding = encoding
    except Exception:
        pass

    try:
        return repair_mojibake(getattr(response, "text", "") or "")
    except Exception:
        content = getattr(response, "content", b"") or b""
        if isinstance(content, str):
            return repair_mojibake(content)
        try:
            return repair_mojibake(bytes(content).decode(encoding, errors="replace"))
        except Exception:
            return repair_mojibake(bytes(content).decode("utf-8", errors="replace"))
