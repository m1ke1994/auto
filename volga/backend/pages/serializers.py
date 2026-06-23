from rest_framework import serializers

from core.media_utils import FALLBACK_GALLERY_IMAGE, FALLBACK_HERO_IMAGE, media_url_or_fallback
from .models import Page, PageGalleryImage, PageSection


class PageSectionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PageSection
        fields = ("id", "title", "text", "image", "order")

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class PageGalleryImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PageGalleryImage
        fields = ("id", "image", "order")

    def get_image(self, obj):
        return media_url_or_fallback(
            obj.image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_GALLERY_IMAGE,
        )


class PageSerializer(serializers.ModelSerializer):
    hero_image = serializers.SerializerMethodField()
    sections = PageSectionSerializer(many=True, read_only=True)
    gallery = PageGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = (
            "title",
            "slug",
            "subtitle",
            "hero_image",
            "sections",
            "gallery",
        )

    def get_hero_image(self, obj):
        return media_url_or_fallback(
            obj.hero_image,
            request=self.context.get("request"),
            fallback_path=FALLBACK_HERO_IMAGE,
        )
