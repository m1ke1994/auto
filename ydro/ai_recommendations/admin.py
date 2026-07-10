from django.contrib import admin
from ai_recommendations.models import AIRecommendationJob
@admin.register(AIRecommendationJob)
class AIRecommendationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "site", "recommendation_type", "status", "created_at")
    list_filter = ("status", "recommendation_type")
    readonly_fields = ("input_snapshot", "result")

