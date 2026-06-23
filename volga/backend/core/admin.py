import json

from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Article,
    HeroBlock,
    News,
    Review,
    ScheduleDay,
    ScheduleEvent,
    Service,
    ServiceImage,
    SiteSettings,
    Tariff,
)


@admin.register(HeroBlock)
class HeroBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    fields = (
        "title",
        "description",
        "background_image",
        "background_image_preview",
        "avatar",
        "avatar_preview",
        "is_active",
    )
    readonly_fields = ("background_image_preview", "avatar_preview")

    def has_add_permission(self, request):
        if HeroBlock.objects.exists():
            return False
        return super().has_add_permission(request)

    @admin.display(description="Превью фона")
    def background_image_preview(self, obj):
        if obj and obj.background_image:
            return format_html(
                '<img src="{}" style="max-width: 320px; border-radius: 8px;" />',
                obj.background_image.url,
            )
        return "Изображение не загружено"

    @admin.display(description="Превью аватара")
    def avatar_preview(self, obj):
        if obj and obj.avatar:
            return format_html(
                '<img src="{}" style="max-width: 140px; border-radius: 9999px;" />',
                obj.avatar.url,
            )
        return "Изображение не загружено"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("phone", "email", "telegram_username", "updated_at")
    fields = ("phone", "email", "telegram_url", "telegram_username", "address")

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "Администрирование"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Управление контентом"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("avatar", "name", "event_name", "rating", "date", "created_at")
    list_filter = ("rating", "date")
    search_fields = ("name", "event_name")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "is_published", "published_date", "created_at")
    list_filter = ("content_type", "is_published", "published_date")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Основное", {"fields": ("title", "slug", "content_type", "is_published", "published_date")}),
        ("Превью", {"fields": ("preview_image", "preview_description")}),
        ("Контент", {"fields": ("content", "video_url")}),
    )


class NewsAdminForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 12}),
        help_text="Можно вставить JSON-массив или обычный текст абзацами (через пустую строку).",
    )

    class Meta:
        model = News
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        value = self.initial.get("content")
        if isinstance(value, list):
            self.initial["content"] = "\n\n".join(str(item) for item in value if str(item).strip())

    def clean_content(self):
        raw = (self.cleaned_data.get("content") or "").strip()
        if not raw:
            return []

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

        paragraphs = [part.strip() for part in raw.split("\n\n") if part.strip()]
        if paragraphs:
            return paragraphs

        return [raw]


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ("title", "published_date", "is_published", "created_at")
    list_filter = ("is_published", "published_date")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Основное", {"fields": ("title", "slug", "published_date", "is_published")}),
        ("Превью", {"fields": ("description", "image")}),
        ("Контент", {"fields": ("content",)}),
    )

class TariffInline(admin.TabularInline):
    model = Tariff
    extra = 1
    fields = ("title", "slug", "description", "duration", "price", "order")


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ("image", "order")
    ordering = ("order", "id")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "is_category", "parent", "order")
    list_filter = ("is_category",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    fields = ("title", "slug", "description", "image", "is_active", "is_category", "parent", "order")
    inlines = (TariffInline, ServiceImageInline)


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "order")
    search_fields = ("service__title",)
    autocomplete_fields = ("service",)
    ordering = ("order", "id")


class ScheduleEventInline(admin.TabularInline):
    model = ScheduleEvent
    extra = 1
    fields = (
        "time_start",
        "time_end",
        "title",
        "category",
        "image",
        "service",
        "price",
        "color",
        "order",
    )
    autocomplete_fields = ("service",)


@admin.register(ScheduleDay)
class ScheduleDayAdmin(admin.ModelAdmin):
    list_display = ("date", "is_published")
    list_filter = ("is_published",)
    date_hierarchy = "date"
    search_fields = ("date",)
    inlines = (ScheduleEventInline,)


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ("day", "time_start", "time_end", "title", "category", "service", "price", "order")
    list_filter = ("category", "day__is_published")
    search_fields = ("title", "category", "description")
    autocomplete_fields = ("day", "service")
    fields = (
        "day",
        "time_start",
        "time_end",
        "title",
        "category",
        "description",
        "image",
        "service",
        "price",
        "color",
        "order",
    )
