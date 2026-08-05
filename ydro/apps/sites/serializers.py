from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags

from rest_framework import serializers

from leads.services import send_lead_telegram_notification

from .models import SectionSchema, Site, SiteLead, SiteSection
from .a_meditation import SECTION_TITLES
from .seo import build_public_site_seo
from .services import (
    is_technical_template_source_site,
    is_template_catalog_source_site,
    site_capabilities,
    site_metadata,
    site_type,
)
from .volga_site import SECTION_TITLES as VOLGA_SECTION_TITLES
from .tracker_utils import build_tracker_script_tag
from .tasks import send_site_lead_push_notification_task

logger = logging.getLogger(__name__)


class PublicSiteSerializer(serializers.ModelSerializer):
    seo = serializers.SerializerMethodField()
    sections_count = serializers.SerializerMethodField()
    tracker_key = serializers.CharField(source="api_key", read_only=True)

    class Meta:
        model = Site
        fields = ("id", "name", "slug", "domain", "seo", "is_active", "sections_count", "tracker_key")

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()

    def get_seo(self, obj):
        return build_public_site_seo(obj)


class PublicSiteSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "section_type",
            "component_key",
            "order",
            "schema",
            "content",
            "settings",
            "seo",
            "is_active",
        )


class SectionSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionSchema
        fields = ("id", "section_key", "title", "schema", "description", "created_at", "updated_at")


class AdminMySiteSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()
    tracker_script_tag = serializers.SerializerMethodField()
    is_template_source = serializers.SerializerMethodField()
    is_technical_template_source = serializers.SerializerMethodField()
    is_template_catalog_source = serializers.SerializerMethodField()
    site_type = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    render_mode = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = (
            "id",
            "name",
            "slug",
            "domain",
            "owner_id",
            "owner_name",
            "owner_email",
            "api_key",
            "telegram_chat_id",
            "send_to_telegram",
            "telegram_connected_at",
            "seo",
            "is_active",
            "sections_count",
            "tracker_script_tag",
            "is_template_source",
            "is_technical_template_source",
            "is_template_catalog_source",
            "site_type",
            "source",
            "render_mode",
            "status",
            "capabilities",
            "created_at",
            "updated_at",
        )

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()

    def get_tracker_script_tag(self, obj):
        return build_tracker_script_tag(obj.api_key)

    def get_is_template_source(self, obj):
        return is_technical_template_source_site(obj)

    def get_is_technical_template_source(self, obj):
        return is_technical_template_source_site(obj)

    def get_is_template_catalog_source(self, obj):
        return is_template_catalog_source_site(obj)

    def get_site_type(self, obj):
        return site_type(obj)

    def get_owner_name(self, obj):
        owner = getattr(obj, "owner", None)
        if owner is None:
            return ""
        return owner.get_full_name() or owner.username

    def get_owner_email(self, obj):
        return getattr(getattr(obj, "owner", None), "email", "") or ""

    def _metadata(self, obj):
        cache_name = "_tracknode_site_metadata"
        if not hasattr(obj, cache_name):
            setattr(obj, cache_name, site_metadata(obj))
        return getattr(obj, cache_name)

    def get_source(self, obj):
        return self._metadata(obj)["source"]

    def get_render_mode(self, obj):
        return self._metadata(obj)["render_mode"]

    def get_status(self, obj):
        return self._metadata(obj)["status"]

    def get_capabilities(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return site_capabilities(obj, user)


class AdminMySiteSectionSerializer(serializers.ModelSerializer):
    schema_template = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()

    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "display_title",
            "section_type",
            "component_key",
            "order",
            "is_active",
            "schema",
            "schema_template",
            "content",
            "settings",
            "seo",
            "created_at",
            "updated_at",
        )

    def get_schema_template(self, obj):
        site_specific_key = f"{obj.site.slug}-{obj.key}"
        schema_obj = (
            SectionSchema.objects.filter(section_key=site_specific_key).first()
            or SectionSchema.objects.filter(section_key=obj.key).first()
        )
        if not schema_obj:
            return None
        return SectionSchemaSerializer(schema_obj).data

    def get_display_title(self, obj):
        if obj.site.slug == "a-meditation":
            return SECTION_TITLES.get(obj.key, obj.title)
        if obj.site.slug == "novaya-konakova":
            return VOLGA_SECTION_TITLES.get(obj.key, obj.title)
        return obj.title


class AdminMySiteSectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "section_type",
            "component_key",
            "order",
            "is_active",
            "schema",
            "content",
            "settings",
            "seo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "site", "created_at", "updated_at")

    def validate_schema(self, value):
        try:
            SiteSection.validate_schema(value)
        except DjangoValidationError as exc:
            details = exc.message_dict.get("schema", exc.messages)
            raise serializers.ValidationError(details)
        return value

    def validate(self, attrs):
        schema = attrs.get("schema")
        content = attrs.get("content")
        if schema is not None and content is not None:
            try:
                SiteSection.validate_content(content=content, schema=schema)
            except DjangoValidationError as exc:
                details = exc.message_dict.get("content", exc.messages)
                raise serializers.ValidationError({"content": details})
        return attrs


class AdminMySiteSectionPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = ("content",)

    def validate(self, attrs):
        forbidden_fields = set(self.initial_data.keys()) - {"content"}
        if forbidden_fields:
            details = {field: "This field is read-only in this endpoint." for field in sorted(forbidden_fields)}
            raise serializers.ValidationError(details)
        return attrs

    def validate_content(self, value):
        if self.instance is None:
            return value

        try:
            SiteSection.validate_schema(self.instance.schema)
            SiteSection.validate_content(content=value, schema=self.instance.schema)
        except DjangoValidationError as exc:
            details = exc.message_dict.get("content", exc.messages)
            raise serializers.ValidationError(details)

        return value

    def to_representation(self, instance):
        return AdminMySiteSectionSerializer(instance, context=self.context).data


