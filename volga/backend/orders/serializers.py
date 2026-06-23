from rest_framework import serializers

from core.models import Service, Tariff

from .models import ContactRequest, DayScenarioRequest, ServiceRequest


def split_contact(raw_contact, phone="", email=""):
    contact = str(raw_contact or "").strip()
    resolved_phone = str(phone or "").strip()
    resolved_email = str(email or "").strip()

    if contact:
        if "@" in contact and not resolved_email:
            resolved_email = contact
        elif not resolved_phone:
            resolved_phone = contact

    return resolved_phone, resolved_email


class ContactRequestSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ContactRequest
        fields = (
            "id",
            "name",
            "contact",
            "phone",
            "email",
            "message",
            "created_at",
            "status",
        )
        read_only_fields = ("id", "created_at", "status")
        extra_kwargs = {
            "phone": {"required": False, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
            "message": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        phone, email = split_contact(
            attrs.pop("contact", ""),
            phone=attrs.get("phone", ""),
            email=attrs.get("email", ""),
        )
        if not phone and not email:
            raise serializers.ValidationError("Укажите телефон или email для связи.")

        attrs["phone"] = phone
        attrs["email"] = email
        return attrs


class ServiceRequestSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(write_only=True, required=False, allow_blank=True)
    service_slug = serializers.SlugField(write_only=True)
    tariff_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    message = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ServiceRequest
        fields = (
            "id",
            "service",
            "service_slug",
            "tariff_id",
            "name",
            "contact",
            "phone",
            "tariff",
            "message",
            "created_at",
            "status",
        )
        read_only_fields = ("id", "service", "tariff", "created_at", "status")
        extra_kwargs = {
            "phone": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        phone, _ = split_contact(
            attrs.pop("contact", ""),
            phone=attrs.get("phone", ""),
        )
        if not phone:
            raise serializers.ValidationError("Укажите телефон для связи.")

        service_slug = attrs.pop("service_slug")
        service = Service.objects.filter(slug=service_slug).first()
        if service is None:
            raise serializers.ValidationError({"service_slug": "Услуга не найдена."})

        tariff_value = ""
        tariff_id = attrs.pop("tariff_id", None)
        if tariff_id is not None:
            tariff = Tariff.objects.filter(id=tariff_id, service=service).first()
            if tariff is None:
                raise serializers.ValidationError({"tariff_id": "Тариф не найден для выбранной услуги."})
            tariff_value = tariff.title

        message = str(attrs.pop("message", "") or "").strip()
        tariff_prefix = "Выбран тариф:"
        if not tariff_value and message.startswith(tariff_prefix):
            tariff_value = message.split(":", 1)[1].strip()

        attrs["service"] = service
        attrs["phone"] = phone
        attrs["tariff"] = tariff_value
        return attrs


class DayScenarioRequestSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(write_only=True, required=False, allow_blank=True)
    guests_count = serializers.IntegerField(write_only=True, required=False, min_value=1)
    comment = serializers.CharField(write_only=True, required=False, allow_blank=True)
    items = serializers.ListField(write_only=True, required=False, child=serializers.DictField())

    class Meta:
        model = DayScenarioRequest
        fields = (
            "id",
            "name",
            "email",
            "contact",
            "date",
            "guests",
            "guests_count",
            "total_price",
            "comment",
            "items",
            "created_at",
            "status",
        )
        read_only_fields = ("id", "created_at", "status")
        extra_kwargs = {
            "guests": {"required": False},
        }

    def validate(self, attrs):
        _, email = split_contact(
            attrs.pop("contact", ""),
            email=attrs.get("email", ""),
        )
        if not email:
            raise serializers.ValidationError({"email": "Укажите email для связи."})

        guests_count = attrs.pop("guests_count", None)
        if guests_count is not None:
            attrs["guests"] = guests_count

        if not attrs.get("guests"):
            raise serializers.ValidationError({"guests": "Укажите количество гостей."})

        attrs["email"] = email
        attrs.pop("comment", None)
        attrs.pop("items", None)
        return attrs
