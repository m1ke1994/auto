from calendar import monthrange
from datetime import datetime, time, timedelta

from django.utils import timezone

from platform_admin.models import PlatformAuditLog


def period_bounds(request):
    now = timezone.localtime()
    preset = request.query_params.get("period", "30d")
    today = now.date()
    if preset == "today": start = end = today
    elif preset == "yesterday": start = end = today - timedelta(days=1)
    elif preset == "7d": start, end = today - timedelta(days=6), today
    elif preset == "month": start, end = today.replace(day=1), today
    elif preset == "previous_month":
        previous = (today.replace(day=1) - timedelta(days=1))
        start, end = previous.replace(day=1), previous
    elif preset == "custom":
        try:
            start = datetime.strptime(request.query_params["date_from"], "%Y-%m-%d").date()
            end = datetime.strptime(request.query_params["date_to"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            start, end = today - timedelta(days=29), today
    else: start, end = today - timedelta(days=29), today
    if start > end: start, end = end, start
    if (end - start).days > 366: start = end - timedelta(days=366)
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(start, time.min), tz), timezone.make_aware(datetime.combine(end, time.max), tz)


def client_ip(request):
    return (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")


def audit(request, action, *, site=None, client=None, object_type="", object_id="", metadata=None):
    safe = {key: value for key, value in (metadata or {}).items() if key not in {"password", "token", "secret", "api_key"}}
    PlatformAuditLog.objects.create(actor=request.user, action=action, site=site, client=client, object_type=object_type, object_id=str(object_id or ""), ip_address=client_ip(request), metadata=safe)

