"""Host supervisor heartbeat: liveness, not generation progress."""
import json
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .jobs import job_root


def worker_health():
    required = getattr(settings, "STUDIO_WORKER_REQUIRED", False)
    result = {"required": required, "available": not required, "state": "unknown", "updated_at": None, "visual_available": not required, "visual_style_available": not required, "scope_edit_available": not required}
    try:
        path = job_root() / "worker-health.json"
        if path.stat().st_size > 8192:
            return result
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("protocol") != 1:
            return result
        stamp = parse_datetime(data.get("updated_at", ""))
        if stamp is None or timezone.is_naive(stamp):
            return result
        age = (timezone.now() - stamp).total_seconds()
        if not -5 <= age <= 15:
            return {**result, "state": "offline", "updated_at": stamp.isoformat()}
        state = data.get("state")
        if state not in ("ready", "busy", "starting", "recovering", "blocked", "offline"):
            return result
        available = not required or state in ("ready", "busy")
        features = []
        try:
            ready = job_root() / "watcher-ready.json"
            if ready.stat().st_size <= 8192:
                ack = json.loads(ready.read_text(encoding="utf-8"))
                if (isinstance(ack, dict) and ack.get("protocol") == 1
                        and isinstance(ack.get("pid"), int) and ack["pid"] == data.get("pid")
                        and isinstance(ack.get("features"), list)):
                    features = ack["features"]
        except (OSError, ValueError, TypeError):
            pass
        return {**result, "state": state, "updated_at": stamp.isoformat(), "available": available,
                "visual_available": available and (not required or "visual-text-v1" in features),
                "visual_style_available": available and (not required or "visual-style-v1" in features),
                "scope_edit_available": available and (not required or "scope-edit-v2" in features)}
    except (OSError, ValueError, TypeError, OverflowError):
        return result
