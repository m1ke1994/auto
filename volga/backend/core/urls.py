from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleDetailAPIView,
    ArticleListAPIView,
    HeroBlockAPIView,
    NewsDetailAPIView,
    NewsListAPIView,
    ReviewViewSet,
    ScheduleViewSet,
    ServiceViewSet,
    SiteSettingsAPIView,
)

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="reviews")
router.register("services", ServiceViewSet, basename="services")
router.register("schedule", ScheduleViewSet, basename="schedule")

urlpatterns = [
    path("hero/", HeroBlockAPIView.as_view(), name="hero-api"),
    path("site-settings/", SiteSettingsAPIView.as_view(), name="site-settings-api"),
    path("articles/", ArticleListAPIView.as_view(), name="articles-list"),
    path("articles/<slug:slug>/", ArticleDetailAPIView.as_view(), name="articles-detail"),
    path("news/", NewsListAPIView.as_view(), name="news-list"),
    path("news/<slug:slug>/", NewsDetailAPIView.as_view(), name="news-detail"),
    path("", include(router.urls)),
]
