from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import ClientProfile


class ClientProfileMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ("display_name", "company_name", "phone")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "Укажите текущий пароль.",
            "blank": "Укажите текущий пароль.",
        },
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "Укажите новый пароль.",
            "blank": "Укажите новый пароль.",
        },
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "Повторите новый пароль.",
            "blank": "Повторите новый пароль.",
        },
    )


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=150,
        error_messages={
            "required": "Укажите имя.",
            "blank": "Укажите имя.",
            "max_length": "Имя слишком длинное.",
        },
    )
    email = serializers.EmailField(
        max_length=150,
        error_messages={
            "required": "Укажите email.",
            "blank": "Укажите email.",
            "invalid": "Введите корректный email.",
            "max_length": "Email слишком длинный.",
        },
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "Укажите пароль.",
            "blank": "Укажите пароль.",
        },
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "Повторите пароль.",
            "blank": "Повторите пароль.",
        },
    )
    company_name = serializers.CharField(
        max_length=255,
        error_messages={
            "required": "Укажите название компании или проекта.",
            "blank": "Укажите название компании или проекта.",
            "max_length": "Название компании или проекта слишком длинное.",
        },
    )
    contact = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default="",
        error_messages={"max_length": "Контакт слишком длинный."},
    )
    accepted_terms = serializers.BooleanField(
        write_only=True,
        error_messages={
            "required": "Необходимо принять пользовательское соглашение и политику конфиденциальности.",
            "invalid": "Необходимо принять пользовательское соглашение и политику конфиденциальности.",
        },
    )

    def validate_email(self, value):
        email = value.strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо принять пользовательское соглашение и политику конфиденциальности."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})

        user_model = get_user_model()
        password_user = user_model(
            username=attrs["email"],
            email=attrs["email"],
            first_name=attrs["name"],
        )
        try:
            validate_password(attrs["password"], user=password_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["name"],
            is_staff=False,
            is_superuser=False,
        )
        ClientProfile.objects.create(
            user=user,
            display_name=validated_data["name"],
            company_name=validated_data["company_name"],
            phone=validated_data.get("contact", ""),
        )
        return user


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    profile = serializers.SerializerMethodField()
    sites_count = serializers.SerializerMethodField()

    def get_profile(self, obj):
        profile = getattr(obj, "client_profile", None)
        if profile is None:
            return None
        return ClientProfileMeSerializer(profile).data

    def get_sites_count(self, obj):
        return obj.sites.count()


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs):
        username_field = self.username_field
        candidate = attrs.get(username_field)

        if candidate and "@" in candidate:
            user_model = get_user_model()
            user = user_model.objects.filter(email__iexact=candidate).order_by("id").first()
            if user is not None:
                attrs[username_field] = getattr(user, username_field)

        return super().validate(attrs)
