from django.db.models import DateTimeField, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DashboardNews, UserNewsRead
from .serializers import DashboardNewsDetailSerializer, DashboardNewsListSerializer


class PublishedNewsMixin:
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        read_at = UserNewsRead.objects.filter(
            user=self.request.user,
            news_id=OuterRef("pk"),
        ).values("read_at")[:1]
        return (
            DashboardNews.objects.filter(is_published=True, published_at__lte=timezone.now())
            .annotate(user_read_at=Subquery(read_at, output_field=DateTimeField()))
            .order_by("-is_important", "-published_at", "-created_at")
        )


class DashboardNewsListView(PublishedNewsMixin, generics.ListAPIView):
    serializer_class = DashboardNewsListSerializer


class DashboardNewsDetailView(PublishedNewsMixin, generics.RetrieveAPIView):
    serializer_class = DashboardNewsDetailSerializer


class DashboardNewsReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        news = get_object_or_404(
            DashboardNews,
            pk=pk,
            is_published=True,
            published_at__lte=timezone.now(),
        )
        read_record, _ = UserNewsRead.objects.get_or_create(user=request.user, news=news)
        return Response(
            {"is_read": True, "read_at": read_record.read_at},
            status=status.HTTP_200_OK,
        )


class DashboardNewsUnreadCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = (
            DashboardNews.objects.filter(is_published=True, published_at__lte=timezone.now())
            .exclude(read_records__user=request.user)
            .count()
        )
        return Response({"count": count})

