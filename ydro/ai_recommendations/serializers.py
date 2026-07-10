from rest_framework import serializers

from ai_recommendations.models import AIRecommendationJob


class AIRecommendationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendationJob
        fields = ("id", "external_job_id", "remote_job_id", "site", "recommendation_type", "status", "period_from", "period_to", "result", "error_message", "created_at", "started_at", "completed_at", "updated_at")
        read_only_fields = fields


class AIRecommendationCreateSerializer(serializers.Serializer):
    site_id = serializers.IntegerField(min_value=1)
    recommendation_type = serializers.ChoiceField(choices=AIRecommendationJob.Type.choices)
    period_from = serializers.DateField()
    period_to = serializers.DateField()

    def validate(self, attrs):
        if attrs["period_from"] > attrs["period_to"]: raise serializers.ValidationError("Начало периода должно быть раньше окончания.")
        if (attrs["period_to"] - attrs["period_from"]).days > 366: raise serializers.ValidationError("Период не может превышать 366 дней.")
        return attrs

