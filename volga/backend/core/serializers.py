from rest_framework import serializers

from .media_utils import (
    FALLBACK_AVATAR_IMAGE,
    FALLBACK_GALLERY_IMAGE,
    FALLBACK_HERO_IMAGE,
    media_url_or_fallback,
)
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


class HeroBlockSerializer(serializers.ModelSerializer):
    background_image = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = HeroBlock
        fields = ("id", "title", "description", "background_image", "avatar")

    def get_background_image(self, obj):
        return media_url_or_fallback(
            obj.background_image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_HERO_IMAGE,
        )

    def get_avatar(self, obj):
        return media_url_or_fallback(
            obj.avatar,
            request=self.context.get("request"),
            fallback_path=FALLBACK_AVATAR_IMAGE,
        )


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ("phone", "email", "telegram_url", "telegram_username", "address")


class ReviewSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = "__all__"

    def get_avatar(self, obj):
        return media_url_or_fallback(
            obj.avatar,
            request=self.context.get("request"),
            fallback_path=None,
        )


class ArticleSerializer(serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = "__all__"

    def get_preview_image(self, obj):
        return media_url_or_fallback(
            obj.preview_image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class ArticleListSerializer(serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            "title",
            "slug",
            "preview_image",
            "preview_description",
            "content_type",
            "published_date",
            "created_at",
        )

    def get_preview_image(self, obj):
        return media_url_or_fallback(
            obj.preview_image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class NewsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = "__all__"

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class NewsListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ("id", "title", "slug", "description", "image", "published_date")

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ("id", "title", "slug", "description", "duration", "price", "order")


class ServiceImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ServiceImage
        fields = ("id", "image", "image_url", "order")

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )

    def get_image_url(self, obj):
        return self.get_image(obj)


class ServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    tariffs = TariffSerializer(many=True, read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "image",
            "image_url",
            "is_category",
            "order",
            "children",
            "tariffs",
            "images",
        )

    def get_children(self, obj):
        children = obj.children.all().order_by("order")
        return ServiceSerializer(children, many=True, context=self.context).data

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )

    def get_image_url(self, obj):
        return self.get_image(obj)


class ScheduleEventSerializer(serializers.ModelSerializer):
    time_start = serializers.TimeField(format="%H:%M")
    time_end = serializers.TimeField(format="%H:%M")
    image = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEvent
        fields = (
            "id",
            "time_start",
            "time_end",
            "title",
            "category",
            "description",
            "price",
            "color",
            "image",
        )

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class ScheduleDaySerializer(serializers.ModelSerializer):
    weekday = serializers.SerializerMethodField()
    events = ScheduleEventSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduleDay
        fields = ("date", "weekday", "events")

    def get_weekday(self, obj):
        weekdays = [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]
        return weekdays[obj.date.weekday()]
