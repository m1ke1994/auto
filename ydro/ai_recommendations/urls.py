from django.urls import path
from ai_recommendations.views import JobDetailView, JobListCreateView, JobRetryView
urlpatterns = [
    path("", JobListCreateView.as_view(), name="ai-recommendation-list"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="ai-recommendation-detail"),
    path("<uuid:pk>/retry/", JobRetryView.as_view(), name="ai-recommendation-retry"),
]

