"""Host supervisor heartbeat: liveness, not generation progress."""
import json
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .jobs import job_root


def worker_health():
    required = getattr(settings, "STUDIO_WORKER_REQUIRED", False)
    result = {"required": required, "available": not required, "state": "unknown", "updated_at": None}
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
        return {**result, "state": state, "updated_at": stamp.isoformat(),
                "available": not required or state in ("ready", "busy")}
    except (OSError, ValueError, TypeError, OverflowError):
        return result
