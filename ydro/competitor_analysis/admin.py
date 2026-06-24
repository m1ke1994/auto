from django.contrib import admin

from competitor_analysis.models import CompetitorAnalysis


@admin.register(CompetitorAnalysis)
class CompetitorAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "site", "client", "user_domain", "competitor_domain", "status", "created_at", "finished_at")
    list_filter = ("status", "site", "client")
    search_fields = ("site__name", "site__domain", "user_domain", "competitor_domain", "client__name", "client__owner__email")
    readonly_fields = ("created_at", "updated_at", "finished_at")
