from django.contrib import admin

from .models import DashboardNews


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
# UserNewsRead — технический журнал прочтений; модель продолжает работать,
# но отдельный раздел в Django admin пользователю не нужен.
