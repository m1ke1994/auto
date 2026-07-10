from django.contrib import admin
from platform_admin.models import PlatformAuditLog

@admin.register(PlatformAuditLog)
class PlatformAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "site", "object_type", "object_id")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "actor__email", "object_id")
    readonly_fields = tuple(field.name for field in PlatformAuditLog._meta.fields)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

