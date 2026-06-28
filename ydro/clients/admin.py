from django.contrib import admin
from django.utils.html import format_html, format_html_join

from clients.models import Client, PushSubscription


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "uuid", "owner", "owner_sites", "is_active", "send_to_telegram", "created_at")
    search_fields = ("name", "owner__email", "api_key")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)

    readonly_fields = ("uuid", "api_key", "tracker_url_readonly", "public_script_snippet")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "owner",
                    "name",
                    "uuid",
                    "api_key",
                    "tracker_url_readonly",
                    "public_script_snippet",
                    "telegram_chat_id",
                    "send_to_telegram",
                    "is_active",
                )
            },
        ),
    )

    def tracker_url_readonly(self, obj):
        if not obj.pk:
            return "-"
        return obj.tracker_script_url

    tracker_url_readonly.short_description = "URL трекера"

    def public_script_snippet(self, obj):
        if not obj.pk:
            return "-"
        return format_html('<textarea rows="3" readonly style="width:100%;font-family:monospace;">{}</textarea>', obj.public_script_tag)

    public_script_snippet.short_description = "Скрипт подключения"

    @admin.display(description="Сайты владельца")
    def owner_sites(self, obj):
        if not obj.pk or not obj.owner_id:
            return "-"

        sites = list(obj.owner.sites.order_by("name").values_list("name", "slug")[:5])
        if not sites:
            return "-"

        return format_html_join("", "<div>{} <code>{}</code></div>", sites)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_active", "created_at", "updated_at")
    search_fields = ("user__email", "user__username", "endpoint")
    list_filter = ("is_active", "created_at", "updated_at")
    readonly_fields = ("user", "endpoint", "p256dh", "auth", "user_agent", "created_at", "updated_at")
