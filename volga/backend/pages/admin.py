from django.contrib import admin

from .models import Page, PageGalleryImage, PageSection


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 1
    fields = ("title", "text", "image", "order")
    ordering = ("order", "id")


class PageGalleryImageInline(admin.TabularInline):
    model = PageGalleryImage
    extra = 1
    fields = ("image", "order")
    ordering = ("order", "id")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "order", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug")
    ordering = ("order", "id")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline, PageGalleryImageInline)


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "page", "order")
    search_fields = ("title", "page__title")
    ordering = ("order", "id")


@admin.register(PageGalleryImage)
class PageGalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "order")
    search_fields = ("page__title",)
    ordering = ("order", "id")
