from django.contrib import admin

from .models import DashboardNews, UserNewsRead


@admin.register(DashboardNews)
class DashboardNewsAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "is_important", "published_at", "created_by", "created_at")
    list_filter = ("is_published", "is_important", "published_at", "created_at")
    search_fields = ("title", "body")
    readonly_fields = ("created_at", "updated_at", "created_by")
    date_hierarchy = "created_at"
    fieldsets = (
        ("Новость", {"fields": ("title", "body", "is_important")}),
        ("Публикация", {"fields": ("is_published", "published_at")}),
        ("Служебное", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserNewsRead)
class UserNewsReadAdmin(admin.ModelAdmin):
    list_display = ("user", "news", "read_at")
    list_filter = ("read_at", "news__is_important")
    search_fields = ("user__username", "user__email", "news__title")
    readonly_fields = ("user", "news", "read_at")

    def has_add_permission(self, request):
        return False

