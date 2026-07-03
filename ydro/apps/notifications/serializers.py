from django.utils.text import Truncator
from rest_framework import serializers

from .models import DashboardNews


class DashboardNewsListSerializer(serializers.ModelSerializer):
    short_body = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    read_at = serializers.DateTimeField(source="user_read_at", read_only=True, allow_null=True)

    class Meta:
        model = DashboardNews
        fields = (
            "id",
            "title",
            "short_body",
            "created_at",
            "published_at",
            "is_important",
            "is_read",
            "read_at",
        )

    def get_short_body(self, obj):
        return Truncator(obj.body).chars(240)

    def get_is_read(self, obj):
        return obj.user_read_at is not None


class DashboardNewsDetailSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    read_at = serializers.DateTimeField(source="user_read_at", read_only=True, allow_null=True)

    class Meta:
        model = DashboardNews
        fields = (
            "id",
            "title",
            "body",
            "created_at",
            "published_at",
            "is_important",
            "is_read",
            "read_at",
        )

    def get_is_read(self, obj):
        return obj.user_read_at is not None

