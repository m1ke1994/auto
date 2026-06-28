import csv
import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import date, time
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from apps.sites.models import Site, SiteSection
from apps.sites.volga_site import VOLGA_SITE_DOMAIN, VOLGA_SITE_NAME, VOLGA_SITE_SLUG


CSV_HEADERS = {
    "01_hero.csv": {"id", "title", "description", "background_image", "avatar"},
    "02_services.csv": {
        "id",
        "title",
        "slug",
        "description",
        "is_category",
        "order",
        "parent_id",
    },
    "03_tariffs.csv": {
        "id",
        "title",
        "slug",
        "description",
        "duration",
        "price",
        "order",
        "service_id",
    },
    "04_news.csv": {
        "id",
        "title",
        "slug",
        "description",
        "image",
        "published_date",
        "content",
    },
    "05_articles.csv": {
        "id",
        "title",
        "slug",
        "preview_image",
        "preview_description",
        "content",
        "content_type",
        "video_url",
        "published_date",
        "created_at",
    },
    "06_reviews.csv": {"id", "avatar", "name", "event_name", "rating", "text", "date"},
    "07_schedule_days.csv": {"id", "date", "title", "is_published"},
    "08_schedule_events.csv": {
        "id",
        "title",
        "category",
        "description",
        "time_start",
        "time_end",
        "price",
        "color",
        "order",
        "day_id",
        "image",
    },
    "09_schedule_items.csv": {
        "id",
        "time",
        "title",
        "description",
        "capacity",
        "is_active",
        "day_id",
        "service_id",
        "category",
        "price",
        "time_end",
    },
    "10_pages.csv": {"id", "title", "slug", "subtitle", "hero_image", "order"},
    "11_page_sections.csv": {"id", "title", "text", "image", "order", "page_id"},
    "12_page_gallery.csv": {"id", "image", "order", "page_id"},
}

SECTION_FILES = {
    "hero": {"01_hero.csv"},
    "services": {"02_services.csv", "03_tariffs.csv"},
    "schedule": {"07_schedule_days.csv", "08_schedule_events.csv", "09_schedule_items.csv"},
    "reviews": {"06_reviews.csv"},
    "articles": {"05_articles.csv"},
    "news": {"04_news.csv"},
    "pages": {"10_pages.csv", "11_page_sections.csv", "12_page_gallery.csv"},
}

SECTION_TEXT_FIELDS = {
    "hero": "title, description",
    "services": "title, description, tariffs[].title, tariffs[].description, tariffs[].duration",
    "schedule": "month, weekday, title, category, description",
    "reviews": "name, event_name, text",
    "articles": "title, preview_description, content",
    "news": "title, description, content",
    "pages": "title, subtitle, sections[].title, sections[].text",
}

TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}
PROTECTED_SITE_SLUGS = {"a-meditation", "amedia"}
PROTECTED_SITE_DOMAINS = {"leelabird.ru"}

MONTH_NAMES_RU = (
    "",
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
)
WEEKDAY_NAMES_RU = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
)

# The initial Yadro seed used four temporary service identifiers. These aliases let
# the importer retain their already uploaded media while replacing placeholder text.
SERVICE_SEED_ALIASES = {
    "34": {"moose"},
    "35": {"running"},
    "37": {"master"},
    "43": {"author"},
}


def normalize_identity(value):
    value = str(value or "").strip().casefold().replace("ё", "е")
    return re.sub(r"[^0-9a-zа-я]+", "", value)


