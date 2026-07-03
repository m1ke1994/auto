from django.urls import path

from .views import (
    DashboardNewsDetailView,
    DashboardNewsListView,
    DashboardNewsReadView,
    DashboardNewsUnreadCountView,
)

app_name = "dashboard_news"

urlpatterns = [
    path("", DashboardNewsListView.as_view(), name="list"),
    path("unread-count/", DashboardNewsUnreadCountView.as_view(), name="unread-count"),
    path("<int:pk>/", DashboardNewsDetailView.as_view(), name="detail"),
    path("<int:pk>/read/", DashboardNewsReadView.as_view(), name="read"),
]

