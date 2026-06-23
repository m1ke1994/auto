from django.urls import path

from .views import (
    ContactRequestCreateAPIView,
    DayScenarioRequestCreateAPIView,
    ServiceRequestCreateAPIView,
)

urlpatterns = [
    path("leads/", ContactRequestCreateAPIView.as_view(), name="contact-request-create"),
    path("service-requests/", ServiceRequestCreateAPIView.as_view(), name="service-request-create"),
    path("day-scenarios/", DayScenarioRequestCreateAPIView.as_view(), name="day-scenario-request-create"),
]
