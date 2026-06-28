import re
from ipaddress import ip_address
from urllib.parse import urlparse

from rest_framework import serializers


PUSH_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class PushSubscriptionPayloadSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=1024)
    keys = serializers.DictField()

    def validate_endpoint(self, value):
        parsed = urlparse(value)
        if parsed.scheme != "https":
            raise serializers.ValidationError("Push endpoint must use HTTPS.")
        try:
            port = parsed.port
        except ValueError:
            raise serializers.ValidationError("Push endpoint has an invalid port.")
        if parsed.username or parsed.password or port not in (None, 443):
            raise serializers.ValidationError("Push endpoint must use the standard HTTPS origin.")

        hostname = (parsed.hostname or "").rstrip(".").lower()
        if not hostname or hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
            raise serializers.ValidationError("Push endpoint must use a public host.")
        try:
            if not ip_address(hostname).is_global:
                raise serializers.ValidationError("Push endpoint must use a public host.")
        except ValueError:
            pass
        return value

    def validate_keys(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Push subscription keys are required.")

        normalized = {}
        for key_name in ("p256dh", "auth"):
            key_value = value.get(key_name)
            if not isinstance(key_value, str) or not key_value or len(key_value) > 512:
                raise serializers.ValidationError({key_name: "A valid push subscription key is required."})
            if not PUSH_KEY_PATTERN.fullmatch(key_value):
                raise serializers.ValidationError({key_name: "The push subscription key has an invalid format."})
            normalized[key_name] = key_value
        return normalized


class PushSubscriptionDeleteSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=1024)
