from rest_framework import generics

from .models import Page
from .serializers import PageSerializer


class PageDetailView(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    lookup_field = "slug"
    queryset = (
        Page.objects.filter(is_published=True)
        .prefetch_related("sections", "gallery")
        .order_by("order", "id")
    )
