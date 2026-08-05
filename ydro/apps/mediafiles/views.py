from django.db.models import QuerySet
from django.db.models import Q
import mimetypes
from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import generics
from rest_framework.exceptions import APIException
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.sites.models import Site
from platform_admin.permissions import is_platform_owner
from subscriptions.access import FEATURE_SITE_EDIT
from subscriptions.permissions import HasFeatureAccess

from .models import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, MediaFile
from .serializers import MediaFileSerializer


class MediaApiException(APIException):
    default_code = "media_error"
    default_detail = "Media request failed."

    def __init__(self, *, code, detail, status_code):
        self.status_code = status_code
        super().__init__({"code": code, "detail": detail})


def media_error(code, detail, status_code):
    return Response({"code": code, "detail": detail}, status=status_code)


def _uploaded_file_name(file_obj) -> str:
    return str(getattr(file_obj, "name", "") or "").strip()


def _extension_for_name(filename: str) -> str:
    return PurePath(filename).suffix.lower().lstrip(".")


def _is_safe_filename(filename: str) -> bool:
    if not filename or "/" in filename or "\\" in filename:
        return False
    if PurePath(filename).name != filename:
        return False
    return not any(ord(char) < 32 for char in filename)


def _read_signature(file_obj, size=64) -> bytes:
    position = None
    try:
        position = file_obj.tell()
    except (AttributeError, OSError):
        position = None

    try:
        header = file_obj.read(size)
    finally:
        try:
            file_obj.seek(0 if position is None else position)
        except (AttributeError, OSError):
            pass

    return header or b""


def _signature_matches(extension: str, header: bytes) -> bool:
    if extension in {"jpg", "jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if extension == "png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == "webp":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if extension == "ico":
        return header.startswith((b"\x00\x00\x01\x00", b"\x00\x00\x02\x00"))
    if extension == "mp4":
        return len(header) >= 12 and header[4:8] == b"ftyp"
    if extension == "webm":
        return header.startswith(b"\x1a\x45\xdf\xa3")
    return False


def validate_uploaded_media_file(file_obj):
    if file_obj is None:
        raise MediaApiException(
            code="file_required",
            detail="File is required.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    filename = _uploaded_file_name(file_obj)
    if not _is_safe_filename(filename):
        raise MediaApiException(
            code="invalid_media_type",
            detail="Invalid file name.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    max_size = int(getattr(settings, "MEDIAFILE_MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
    file_size = int(getattr(file_obj, "size", 0) or 0)
    if file_size > max_size:
        raise MediaApiException(
            code="file_too_large",
            detail=f"File is too large. Maximum size is {max_size} bytes.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    extension = _extension_for_name(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise MediaApiException(
            code="invalid_media_type",
            detail="Unsupported media type.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    supplied_mime = str(getattr(file_obj, "content_type", "") or "").split(";")[0].lower().strip()
    guessed_mime = (mimetypes.guess_type(filename)[0] or "").lower()
    allowed_mime_types = ALLOWED_MIME_TYPES[extension]
    if supplied_mime:
        mime_matches = supplied_mime in allowed_mime_types
    else:
        mime_matches = guessed_mime in allowed_mime_types
    if not mime_matches:
        raise MediaApiException(
            code="invalid_media_type",
            detail="File extension and MIME type do not match.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not _signature_matches(extension, _read_signature(file_obj)):
        raise MediaApiException(
            code="invalid_media_type",
            detail="File content does not match the declared media type.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ClientMediaAccessMixin:
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def get_accessible_sites(self) -> QuerySet[Site]:
        queryset = Site.objects.filter(is_active=True)
        if self.request.user.is_superuser or is_platform_owner(self.request.user):
            return queryset
        return queryset.filter(owner=self.request.user)

    def resolve_site(self, requested=None, *, required=False) -> Site:
        requested = str(requested or "").strip()
        queryset = self.get_accessible_sites()

        if not requested:
            if required:
                raise MediaApiException(
                    code="site_not_found",
                    detail="Site is required.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            site = queryset.order_by("id").first()
            if site is None:
                raise MediaApiException(
                    code="site_not_found",
                    detail="Active site for current user was not found.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            return site

        lookup = Q(slug=requested)
        if requested.isdigit():
            lookup |= Q(id=int(requested))
        site = Site.objects.filter(is_active=True).filter(lookup).first()
        if site is None:
            raise MediaApiException(
                code="site_not_found",
                detail="Active site was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not queryset.filter(pk=site.pk).exists():
            raise MediaApiException(
                code="permission_denied",
                detail="You do not have permission to access media for this site.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return site

    def get_client_site(self) -> Site:
        return self.resolve_site()

    def get_queryset(self) -> QuerySet[MediaFile]:
        return MediaFile.objects.filter(site__in=self.get_accessible_sites()).select_related("site", "uploaded_by")


class ClientMediaListView(ClientMediaAccessMixin, generics.ListAPIView):
    serializer_class = MediaFileSerializer

    def get_queryset(self) -> QuerySet[MediaFile]:
        queryset = super().get_queryset()
        site = self.request.query_params.get("site")
        file_type = self.request.query_params.get("file_type")
        search = self.request.query_params.get("search")

        if site:
            queryset = queryset.filter(site=self.resolve_site(site))
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        if search:
            queryset = queryset.filter(
                Q(original_name__icontains=search)
                | Q(title__icontains=search)
                | Q(alt_text__icontains=search)
                | Q(description__icontains=search)
            )

        return queryset.order_by("-uploaded_at")


class ClientMediaUploadView(ClientMediaAccessMixin, generics.CreateAPIView):
    serializer_class = MediaFileSerializer
    parser_classes = [MultiPartParser, FormParser]

    def _resolve_site(self):
        return self.resolve_site(self.request.data.get("site"), required=True)

    def _unique_original_name(self, *, site, section_key, field_key, original_name):
        original_name = original_name or "file"
        candidate = original_name
        stem = PurePath(original_name).stem or "file"
        suffix = PurePath(original_name).suffix
        counter = 2

        while MediaFile.objects.filter(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=candidate,
        ).exists():
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1

        return candidate

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file") or request.data.get("file")
        try:
            site = self._resolve_site()
            validate_uploaded_media_file(file_obj)
        except MediaApiException as exc:
            raise exc

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return media_error(
                "media_upload_failed",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.perform_create(serializer, site=site, file_obj=file_obj)
        except (IntegrityError, ValidationError) as exc:
            return media_error(
                "media_upload_failed",
                getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc),
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return media_error(
                "media_upload_failed",
                "Media upload failed.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, *, site=None, file_obj=None):
        if site is None:
            site = self._resolve_site()
        if file_obj is None:
            file_obj = self.request.FILES.get("file") or self.request.data.get("file")
        section_key = str(self.request.data.get("section") or "uploads").strip()[:100] or "uploads"
        field_key = str(self.request.data.get("field") or "").strip()[:255]
        original_name = self._unique_original_name(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=_uploaded_file_name(file_obj),
        )

        serializer.save(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=original_name,
            uploaded_by=self.request.user,
        )


class ClientMediaDetailView(ClientMediaAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MediaFileSerializer
    lookup_field = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def perform_destroy(self, instance):
        storage = instance.file.storage
        file_name = instance.file.name

        instance.delete()

        if file_name:
            storage.delete(file_name)


class UploadFileView(ClientMediaUploadView):
    """
    Alias endpoint for uploader integrations.
    POST /api/uploads/
    """
