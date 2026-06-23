from django.contrib import admin

from .models import ContactRequest, DayScenarioRequest, ServiceRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "email", "created_at", "status")
    ordering = ("-created_at",)
    search_fields = ("name", "phone", "email")
    list_filter = ("status",)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "service", "tariff", "created_at", "status")
    ordering = ("-created_at",)
    search_fields = ("name", "phone", "service__title", "tariff")
    list_filter = ("status", "service")
    autocomplete_fields = ("service",)


@admin.register(DayScenarioRequest)
class DayScenarioRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "date", "guests", "created_at", "status")
    ordering = ("-created_at",)
    search_fields = ("name", "email")
    list_filter = ("status", "date")

# Register your models here.