class Command(BaseCommand):
    help = "Import Novaya Konakova text content from the legacy Export Content CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--site-slug",
            default=VOLGA_SITE_SLUG,
            help=f"Target site slug (default: {VOLGA_SITE_SLUG}).",
        )
        parser.add_argument(
            "--source",
            default="export_content",
            help="Directory containing Export Content CSV files (default: export_content).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report changes without writing to the database.",
        )

    def handle(self, *args, **options):
        self.empty_values = 0
        self.skipped = []
        self.section_reports = []

        source_dir = self._resolve_source_dir(options["source"])
        rows_by_file, found_files, unrecognized_files = self._read_source(source_dir)
        if not found_files:
            raise CommandError(f"No CSV files were found in source directory: {source_dir}")

        required_sections = self._required_sections(rows_by_file)
        dry_run = options["dry_run"]

        with transaction.atomic():
            site = self._resolve_site(options["site_slug"])
            sections = self._load_sections(site, required_sections)

            builders = {
                "hero": self._build_hero,
                "services": self._build_services,
                "schedule": self._build_schedule,
                "reviews": self._build_reviews,
                "articles": self._build_articles,
                "news": self._build_news,
                "pages": self._build_pages,
            }

            for section_key in (
                "hero",
                "services",
                "schedule",
                "reviews",
                "articles",
                "news",
                "pages",
            ):
                if section_key not in required_sections:
                    continue

                section = sections[section_key]
                content, item_count = builders[section_key](deepcopy(section.content), rows_by_file)
                try:
                    SiteSection.validate_content(content, section.schema)
                except ValidationError as exc:
                    raise CommandError(f"Invalid generated content for section '{section_key}': {exc}") from exc

                changed = content != section.content
                self.section_reports.append(
                    {
                        "key": section_key,
                        "changed": changed,
                        "fields": SECTION_TEXT_FIELDS[section_key],
                        "items": item_count,
                    }
                )
                if changed and not dry_run:
                    section.content = content
                    section.save(update_fields=["content", "updated_at"])

        self._write_report(
            site=site,
            source_dir=source_dir,
            found_files=found_files,
            unrecognized_files=unrecognized_files,
            rows_by_file=rows_by_file,
            dry_run=dry_run,
        )

    def _resolve_source_dir(self, requested):
        requested_path = Path(requested).expanduser()
        if requested_path.is_absolute():
            candidates = [requested_path]
        else:
            candidates = [
                Path.cwd() / requested_path,
                Path(settings.BASE_DIR) / requested_path,
                Path(settings.BASE_DIR).parent / requested_path,
            ]

        checked = []
        seen = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            checked.append(resolved)
            if resolved.is_dir():
                return resolved

        paths = "\n".join(f"- {path}" for path in checked)
        raise CommandError(f"Source directory was not found. Checked:\n{paths}")

    def _read_source(self, source_dir):
        csv_files = sorted(source_dir.glob("*.csv"), key=lambda path: path.name)
        found_files = [path.name for path in csv_files]
        unrecognized_files = [name for name in found_files if name not in CSV_HEADERS]
        rows_by_file = {}

        for path in csv_files:
            if path.name not in CSV_HEADERS:
                continue
            rows_by_file[path.name] = self._read_csv(path, CSV_HEADERS[path.name])

        return rows_by_file, found_files, unrecognized_files

    def _read_csv(self, path, required_headers):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                sample = handle.read(8192)
                handle.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;")
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ";" if sample.count(";") > sample.count(",") else ","

                reader = csv.DictReader(handle, delimiter=delimiter)
                if reader.fieldnames is None:
                    raise CommandError(f"CSV has no header: {path.name}")

                original_headers = reader.fieldnames
                normalized_headers = [header.lstrip("\ufeff").strip() for header in original_headers]
                if len(set(normalized_headers)) != len(normalized_headers):
                    raise CommandError(f"CSV has duplicate columns: {path.name}")

                missing = required_headers - set(normalized_headers)
                if missing:
                    missing_list = ", ".join(sorted(missing))
                    raise CommandError(f"CSV {path.name} is missing required columns: {missing_list}")

                rows = []
                for line_number, raw_row in enumerate(reader, start=2):
                    if None in raw_row:
                        raise CommandError(f"Malformed row in {path.name}:{line_number}")
                    row = {
                        normalized: raw_row.get(original, "") or ""
                        for original, normalized in zip(original_headers, normalized_headers)
                    }
                    if not any(str(value).strip() for value in row.values()):
                        self.skipped.append(f"{path.name}:{line_number}: blank row")
                        continue
                    row["__line__"] = line_number
                    rows.append(row)
                return rows
        except UnicodeDecodeError as exc:
            raise CommandError(f"CSV is not valid UTF-8/UTF-8 BOM: {path.name}") from exc

    def _required_sections(self, rows_by_file):
        required = set()
        for section_key, filenames in SECTION_FILES.items():
            if filenames & rows_by_file.keys():
                required.add(section_key)

        # Image-only page gallery data cannot change the text section by itself.
        if required == {"pages"} and not (
            {"10_pages.csv", "11_page_sections.csv"} & rows_by_file.keys()
        ):
            required.remove("pages")
        return required

    def _resolve_site(self, requested_slug):
        requested_slug = (requested_slug or "").strip()
        if not requested_slug:
            raise CommandError("--site-slug cannot be empty.")
        if requested_slug.casefold() in PROTECTED_SITE_SLUGS:
            raise CommandError("A Meditation / Amedia is protected and cannot be targeted by this command.")

        queryset = Site.objects.select_for_update()
        site = queryset.filter(slug=requested_slug).first()
        if site is None and requested_slug == VOLGA_SITE_SLUG:
            candidates = list(
                queryset.filter(Q(name=VOLGA_SITE_NAME) | Q(domain__iexact=VOLGA_SITE_DOMAIN)).order_by("id")[:2]
            )
            if len(candidates) > 1:
                raise CommandError("More than one site matches the Novaya Konakova name/domain fallback.")
            site = candidates[0] if candidates else None

        if site is None:
            raise CommandError(f"Target site was not found: slug={requested_slug!r}")

        domain = (site.domain or "").strip().casefold()
        if site.slug.casefold() in PROTECTED_SITE_SLUGS or domain in PROTECTED_SITE_DOMAINS:
            raise CommandError("A Meditation / Amedia is protected and cannot be targeted by this command.")

        is_volga_site = (
            site.slug == VOLGA_SITE_SLUG
            or site.name == VOLGA_SITE_NAME
            or domain == VOLGA_SITE_DOMAIN.casefold()
        )
        if not is_volga_site:
            raise CommandError(
                f"Refusing to import Volga content into unrelated site: {site.name} / {site.slug} / {site.domain}"
            )
        return site

    def _load_sections(self, site, required_sections):
        sections = {
            section.key: section
            for section in SiteSection.objects.select_for_update().filter(
                site=site,
                key__in=required_sections,
            )
        }
        missing = required_sections - sections.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise CommandError(
                f"Target site is missing required sections: {missing_list}. "
                "Run seed_volga_site first; this command does not create sections."
            )
        return sections

    def _text(self, row, key, fallback=""):
        value = row.get(key, "")
        if not str(value).strip():
            self.empty_values += 1
            return fallback
        return value

    def _required_value(self, row, key, filename):
        value = str(row.get(key, "")).strip()
        if not value:
            line = row.get("__line__", "?")
            raise CommandError(f"{filename}:{line}: required value '{key}' is empty")
        return value

    def _integer(self, row, key, filename, fallback=0, minimum=None, maximum=None):
        raw_value = str(row.get(key, "")).strip()
        if not raw_value:
            return fallback
        try:
            value = int(raw_value)
        except ValueError as exc:
            line = row.get("__line__", "?")
            raise CommandError(f"{filename}:{line}: '{key}' must be an integer") from exc
        if minimum is not None and value < minimum or maximum is not None and value > maximum:
            line = row.get("__line__", "?")
            raise CommandError(f"{filename}:{line}: '{key}' is outside the allowed range")
        return value

    def _boolean(self, row, key, filename, fallback=False):
        raw_value = str(row.get(key, "")).strip().casefold()
        if not raw_value:
            return fallback
        if raw_value in TRUE_VALUES:
            return True
        if raw_value in FALSE_VALUES:
            return False
        line = row.get("__line__", "?")
        raise CommandError(f"{filename}:{line}: '{key}' must be a boolean")

    def _unique_rows(self, rows, key, filename):
        indexed = {}
        for row in rows:
            value = self._required_value(row, key, filename)
            if value in indexed:
                line = row.get("__line__", "?")
                raise CommandError(f"{filename}:{line}: duplicate {key}={value!r}")
            indexed[value] = row
        return indexed

    def _take_existing(
        self,
        pool,
        used,
        candidates,
        *,
        fallback_index=None,
        predicate=None,
        fallback_any=True,
    ):
        normalized_candidates = {normalize_identity(value) for value in candidates if value not in (None, "")}
        normalized_candidates.discard("")

        for index, item in enumerate(pool):
            if index in used or not isinstance(item, dict):
                continue
            if predicate is not None and not predicate(item):
                continue
            identities = {
                normalize_identity(item.get(key))
                for key in ("id", "slug", "title", "name")
                if item.get(key) not in (None, "")
            }
            if normalized_candidates & identities:
                used.add(index)
                return item

        if fallback_index is not None and fallback_index < len(pool) and fallback_index not in used:
            item = pool[fallback_index]
            if isinstance(item, dict) and (predicate is None or predicate(item)):
                used.add(fallback_index)
                return item

        if not fallback_any:
            return {}

        for index, item in enumerate(pool):
            if index in used or not isinstance(item, dict):
                continue
            if predicate is None or predicate(item):
                used.add(index)
                return item
        return {}

    def _build_hero(self, content, rows_by_file):
        rows = rows_by_file.get("01_hero.csv", [])
        if not rows:
            self.skipped.append("01_hero.csv: no data rows")
            return content, 0
        if len(rows) > 1:
            raise CommandError("01_hero.csv must contain exactly one data row.")

        row = rows[0]
        content["title"] = self._text(row, "title", content.get("title", ""))
        content["description"] = self._text(row, "description", content.get("description", ""))
        # background_image and avatar are intentionally retained from current content.
        return content, 1

    def _build_services(self, content, rows_by_file):
        filename = "02_services.csv"
        rows = rows_by_file.get(filename, [])
        if not rows:
            self.skipped.append(f"{filename}: no data rows")
            return content, 0

        rows_by_id = self._unique_rows(rows, "id", filename)
        self._unique_rows(rows, "slug", filename)
        tariff_filename = "03_tariffs.csv"
        tariff_rows = rows_by_file.get(tariff_filename, [])
        self._unique_rows(tariff_rows, "id", tariff_filename)
        tariffs_by_service = defaultdict(list)
        for tariff_row in tariff_rows:
            service_id = self._required_value(tariff_row, "service_id", tariff_filename)
            if service_id not in rows_by_id:
                self.skipped.append(
                    f"{tariff_filename}:{tariff_row['__line__']}: unknown service_id={service_id}"
                )
                continue
            tariffs_by_service[service_id].append(tariff_row)

        parent_children = defaultdict(list)
        top_level_rows = []
        for row in rows:
            parent_id = str(row.get("parent_id", "")).strip()
            if not parent_id:
                top_level_rows.append(row)
            elif parent_id not in rows_by_id:
                self.skipped.append(f"{filename}:{row['__line__']}: unknown parent_id={parent_id}")
            else:
                parent_children[parent_id].append(row)

        top_level_ids = {self._required_value(row, "id", filename) for row in top_level_rows}
        for parent_id in list(parent_children):
            if parent_id in top_level_ids:
                continue
            for child in parent_children.pop(parent_id):
                self.skipped.append(
                    f"{filename}:{child['__line__']}: nested or cyclic parent_id={parent_id} is unsupported"
                )

        for service_id, service_tariffs in tariffs_by_service.items():
            self._unique_rows(service_tariffs, "slug", tariff_filename)

        sort_key = lambda row: (
            self._integer(row, "order", filename, fallback=0),
            self._integer(row, "id", filename, fallback=0),
        )
        top_level_rows.sort(key=sort_key)
        for children in parent_children.values():
            children.sort(key=sort_key)
        for tariffs in tariffs_by_service.values():
            tariffs.sort(
                key=lambda row: (
                    self._integer(row, "order", tariff_filename, fallback=0),
                    self._integer(row, "id", tariff_filename, fallback=0),
                )
            )

        existing_top = content.get("items_json", [])
        existing_pool = []
        for item in existing_top if isinstance(existing_top, list) else []:
            if not isinstance(item, dict):
                continue
            existing_pool.append(item)
            existing_pool.extend(child for child in item.get("children", []) if isinstance(child, dict))
        used_existing = set()

        def build_service(row, *, include_children):
            source_id = self._required_value(row, "id", filename)
            candidates = {
                source_id,
                row.get("slug"),
                row.get("title"),
                *SERVICE_SEED_ALIASES.get(source_id, set()),
            }
            existing = self._take_existing(
                existing_pool,
                used_existing,
                candidates,
                fallback_any=False,
            )
            title = self._text(row, "title", existing.get("title", ""))

            existing_tariffs = existing.get("tariffs", []) if isinstance(existing.get("tariffs"), list) else []
            used_tariffs = set()
            built_tariffs = []
            for tariff_index, tariff_row in enumerate(tariffs_by_service.get(source_id, [])):
                tariff_existing = self._take_existing(
                    existing_tariffs,
                    used_tariffs,
                    {tariff_row.get("id"), tariff_row.get("slug"), tariff_row.get("title")},
                    fallback_index=tariff_index,
                )
                built_tariffs.append(
                    {
                        "id": self._required_value(tariff_row, "id", tariff_filename),
                        "slug": self._text(tariff_row, "slug", tariff_existing.get("slug", "")),
                        "title": self._text(tariff_row, "title", tariff_existing.get("title", "")),
                        "description": self._text(
                            tariff_row,
                            "description",
                            tariff_existing.get("description", ""),
                        ),
                        "duration": self._text(
                            tariff_row,
                            "duration",
                            tariff_existing.get("duration", ""),
                        ),
                        "price": self._integer(
                            tariff_row,
                            "price",
                            tariff_filename,
                            fallback=tariff_existing.get("price", 0),
                        ),
                        "order": self._integer(
                            tariff_row,
                            "order",
                            tariff_filename,
                            fallback=tariff_existing.get("order", 0),
                        ),
                    }
                )

            service = {
                "id": source_id,
                "slug": self._text(row, "slug", existing.get("slug", "")),
                "title": title,
                "full_title": existing.get("full_title") or title,
                "description": self._text(row, "description", existing.get("description", "")),
                "duration_label": existing.get("duration_label", ""),
                "intro": existing.get("intro", ""),
                "note": existing.get("note", ""),
                "image": existing.get("image", ""),
                "order": self._integer(row, "order", filename, fallback=existing.get("order", 0)),
                "is_category": self._boolean(
                    row,
                    "is_category",
                    filename,
                    fallback=existing.get("is_category", False),
                ),
                "images": deepcopy(existing.get("images", [])),
                "content_sections": deepcopy(existing.get("content_sections", [])),
                "tariffs": built_tariffs,
            }
            if include_children:
                service["children"] = [
                    build_service(child, include_children=False)
                    for child in parent_children.get(source_id, [])
                ]
            return service

        content["items_json"] = [build_service(row, include_children=True) for row in top_level_rows]
        return content, len(rows)

    def _build_reviews(self, content, rows_by_file):
        filename = "06_reviews.csv"
        rows = rows_by_file.get(filename, [])
        self._unique_rows(rows, "id", filename)
        existing_items = content.get("items_json", []) if isinstance(content.get("items_json"), list) else []
        used = set()
        items = []

        for index, row in enumerate(rows):
            source_id = self._required_value(row, "id", filename)
            existing = self._take_existing(
                existing_items,
                used,
                {source_id, row.get("name"), row.get("event_name")},
                fallback_index=index,
            )
            items.append(
                {
                    "id": source_id,
                    "name": self._text(row, "name", existing.get("name", "")),
                    "event_name": self._text(row, "event_name", existing.get("event_name", "")),
                    "rating": self._integer(
                        row,
                        "rating",
                        filename,
                        fallback=existing.get("rating", 5),
                        minimum=1,
                        maximum=5,
                    ),
                    "text": self._text(row, "text", existing.get("text", "")),
                    "date": self._text(row, "date", existing.get("date", "")),
                    "avatar": existing.get("avatar", ""),
                }
            )
        content["items_json"] = items
        if not rows:
            self.skipped.append(f"{filename}: no data rows")
        return content, len(items)

    def _build_articles(self, content, rows_by_file):
        filename = "05_articles.csv"
        rows = rows_by_file.get(filename, [])
        self._unique_rows(rows, "slug", filename)
        existing_items = content.get("items_json", []) if isinstance(content.get("items_json"), list) else []
        used = set()
        items = []

        for index, row in enumerate(rows):
            content_type = str(row.get("content_type", "")).strip() or "article"
            if content_type not in {"article", "video"}:
                line = row.get("__line__", "?")
                raise CommandError(f"{filename}:{line}: unsupported content_type={content_type!r}")
            existing = self._take_existing(
                existing_items,
                used,
                {row.get("slug"), row.get("title")},
                fallback_index=index,
                predicate=lambda item, expected=content_type: item.get("content_type", "article") == expected,
            )
            if not existing:
                existing = self._take_existing(
                    existing_items,
                    used,
                    {row.get("slug"), row.get("title")},
                    fallback_index=index,
                )
            items.append(
                {
                    "title": self._text(row, "title", existing.get("title", "")),
                    "slug": self._required_value(row, "slug", filename),
                    "preview_image": existing.get("preview_image", ""),
                    "preview_description": self._text(
                        row,
                        "preview_description",
                        existing.get("preview_description", ""),
                    ),
                    "content": self._text(row, "content", existing.get("content", "")),
                    "content_type": content_type,
                    # A video URL is media content and is deliberately not imported from CSV.
                    "video_url": existing.get("video_url", ""),
                    "published_date": self._text(
                        row,
                        "published_date",
                        existing.get("published_date", ""),
                    ),
                    "created_at": self._text(row, "created_at", existing.get("created_at", "")),
                }
            )
        content["items_json"] = items
        if not rows:
            self.skipped.append(f"{filename}: no data rows")
        return content, len(items)

    def _news_content(self, row, fallback):
        value = row.get("content", "")
        if not str(value).strip():
            self.empty_values += 1
            return fallback
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, str):
            return parsed
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            non_empty = [item for item in parsed if item.strip()]
            self.empty_values += len(parsed) - len(non_empty)
            return "\n\n".join(non_empty) if non_empty else fallback
        line = row.get("__line__", "?")
        raise CommandError(f"04_news.csv:{line}: content JSON must be a string or list of strings")

    def _build_news(self, content, rows_by_file):
        filename = "04_news.csv"
        rows = rows_by_file.get(filename, [])
        self._unique_rows(rows, "id", filename)
        self._unique_rows(rows, "slug", filename)
        existing_items = content.get("items_json", []) if isinstance(content.get("items_json"), list) else []
        used = set()
        items = []

        for index, row in enumerate(rows):
            source_id = self._integer(row, "id", filename, minimum=1)
            existing = self._take_existing(
                existing_items,
                used,
                {source_id, row.get("slug"), row.get("title")},
                fallback_index=index,
            )
            items.append(
                {
                    "id": source_id,
                    "title": self._text(row, "title", existing.get("title", "")),
                    "slug": self._required_value(row, "slug", filename),
                    "description": self._text(
                        row,
                        "description",
                        existing.get("description", ""),
                    ),
                    "image": existing.get("image", ""),
                    "published_date": self._text(
                        row,
                        "published_date",
                        existing.get("published_date", ""),
                    ),
                    "content": self._news_content(row, existing.get("content", "")),
                }
            )
        content["items_json"] = items
        if not rows:
            self.skipped.append(f"{filename}: no data rows")
        return content, len(items)

    def _parse_iso_date(self, row, key, filename):
        raw_value = self._required_value(row, key, filename)
        try:
            return date.fromisoformat(raw_value)
        except ValueError as exc:
            line = row.get("__line__", "?")
            raise CommandError(f"{filename}:{line}: '{key}' must use YYYY-MM-DD") from exc

    def _parse_time(self, row, key, filename):
        raw_value = self._required_value(row, key, filename)
        try:
            parsed = time.fromisoformat(raw_value)
        except ValueError as exc:
            line = row.get("__line__", "?")
            raise CommandError(f"{filename}:{line}: '{key}' is not a valid time") from exc
        return parsed.strftime("%H:%M")

    def _build_schedule(self, content, rows_by_file):
        day_filename = "07_schedule_days.csv"
        event_filename = "08_schedule_events.csv"
        legacy_filename = "09_schedule_items.csv"
        day_rows = rows_by_file.get(day_filename, [])
        event_rows = list(rows_by_file.get(event_filename, []))

        for legacy_row in rows_by_file.get(legacy_filename, []):
            if not self._boolean(legacy_row, "is_active", legacy_filename, fallback=True):
                self.skipped.append(f"{legacy_filename}:{legacy_row['__line__']}: inactive row")
                continue
            event_rows.append(
                {
                    "id": legacy_row.get("id", ""),
                    "title": legacy_row.get("title", ""),
                    "category": legacy_row.get("category", ""),
                    "description": legacy_row.get("description", ""),
                    "time_start": legacy_row.get("time", ""),
                    "time_end": legacy_row.get("time_end", ""),
                    "price": legacy_row.get("price", ""),
                    "color": "",
                    "order": "0",
                    "day_id": legacy_row.get("day_id", ""),
                    "image": "",
                    "__line__": legacy_row.get("__line__", "?"),
                    "__source__": legacy_filename,
                }
            )

        if event_rows and not day_rows:
            raise CommandError("Schedule events were provided without 07_schedule_days.csv data.")

        days_by_id = self._unique_rows(day_rows, "id", day_filename)
        self._unique_rows(day_rows, "date", day_filename)
        event_ids = set()
        events_by_day = defaultdict(list)
        for event_row in event_rows:
            source_name = event_row.get("__source__", event_filename)
            event_id = self._required_value(event_row, "id", source_name)
            if event_id in event_ids:
                line = event_row.get("__line__", "?")
                raise CommandError(f"{source_name}:{line}: duplicate id={event_id!r}")
            event_ids.add(event_id)
            day_id = self._required_value(event_row, "day_id", source_name)
            if day_id not in days_by_id:
                self.skipped.append(f"{source_name}:{event_row['__line__']}: unknown day_id={day_id}")
                continue
            events_by_day[day_id].append(event_row)

        existing_events = []
        existing_images_by_title = {}
        for month in content.get("items_json", []) if isinstance(content.get("items_json"), list) else []:
            for day_item in month.get("days", []) if isinstance(month, dict) else []:
                for event in day_item.get("events", []) if isinstance(day_item, dict) else []:
                    if not isinstance(event, dict):
                        continue
                    existing_events.append(event)
                    if event.get("image"):
                        existing_images_by_title.setdefault(normalize_identity(event.get("title")), event["image"])
        existing_by_id = {str(item.get("id")): item for item in existing_events if item.get("id") not in (None, "")}

        month_groups = defaultdict(list)
        event_count = 0
        for day_id, day_row in days_by_id.items():
            if not self._boolean(day_row, "is_published", day_filename, fallback=True):
                self.skipped.append(f"{day_filename}:{day_row['__line__']}: unpublished day")
                continue
            parsed_date = self._parse_iso_date(day_row, "date", day_filename)
            built_events = []
            sorted_event_rows = sorted(
                events_by_day.get(day_id, []),
                key=lambda row: (
                    self._parse_time(row, "time_start", row.get("__source__", event_filename)),
                    self._integer(
                        row,
                        "order",
                        row.get("__source__", event_filename),
                        fallback=0,
                    ),
                    str(row.get("id", "")),
                ),
            )
            for event_row in sorted_event_rows:
                source_name = event_row.get("__source__", event_filename)
                event_id = self._required_value(event_row, "id", source_name)
                existing = existing_by_id.get(event_id, {})
                title = self._text(event_row, "title", existing.get("title", ""))
                image = existing.get("image") or existing_images_by_title.get(normalize_identity(title), "")
                built_events.append(
                    {
                        "id": event_id,
                        "time_start": self._parse_time(event_row, "time_start", source_name),
                        "time_end": self._parse_time(event_row, "time_end", source_name),
                        "title": title,
                        "category": self._text(
                            event_row,
                            "category",
                            existing.get("category", ""),
                        ),
                        "description": self._text(
                            event_row,
                            "description",
                            existing.get("description", ""),
                        ),
                        "price": self._integer(
                            event_row,
                            "price",
                            source_name,
                            fallback=existing.get("price", 0),
                        ),
                        "color": self._text(event_row, "color", existing.get("color", "")),
                        "image": image,
                    }
                )
            event_count += len(built_events)
            month_groups[(parsed_date.year, parsed_date.month)].append(
                {
                    "date": parsed_date.isoformat(),
                    "weekday": WEEKDAY_NAMES_RU[parsed_date.weekday()],
                    "events": built_events,
                }
            )

        months = []
        for year, month_number in sorted(month_groups):
            months.append(
                {
                    "month": f"{MONTH_NAMES_RU[month_number]} {year}",
                    "year": year,
                    "month_number": month_number,
                    "days": sorted(month_groups[(year, month_number)], key=lambda item: item["date"]),
                }
            )
        content["items_json"] = months
        if not day_rows:
            self.skipped.append(f"{day_filename}: no data rows")
        if not event_rows:
            self.skipped.append("schedule events: no data rows")
        return content, event_count

    def _build_pages(self, content, rows_by_file):
        page_filename = "10_pages.csv"
        section_filename = "11_page_sections.csv"
        page_rows = rows_by_file.get(page_filename, [])
        section_rows = rows_by_file.get(section_filename, [])
        if not page_rows:
            self.skipped.append(f"{page_filename}: no data rows")
            return content, 0

        pages_by_id = self._unique_rows(page_rows, "id", page_filename)
        self._unique_rows(page_rows, "slug", page_filename)
        self._unique_rows(section_rows, "id", section_filename)
        sections_by_page = defaultdict(list)
        for section_row in section_rows:
            page_id = self._required_value(section_row, "page_id", section_filename)
            if page_id not in pages_by_id:
                self.skipped.append(
                    f"{section_filename}:{section_row['__line__']}: unknown page_id={page_id}"
                )
                continue
            sections_by_page[page_id].append(section_row)

        existing_pages = content.get("items_json", []) if isinstance(content.get("items_json"), list) else []
        used_pages = set()
        sorted_pages = sorted(
            page_rows,
            key=lambda row: (
                self._integer(row, "order", page_filename, fallback=0),
                self._integer(row, "id", page_filename, fallback=0),
            ),
        )
        items = []
        section_count = 0
        for page_index, row in enumerate(sorted_pages):
            page_id = self._required_value(row, "id", page_filename)
            existing = self._take_existing(
                existing_pages,
                used_pages,
                {row.get("slug"), row.get("title")},
                fallback_index=page_index,
            )
            existing_sections = (
                existing.get("sections", []) if isinstance(existing.get("sections"), list) else []
            )
            used_sections = set()
            built_sections = []
            sorted_sections = sorted(
                sections_by_page.get(page_id, []),
                key=lambda section_row: (
                    self._integer(section_row, "order", section_filename, fallback=0),
                    self._integer(section_row, "id", section_filename, fallback=0),
                ),
            )
            for section_index, section_row in enumerate(sorted_sections):
                section_existing = self._take_existing(
                    existing_sections,
                    used_sections,
                    {section_row.get("title")},
                    fallback_index=section_index,
                )
                built_sections.append(
                    {
                        "title": self._text(
                            section_row,
                            "title",
                            section_existing.get("title", ""),
                        ),
                        "text": self._text(
                            section_row,
                            "text",
                            section_existing.get("text", ""),
                        ),
                        "order": self._integer(
                            section_row,
                            "order",
                            section_filename,
                            fallback=section_existing.get("order", 0),
                        ),
                    }
                )
            section_count += len(built_sections)
            items.append(
                {
                    "slug": self._required_value(row, "slug", page_filename),
                    "title": self._text(row, "title", existing.get("title", "")),
                    "subtitle": self._text(row, "subtitle", existing.get("subtitle", "")),
                    "hero_image": existing.get("hero_image", ""),
                    "order": self._integer(
                        row,
                        "order",
                        page_filename,
                        fallback=existing.get("order", 0),
                    ),
                    "sections": built_sections,
                    # Page gallery CSV is image-only; retain the current gallery unchanged.
                    "gallery": deepcopy(existing.get("gallery", [])),
                }
            )
        content["items_json"] = items
        return content, len(items) + section_count

    def _write_report(
        self,
        *,
        site,
        source_dir,
        found_files,
        unrecognized_files,
        rows_by_file,
        dry_run,
    ):
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no database changes were written."))
        else:
            self.stdout.write(self.style.SUCCESS("Volga text content import completed."))
        self.stdout.write(f"Site: {site.name} / {site.slug}")
        self.stdout.write(f"Source: {source_dir}")
        self.stdout.write("CSV files:")
        for filename in found_files:
            if filename in rows_by_file:
                self.stdout.write(f"- {filename}: {len(rows_by_file[filename])} rows")
            else:
                self.stdout.write(f"- {filename}: unrecognized, skipped")

        self.stdout.write("Updated:" if not dry_run else "Planned:")
        if not self.section_reports:
            self.stdout.write("- none")
        for report in self.section_reports:
            status = "changed" if report["changed"] else "already up to date"
            self.stdout.write(
                f"- {report['key']}: {report['items']} items; fields={report['fields']}; {status}"
            )

        self.stdout.write("Skipped:")
        self.stdout.write("- images, avatars, galleries, preview images and video URLs: ignored by design")
        self.stdout.write(f"- empty text values: {self.empty_values}")
        if "12_page_gallery.csv" in rows_by_file:
            self.stdout.write("- 12_page_gallery.csv: image-only data retained from current site content")
        if unrecognized_files:
            self.stdout.write(f"- unrecognized CSV files: {', '.join(unrecognized_files)}")
        for message in self.skipped:
            self.stdout.write(f"- {message}")
