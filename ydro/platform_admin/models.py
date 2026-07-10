from django.conf import settings
from django.db import models


class PlatformAccess(models.Model):
    """Permission anchor; no business data is stored here."""

    class Meta:
        default_permissions = ()
        permissions = (
            ("access_platform", "Can access platform administration"),
            ("view_platform_personal_data", "Can view personal lead data across platform"),
            ("view_platform_tracker_key", "Can view tracker API keys across platform"),
            ("manage_platform_recommendations", "Can manage and inspect AI recommendations"),
        )


class PlatformAuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="platform_audit_logs")
    action = models.CharField(max_length=64, db_index=True)
    site = models.ForeignKey("sites.Site", null=True, blank=True, on_delete=models.SET_NULL)
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("action", "created_at")), models.Index(fields=("site", "created_at"))]

