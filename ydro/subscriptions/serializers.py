from rest_framework import serializers

from subscriptions.models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "period_months",
            "duration_days",
            "price",
            "old_price",
            "discount_percent",
            "currency",
            "features",
            "recommended",
            "sort_order",
        )


class CreatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
