from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import ContactRequest, DayScenarioRequest, ServiceRequest
from .serializers import (
    ContactRequestSerializer,
    DayScenarioRequestSerializer,
    ServiceRequestSerializer,
)


class ContactRequestCreateAPIView(generics.CreateAPIView):
    queryset = ContactRequest.objects.all()
    serializer_class = ContactRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class ServiceRequestCreateAPIView(generics.CreateAPIView):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class DayScenarioRequestCreateAPIView(generics.CreateAPIView):
    queryset = DayScenarioRequest.objects.all()
    serializer_class = DayScenarioRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

# Create your views here.
