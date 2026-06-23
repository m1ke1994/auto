from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, HeroBlock, News, Review, ScheduleDay, Service, SiteSettings
from .serializers import (
    ArticleListSerializer,
    ArticleSerializer,
    HeroBlockSerializer,
    NewsListSerializer,
    NewsSerializer,
    ReviewSerializer,
    ScheduleDaySerializer,
    ServiceSerializer,
    SiteSettingsSerializer,
)

DEFAULT_SITE_SETTINGS = {
    "phone": "+7 (985) 200-63-22",
    "email": "elizaveta-struchkova@yandex.ru",
    "telegram_url": "https://t.me/novoe_konakovo",
    "telegram_username": "@novoe_konakovo",
    "address": "Тверская область, Конаковский район, природный кластер «Новое Конаково».",
}


class HeroBlockAPIView(APIView):
    def get(self, request):
        hero = HeroBlock.objects.filter(is_active=True).order_by("-created_at").first()
        if hero is None:
            return Response(
                {"detail": "Активный Hero-блок не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HeroBlockSerializer(hero, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SiteSettingsAPIView(APIView):
    def get(self, request):
        site_settings = SiteSettings.objects.order_by("id").first()
        if site_settings is None:
            site_settings = SiteSettings(**DEFAULT_SITE_SETTINGS)

        serializer = SiteSettingsSerializer(site_settings, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class ArticleListAPIView(generics.ListAPIView):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleListSerializer


class ArticleDetailAPIView(generics.RetrieveAPIView):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer
    lookup_field = "slug"


class NewsListAPIView(generics.ListAPIView):
    queryset = News.objects.filter(is_published=True)
    serializer_class = NewsListSerializer


class NewsDetailAPIView(generics.RetrieveAPIView):
    queryset = News.objects.filter(is_published=True)
    serializer_class = NewsSerializer
    lookup_field = "slug"


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(parent__isnull=True).prefetch_related(
        "tariffs",
        "images",
        "children",
        "children__tariffs",
        "children__images",
    )
    serializer_class = ServiceSerializer


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScheduleDay.objects.filter(is_published=True).prefetch_related("events").order_by("date")
    serializer_class = ScheduleDaySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def list(self, request, *args, **kwargs):
        days = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(days, many=True)
        day_items = serializer.data

        month_labels = [
            "Январь",
            "Февраль",
            "Март",
            "Апрель",
            "Май",
            "Июнь",
            "Июль",
            "Август",
            "Сентябрь",
            "Октябрь",
            "Ноябрь",
            "Декабрь",
        ]

        grouped = {}
        ordered_keys = []

        for day in day_items:
            date_raw = day.get("date", "")
            year, month, _ = map(int, date_raw.split("-"))
            key = (year, month)
            if key not in grouped:
                ordered_keys.append(key)
                grouped[key] = {
                    "month": f"{month_labels[month - 1]} {year}",
                    "year": year,
                    "month_number": month,
                    "days": [],
                }
            grouped[key]["days"].append(day)

        return Response([grouped[key] for key in ordered_keys])
