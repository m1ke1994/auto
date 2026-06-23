from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/pages/", include("pages.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("core.urls")),
]

# ВАЖНО: media должны раздаваться всегда, не только при DEBUG
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
