from copy import deepcopy
import hashlib
import mimetypes
import os
from pathlib import Path
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.mediafiles.models import MediaFile
from apps.sites.a_meditation import merge_content_defaults
from apps.sites.models import SectionSchema, Site, SiteSection
from apps.sites.volga_site import (
    VOLGA_SECTION_SEEDS,
    VOLGA_SITE_DOMAIN,
    VOLGA_SITE_NAME,
    VOLGA_SITE_SLUG,
    get_site_specific_schema_key,
)


MEDIA_KEY_HINTS = (
    "image",
    "image_url",
    "background_image",
    "avatar",
    "poster",
    "photo",
    "src",
    "file",
)
MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".svg",
    ".gif",
    ".avif",
    ".mp4",
    ".webm",
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Command(BaseCommand):
    help = "Seed the Novaya Konakova public site into Yadro and import its media."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-content",
            action="store_true",
            help="Replace existing section content with seed values.",
        )
        parser.add_argument(
            "--public-dir",
            help="Path to volga frontend public directory. Defaults to ../volga/frontend/public.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        owner = self._resolve_owner()
        site = self._upsert_site(owner)
        public_dir = self._resolve_public_dir(options.get("public_dir"))
        existing_by_hash = self._index_existing_media(site)

        imported = 0
        reused = 0
        for seed in VOLGA_SECTION_SEEDS:
            schema = deepcopy(seed["schema"])
            content, stats = self._hydrate_media(
                site=site,
                section_key=seed["key"],
                payload=deepcopy(seed["content"]),
                public_dir=public_dir,
                existing_by_hash=existing_by_hash,
            )
            imported += stats["imported"]
            reused += stats["reused"]

            SectionSchema.objects.update_or_create(
                section_key=get_site_specific_schema_key(seed["key"], site.slug),
                defaults={
                    "title": seed["title"],
                    "schema": schema,
                    "description": f"Поля раздела «{seed['title']}» сайта {site.name}",
                },
            )

            section, created = SiteSection.objects.get_or_create(
                site=site,
                key=seed["key"],
                defaults={
                    "title": seed["title"],
                    "section_type": seed["key"],
                    "order": seed["order"],
                    "is_active": True,
                    "schema": schema,
                    "content": content,
                    "component_key": f"{seed['key']}-section",
                    "settings": {},
                    "seo": {},
                },
            )
            if created:
                continue

            section.title = seed["title"]
            section.section_type = seed["key"]
            section.order = seed["order"]
            section.is_active = True
            section.schema = schema
            section.content = content if options["force_content"] else merge_content_defaults(content, section.content)
            section.component_key = section.component_key or f"{seed['key']}-section"
            section.settings = section.settings if isinstance(section.settings, dict) else {}
            section.seo = section.seo if isinstance(section.seo, dict) else {}
            section.save()

        self.stdout.write(self.style.SUCCESS("seed_volga_site completed."))
        self.stdout.write(f"site={site.slug}")
        self.stdout.write(f"owner={owner.email or owner.username}")
        self.stdout.write(f"public_dir={public_dir}")
        self.stdout.write(f"media_imported={imported}")
        self.stdout.write(f"media_reused={reused}")

    def _resolve_owner(self):
        user_model = get_user_model()
        email = (
            os.getenv("VOLGA_SITE_OWNER_EMAIL", "").strip().lower()
            or os.getenv("SUPERUSER_EMAIL", "").strip().lower()
        )
        password = os.getenv("VOLGA_SITE_OWNER_PASSWORD", "") or os.getenv("SUPERUSER_PASSWORD", "")
        username = os.getenv("VOLGA_SITE_OWNER_USERNAME", "").strip() or email or "volga-owner"

        user = None
        if email:
            user = user_model.objects.filter(email__iexact=email).order_by("id").first()

        if user is None and email and password:
            user = user_model.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=False,
            )

        if user is None:
            user = (
                user_model.objects.filter(is_superuser=True).order_by("id").first()
                or user_model.objects.filter(is_staff=True).order_by("id").first()
                or user_model.objects.order_by("id").first()
            )

        if user is None:
            raise CommandError(
                "No user exists for Site.owner. Create an admin user or set "
                "VOLGA_SITE_OWNER_EMAIL and VOLGA_SITE_OWNER_PASSWORD."
            )
        return user

    def _upsert_site(self, owner):
        site_slug = os.getenv("VOLGA_SITE_SLUG", VOLGA_SITE_SLUG).strip() or VOLGA_SITE_SLUG
        domain = os.getenv("VOLGA_SITE_DOMAIN", VOLGA_SITE_DOMAIN).strip()
        site_name = os.getenv("VOLGA_SITE_NAME", VOLGA_SITE_NAME).strip() or VOLGA_SITE_NAME

        site, _ = Site.objects.update_or_create(
            slug=site_slug,
            defaults={
                "name": site_name,
                "domain": domain,
                "owner": owner,
                "is_active": True,
                "seo": {
                    "title": "Новое Конаково — отдых на природе, экскурсии и мероприятия",
                    "description": (
                        "Новое Конаково — природный отдых, экскурсии, мероприятия, "
                        "расписание и статьи."
                    ),
                    "keywords": "Новое Конаково, отдых, природа, экскурсии, мероприятия",
                },
            },
        )
        return site

    def _resolve_public_dir(self, requested):
        if requested:
            public_dir = Path(requested)
        else:
            backend_root = Path(__file__).resolve().parents[4]
            public_dir = backend_root.parent / "volga" / "frontend" / "public"

        public_dir = public_dir.resolve()
        if not public_dir.exists() or not public_dir.is_dir():
            raise CommandError(f"Volga public directory was not found: {public_dir}")
        return public_dir

    def _index_existing_media(self, site):
        indexed = {}
        for media in MediaFile.objects.filter(site=site).exclude(file="").order_by("id"):
            try:
                source_path = Path(media.file.path)
            except (NotImplementedError, ValueError):
                continue
            if not source_path.exists():
                continue
            checksum = media.checksum_sha256 or file_sha256(source_path)
            if not media.checksum_sha256:
                MediaFile.objects.filter(pk=media.pk).update(checksum_sha256=checksum)
                media.checksum_sha256 = checksum
            indexed.setdefault(checksum, media)
        return indexed

    def _hydrate_media(self, *, site, section_key, payload, public_dir, existing_by_hash):
        stats = {"imported": 0, "reused": 0}

        def walk(value, key_path=""):
            if isinstance(value, list):
                return [walk(item, key_path) for item in value]
            if isinstance(value, dict):
                return {key: walk(item, f"{key_path}.{key}" if key_path else key) for key, item in value.items()}
            if isinstance(value, str) and self._looks_like_local_media(value, key_path):
                media_path, status = self._copy_media(
                    site=site,
                    section_key=section_key,
                    field_key=key_path,
                    asset_path=value,
                    public_dir=public_dir,
                    existing_by_hash=existing_by_hash,
                )
                if status:
                    stats[status] += 1
                return media_path
            return value

        return walk(payload), stats

    def _looks_like_local_media(self, value, key_path):
        raw = str(value or "").strip()
        if not raw or not raw.startswith("/") or raw.startswith("/media/"):
            return False
        if raw.startswith("//"):
            return False
        suffix = Path(raw.split("?", 1)[0]).suffix.lower()
        if suffix in MEDIA_EXTENSIONS:
            return True
        key = key_path.lower().split(".")[-1]
        return any(marker in key for marker in MEDIA_KEY_HINTS)

    def _copy_media(self, *, site, section_key, field_key, asset_path, public_dir, existing_by_hash):
        source = (public_dir / asset_path.lstrip("/")).resolve()
        try:
            source.relative_to(public_dir)
        except ValueError:
            return asset_path, None
        if not source.exists() or not source.is_file():
            return asset_path, None

        checksum = file_sha256(source)
        existing = existing_by_hash.get(checksum)
        if existing is not None:
            return existing.get_relative_media_path(), "reused"

        media_root = Path(settings.MEDIA_ROOT).resolve()
        target_dir = media_root / "sites" / site.slug / section_key
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if not target.exists() or source.stat().st_size != target.stat().st_size:
            shutil.copy2(source, target)

        relative_name = target.relative_to(media_root).as_posix()
        mime_type = mimetypes.guess_type(source.name)[0] or ""
        file_type = "video" if mime_type.startswith("video/") else "image"

        media = MediaFile.objects.create(
            site=site,
            section_key=section_key,
            field_key=field_key[:255],
            original_name=source.name,
            file=relative_name,
            file_type=file_type,
            title=source.stem,
            alt_text=source.stem,
            description=f"{section_key}:{field_key}",
            size=source.stat().st_size,
            mime_type=mime_type,
            checksum_sha256=checksum,
        )
        existing_by_hash[checksum] = media
        return media.get_relative_media_path(), "imported"
