from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from clients.models import PushSubscription
from clients.push_serializers import PushSubscriptionDeleteSerializer, PushSubscriptionPayloadSerializer


class PushSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        public_key = str(getattr(settings, "WEB_PUSH_VAPID_PUBLIC_KEY", "") or "")
        configured = bool(
            public_key
            and getattr(settings, "WEB_PUSH_VAPID_PRIVATE_KEY", "")
            and getattr(settings, "WEB_PUSH_VAPID_SUBJECT", "")
        )
        active_endpoints = list(
            PushSubscription.objects.filter(user=request.user, is_active=True).values_list("endpoint", flat=True)
        )
        return Response(
            {
                "configured": configured,
                "vapid_public_key": public_key,
                "active_endpoints": active_endpoints,
            }
        )

    def post(self, request):
        serializer = PushSubscriptionPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        endpoint = serializer.validated_data["endpoint"]
        keys = serializer.validated_data["keys"]

        try:
            with transaction.atomic():
                subscription = PushSubscription.objects.select_for_update().filter(endpoint=endpoint).first()
                if subscription is not None and subscription.user_id != request.user.id:
                    return Response(
                        {"detail": "This push endpoint is already registered."},
                        status=status.HTTP_409_CONFLICT,
                    )

                created = subscription is None
                if created:
                    subscription = PushSubscription(endpoint=endpoint, user=request.user)
                subscription.p256dh = keys["p256dh"]
                subscription.auth = keys["auth"]
                subscription.user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
                subscription.is_active = True
                subscription.save()
        except IntegrityError:
            return Response(
                {"detail": "This push endpoint could not be registered."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"id": subscription.id, "is_active": subscription.is_active},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        serializer = PushSubscriptionDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PushSubscription.objects.filter(
            user=request.user,
            endpoint=serializer.validated_data["endpoint"],
        ).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)
