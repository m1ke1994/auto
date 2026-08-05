import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from io import StringIO
from pathlib import Path

from apps.sites.models import Site, SiteSection
from subscriptions.test_utils import grant_business_analytics

from .models import MediaFile
from .views import MediaApiException, validate_uploaded_media_file


PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
WEBP_BYTES = b"RIFF\x1a\x00\x00\x00WEBPVP8 "
ICO_BYTES = b"\x00\x00\x01\x00\x01\x00"
MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42"
WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01"


class UnsafeNamedFile:
    def __init__(self, name, content=PNG_BYTES, content_type="image/png"):
        self.name = name
        self._content = content
        self.content_type = content_type
        self.size = len(content)
        self._position = 0

    def tell(self):
        return self._position

    def seek(self, position):
        self._position = position

    def read(self, size=-1):
        chunk = self._content[self._position:] if size == -1 else self._content[self._position:self._position + size]
        self._position += len(chunk)
        return chunk


class MediaUploadTests(APITestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()

        self.user = get_user_model().objects.create_user(
            username="media-owner",
            email="media@example.com",
            password="test-test",
        )
        self.site = Site.objects.create(
            name="Leelabird",
            slug="a-meditation",
            domain="localhost:5173",
            owner=self.user,
        )
        grant_business_analytics(self.user)
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_dir.cleanup()

    def test_reupload_same_file_keeps_prior_media_record(self):
        url = reverse("upload-file")
        payload = {
            "site": str(self.site.id),
            "section": "hero",
            "field": "image",
            "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
        }
        first = self.client.post(url, payload, format="multipart")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        payload["file"] = SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png")
        second = self.client.post(url, payload, format="multipart")

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MediaFile.objects.count(), 2)
        self.assertTrue(second.data["path"].startswith(f"/media/sites/{self.site.id}/hero/"))
        self.assertEqual(
            list(MediaFile.objects.order_by("id").values_list("original_name", flat=True)),
            ["cover.png", "cover-2.png"],
        )
        self.assertEqual(MediaFile.objects.latest("id").uploaded_by, self.user)
        self.assertEqual(len(MediaFile.objects.latest("id").checksum_sha256), 64)

    def test_media_library_supports_list_patch_and_delete(self):
        upload = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )
        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)
        media_id = upload.data["id"]

        listing = self.client.get(reverse("client-media-list"), {"site": self.site.id, "file_type": "image"})
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.data), 1)

        detail_url = reverse("client-media-detail", kwargs={"id": media_id})
        patched = self.client.patch(
            detail_url,
            {"title": "Hero cover", "alt_text": "Meditation hero"},
            format="json",
        )
        self.assertEqual(patched.status_code, status.HTTP_200_OK)
        self.assertEqual(patched.data["title"], "Hero cover")
        self.assertEqual(patched.data["alt_text"], "Meditation hero")
        self.assertEqual(patched.data["alt"], "Meditation hero")

        deleted = self.client.delete(detail_url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MediaFile.objects.filter(id=media_id).exists())

    def test_media_library_does_not_expose_another_users_site(self):
        other_user = get_user_model().objects.create_user(
            username="other-media-owner",
            email="other-media@example.com",
            password="test-test",
        )
        other_site = Site.objects.create(
            name="Other",
            slug="other",
            domain="other.test",
            owner=other_user,
        )
        MediaFile.objects.create(
            site=other_site,
            file=SimpleUploadedFile("private.png", PNG_BYTES, content_type="image/png"),
        )

        response = self.client.get(reverse("client-media-list"), {"site": other_site.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "permission_denied")

    def test_upload_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_requires_file(self):
        response = self.client.post(
            reverse("upload-file"),
            {"site": str(self.site.id), "section": "hero", "field": "image"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "file_required")

    def test_upload_requires_concrete_site(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], "site_not_found")

    def test_upload_to_unknown_site_returns_site_not_found(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": "missing-site",
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], "site_not_found")

    def test_upload_to_another_users_site_returns_permission_denied(self):
        other_user = get_user_model().objects.create_user(
            username="other-upload-owner",
            email="other-upload@example.com",
            password="test-test",
        )
        other_site = Site.objects.create(
            name="Other Upload",
            slug="other-upload",
            domain="upload-other.test",
            owner=other_user,
        )

        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(other_site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "permission_denied")

    def test_upload_accepts_jpeg_png_webp_ico_mp4_and_webm(self):
        samples = [
            ("photo.jpg", JPEG_BYTES, "image/jpeg", "image"),
            ("photo.png", PNG_BYTES, "image/png", "image"),
            ("photo.webp", WEBP_BYTES, "image/webp", "image"),
            ("favicon.ico", ICO_BYTES, "image/x-icon", "image"),
            ("clip.mp4", MP4_BYTES, "video/mp4", "video"),
            ("clip.webm", WEBM_BYTES, "video/webm", "video"),
        ]

        for name, content, content_type, expected_type in samples:
            with self.subTest(name=name):
                response = self.client.post(
                    reverse("upload-file"),
                    {
                        "site": str(self.site.id),
                        "section": "gallery",
                        "field": name,
                        "file": SimpleUploadedFile(name, content, content_type=content_type),
                    },
                    format="multipart",
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["file_type"], expected_type)
                self.assertTrue(response.data["path"].startswith(f"/media/sites/{self.site.id}/gallery/"))
                self.assertNotIn(str(self.media_dir.name), response.data["path"])

    def test_upload_rejects_svg(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("icon.svg", b"<svg></svg>", content_type="image/svg+xml"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_media_type")

    def test_upload_rejects_extension_mime_mismatch(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="text/plain"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_media_type")

    def test_upload_rejects_invalid_file_signature(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", b"not a png", content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_media_type")

    @override_settings(MEDIAFILE_MAX_UPLOAD_SIZE=4)
    def test_upload_rejects_large_file(self):
        response = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "file_too_large")

    def test_validator_rejects_path_traversal_filename(self):
        with self.assertRaises(MediaApiException) as context:
            validate_uploaded_media_file(UnsafeNamedFile("../cover.png"))

        self.assertEqual(context.exception.detail["code"], "invalid_media_type")

    def test_detail_endpoint_does_not_expose_another_users_media(self):
        other_user = get_user_model().objects.create_user(
            username="other-detail-owner",
            email="other-detail@example.com",
            password="test-test",
        )
        other_site = Site.objects.create(
            name="Other Detail",
            slug="other-detail",
            domain="detail-other.test",
            owner=other_user,
        )
        media = MediaFile.objects.create(
            site=other_site,
            file=SimpleUploadedFile("private.png", PNG_BYTES, content_type="image/png"),
        )

        response = self.client.get(reverse("client-media-detail", kwargs={"id": media.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_endpoint_removes_physical_media_file(self):
        upload = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )
        media = MediaFile.objects.get(id=upload.data["id"])
        file_path = Path(media.file.path)
        self.assertTrue(file_path.exists())

        response = self.client.delete(reverse("client-media-detail", kwargs={"id": media.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(file_path.exists())

    def test_platform_owner_can_manage_media_for_any_site(self):
        platform_user = get_user_model().objects.create_user(
            username="platform-owner",
            email="platform@example.com",
            password="test-test",
        )
        platform_user.user_permissions.add(
            Permission.objects.get(codename="access_platform", content_type__app_label="platform_admin")
        )
        self.client.force_authenticate(platform_user)

        upload = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )
        listing = self.client.get(reverse("client-media-list"), {"site": self.site.id})

        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.data), 1)

    def test_clearing_section_image_field_does_not_delete_media_file(self):
        upload = self.client.post(
            reverse("upload-file"),
            {
                "site": str(self.site.id),
                "section": "hero",
                "field": "image",
                "file": SimpleUploadedFile("cover.png", PNG_BYTES, content_type="image/png"),
            },
            format="multipart",
        )
        media = MediaFile.objects.get(id=upload.data["id"])
        file_path = Path(media.file.path)
        section = SiteSection.objects.create(
            site=self.site,
            key="editable-hero",
            title="Editable Hero",
            section_type="hero",
            schema={"fields": [{"key": "image", "label": "Image", "type": "image"}]},
            content={"image": media.get_relative_media_path()},
        )

        response = self.client.patch(
            reverse("admin-my-site-section-detail", kwargs={"site_id": self.site.id, "section_id": section.id}),
            {"content": {"image": ""}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"]["image"], "")
        self.assertTrue(MediaFile.objects.filter(id=media.id).exists())
        self.assertTrue(file_path.exists())


class ImportSiteMediaTests(APITestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.media_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()

        user = get_user_model().objects.create_user(
            username="import-owner",
            email="import@example.com",
            password="test-test",
        )
        self.site = Site.objects.create(
            name="Imported site",
            slug="imported-site",
            domain="example.test",
            owner=user,
        )

        images = Path(self.workspace.name) / "assets"
        images.mkdir()
        (images / "one.png").write_bytes(b"same-image")
        (images / "duplicate.png").write_bytes(b"same-image")

    def tearDown(self):
        self.settings_override.disable()
        self.media_dir.cleanup()
        self.workspace.cleanup()

    def test_import_command_is_idempotent_and_reports_duplicates(self):
        report = Path(self.workspace.name) / "report.md"
        stdout = StringIO()

        call_command(
            "import_site_media",
            root=self.workspace.name,
            site=self.site.slug,
            report=str(report),
            stdout=stdout,
        )

        self.assertEqual(MediaFile.objects.count(), 1)
        self.assertIn("imported=1", stdout.getvalue())
        self.assertIn("duplicates=1", stdout.getvalue())
        self.assertTrue(report.exists())

        call_command(
            "import_site_media",
            root=self.workspace.name,
            site=self.site.slug,
            report=str(report),
            stdout=StringIO(),
        )
        self.assertEqual(MediaFile.objects.count(), 1)
