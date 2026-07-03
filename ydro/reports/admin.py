from django.contrib import admin

from reports.models import ReportSettings

ReportSettings._meta.verbose_name = "Настройки отчётов"
ReportSettings._meta.verbose_name_plural = "Настройки отчётов"


@admin.register(ReportSettings)
class ReportSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "daily_pdf_enabled", "last_sent_at", "updated_at")
    search_fields = ("client__name", "client__owner__email")
    list_filter = ("daily_pdf_enabled",)