class PublicLeadCreateSerializer(serializers.Serializer):
    site_slug = serializers.SlugField()
    section_key = serializers.CharField(max_length=100, required=False, allow_blank=True)
    form_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=100, required=False, allow_blank=True)
    telegram = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    contact = serializers.CharField(max_length=255, required=False, allow_blank=True, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    service_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    service_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    source_url = serializers.URLField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False)
    consent = serializers.BooleanField(required=False, default=False, write_only=True)
    website = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    existing_site_url = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=300)
    preferred_contact = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=50)

    default_error_messages = {
        "required_fields": "Заполните обязательные поля",
        "site_not_found": "Сайт не найден",
    }

    def validate(self, attrs):
        required_fields = ("site_slug", "name")
        if any(not str(attrs.get(field, "")).strip() for field in required_fields):
            self.fail("required_fields")
        if str(attrs.get("website", "")).strip():
            raise serializers.ValidationError({"website": "Некорректная отправка формы."})

        for field_name in ("name", "phone", "telegram", "email", "message", "service_type", "service_title", "source_url"):
            if field_name in attrs:
                attrs[field_name] = strip_tags(str(attrs.get(field_name) or "")).strip()

        contact = str(attrs.pop("contact", "") or "").strip()
        phone = str(attrs.get("phone", "") or "").strip()
        telegram = str(attrs.get("telegram", "") or "").strip()
        email = str(attrs.get("email", "") or "").strip()
        if contact and not phone and not email:
            if "@" in contact:
                attrs["email"] = contact
            else:
                attrs["phone"] = contact
        if not str(attrs.get("phone", "")).strip() and not str(attrs.get("email", "")).strip() and not telegram:
            raise serializers.ValidationError({"contact": "Укажите телефон, Telegram или email."})
        if attrs.get("service_type") == "tracknode_website_order" and not attrs.get("consent"):
            raise serializers.ValidationError({"consent": "Подтвердите согласие на обработку персональных данных."})
        attrs.pop("website", None)
        return attrs

    def create(self, validated_data):
        site_slug = validated_data.pop("site_slug")
        consent = bool(validated_data.pop("consent", False))
        telegram = validated_data.pop("telegram", "")
        existing_site_url = strip_tags(str(validated_data.pop("existing_site_url", "") or "")).strip()
        preferred_contact = strip_tags(str(validated_data.pop("preferred_contact", "") or "")).strip()
        site = Site.objects.filter(slug=site_slug, is_active=True).first()
        if site is None:
            self.fail("site_not_found")

        request = self.context.get("request")
        meta = getattr(request, "META", {})
        payload = validated_data.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        payload = dict(payload)
        if meta.get("HTTP_REFERER") and not payload.get("referrer"):
            payload["referrer"] = meta["HTTP_REFERER"]
        if telegram:
            payload["telegram"] = telegram
        if existing_site_url:
            payload["existing_site_url"] = existing_site_url
        if preferred_contact:
            payload["preferred_contact"] = preferred_contact
        if consent:
            payload.setdefault("consent_at", timezone.now().isoformat())
        if validated_data.get("service_type") == "tracknode_website_order":
            payload["source"] = "tracknode_website_order"

        lead = SiteLead.objects.create(
            site=site,
            section_key=validated_data.get("section_key", ""),
            form_name=validated_data.get("form_name", ""),
            name=validated_data["name"],
            phone=validated_data.get("phone", ""),
            email=validated_data.get("email", ""),
            message=validated_data.get("message", ""),
            service_type=validated_data.get("service_type", ""),
            service_title=validated_data.get("service_title", ""),
            source_url=validated_data.get("source_url", ""),
            user_agent=meta.get("HTTP_USER_AGENT", "")[:1000],
            ip_address=self._extract_ip(meta),
            payload=payload,
        )
        self._send_site_lead_telegram_notification(site=site, lead=lead)
        transaction.on_commit(lambda: self._enqueue_site_lead_push_notification(site=site, lead=lead))
        return lead

    @staticmethod
    def _extract_ip(meta):
        x_forwarded_for = meta.get("HTTP_X_FORWARDED_FOR", "")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return meta.get("REMOTE_ADDR")

    def _send_site_lead_telegram_notification(self, *, site: Site, lead: SiteLead) -> None:
        try:
            delivered = send_lead_telegram_notification(lead, site=site)
        except Exception:
            logger.exception(
                "Site lead telegram notification crashed site_id=%s lead_id=%s",
                site.id,
                lead.id,
            )
            return
        if not delivered:
            logger.warning(
                "Site lead telegram notification skipped or failed site_id=%s lead_id=%s",
                site.id,
                lead.id,
            )

    @staticmethod
    def _enqueue_site_lead_push_notification(*, site: Site, lead: SiteLead) -> None:
        try:
            send_site_lead_push_notification_task.delay(lead.id)
        except Exception:
            logger.exception(
                "Failed to enqueue site lead push notification site_id=%s lead_id=%s",
                site.id,
                lead.id,
            )


class AdminLeadSerializer(serializers.ModelSerializer):
    site_slug = serializers.CharField(source="site.slug", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    attribution = serializers.SerializerMethodField()

    def get_attribution(self, obj):
        payload = obj.payload if isinstance(obj.payload, dict) else {}
        return {
            "referrer": payload.get("referrer", ""),
            "utm_source": payload.get("utm_source", ""),
            "utm_medium": payload.get("utm_medium", ""),
            "utm_campaign": payload.get("utm_campaign", ""),
            "utm_term": payload.get("utm_term", ""),
            "utm_content": payload.get("utm_content", ""),
        }

    class Meta:
        model = SiteLead
        fields = (
            "id",
            "site",
            "site_slug",
            "site_name",
            "section_key",
            "form_name",
            "name",
            "phone",
            "email",
            "message",
            "service_type",
            "service_title",
            "source_url",
            "status",
            "status_label",
            "attribution",
            "created_at",
            "updated_at",
        )


class AdminLeadStatusPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteLead
        fields = ("status",)
