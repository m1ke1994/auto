from copy import deepcopy
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.sites.models import Site, SiteSection
from apps.sites.volga_site import VOLGA_SECTION_SEEDS, VOLGA_SITE_DOMAIN, VOLGA_SITE_NAME, VOLGA_SITE_SLUG


SEEDS_BY_KEY = {seed["key"]: seed for seed in VOLGA_SECTION_SEEDS}
MEDIA_KEYS = {
    "avatar",
    "background_image",
    "gallery",
    "hero_image",
    "image",
    "image_url",
    "images",
    "preview_image",
    "video_url",
}


def collect_media_values(value, key=""):
    values = set()
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            values.update(collect_media_values(child_value, child_key))
    elif isinstance(value, list):
        for child_value in value:
            values.update(collect_media_values(child_value, key))
    elif key in MEDIA_KEYS and isinstance(value, str) and value:
        values.add(value)
    return values


class ImportVolgaTextContentTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="volga-owner",
            email="volga@example.com",
            password="test-test",
        )
        self.target_site = Site.objects.create(
            name=VOLGA_SITE_NAME,
            slug=VOLGA_SITE_SLUG,
            domain=VOLGA_SITE_DOMAIN,
            owner=self.owner,
        )
        self.meditation_site = Site.objects.create(
            name="A Meditation",
            slug="a-meditation",
            domain="leelabird.ru",
            owner=self.owner,
        )
        self.meditation_hero = SiteSection.objects.create(
            site=self.meditation_site,
            key="hero",
            title="Hero",
            section_type="hero",
            schema={
                "fields": [
                    {"key": "title", "type": "text"},
                    {"key": "description", "type": "textarea"},
                    {"key": "background_image", "type": "image"},
                    {"key": "avatar", "type": "image"},
                ]
            },
            content={
                "title": "A Meditation",
                "description": "Protected",
                "background_image": "/protected/background.jpg",
                "avatar": "/protected/avatar.jpg",
            },
        )

    def create_volga_sections(self, keys=None):
        keys = keys or SEEDS_BY_KEY.keys()
        sections = {}
        for key in keys:
            seed = SEEDS_BY_KEY[key]
            sections[key] = SiteSection.objects.create(
                site=self.target_site,
                key=key,
                title=seed["title"],
                section_type=key,
                order=seed["order"],
                schema=deepcopy(seed["schema"]),
                content=deepcopy(seed["content"]),
            )
        return sections

    def test_dry_run_supports_utf8_bom_semicolon_and_multiline_text(self):
        hero = self.create_volga_sections({"hero"})["hero"]
        original_content = deepcopy(hero.content)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "01_hero.csv").write_text(
                "\ufeffid;title;description;background_image;avatar\n"
                '1;"Лиза из CSV";"Первая строка\nВторая строка";ignored.jpg;ignored-avatar.jpg\n',
                encoding="utf-8",
            )
            output = StringIO()
            call_command(
                "import_volga_text_content",
                source=source,
                dry_run=True,
                stdout=output,
            )

            hero.refresh_from_db()
            self.assertEqual(hero.content, original_content)
            self.assertIn("DRY RUN", output.getvalue())

            call_command("import_volga_text_content", source=source, stdout=StringIO())
            hero.refresh_from_db()
            self.assertEqual(hero.content["title"], "Лиза из CSV")
            self.assertEqual(hero.content["description"].splitlines(), ["Первая строка", "Вторая строка"])
            self.assertEqual(hero.content["background_image"], original_content["background_image"])
            self.assertEqual(hero.content["avatar"], original_content["avatar"])

            call_command("import_volga_text_content", source=source, stdout=StringIO())
            self.assertEqual(
                SiteSection.objects.filter(site=self.target_site, key="hero").count(),
                1,
            )

        self.meditation_hero.refresh_from_db()
        self.assertEqual(self.meditation_hero.content["title"], "A Meditation")

    def test_missing_section_aborts_before_any_content_is_saved(self):
        hero = self.create_volga_sections({"hero"})["hero"]
        original_content = deepcopy(hero.content)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "01_hero.csv").write_text(
                "id,title,description,background_image,avatar\n"
                "1,Changed,Changed,ignored.jpg,ignored-avatar.jpg\n",
                encoding="utf-8",
            )
            (source / "04_news.csv").write_text(
                "id,title,slug,description,image,published_date,content\n"
                '1,News,news,Description,ignored.jpg,2026-01-01,"[""Body""]"\n',
                encoding="utf-8",
            )

            with self.assertRaisesMessage(CommandError, "missing required sections: news"):
                call_command("import_volga_text_content", source=source, stdout=StringIO())

        hero.refresh_from_db()
        self.assertEqual(hero.content, original_content)

    def test_a_meditation_is_explicitly_rejected(self):
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "01_hero.csv").write_text(
                "id,title,description,background_image,avatar\n"
                "1,Changed,Changed,ignored.jpg,ignored-avatar.jpg\n",
                encoding="utf-8",
            )
            with self.assertRaisesMessage(CommandError, "protected"):
                call_command(
                    "import_volga_text_content",
                    source=source,
                    site_slug="a-meditation",
                    stdout=StringIO(),
                )

        self.meditation_hero.refresh_from_db()
        self.assertEqual(self.meditation_hero.content["title"], "A Meditation")

    def test_full_export_import_is_idempotent_and_preserves_current_media(self):
        sections = self.create_volga_sections()
        before_media = set()
        for section in sections.values():
            before_media.update(collect_media_values(section.content))
        meditation_before = deepcopy(self.meditation_hero.content)
        source = Path(settings.BASE_DIR) / "export_content"
        self.assertTrue(source.is_dir(), "Packaged export_content fixture is missing")

        before_dry_run = {key: deepcopy(section.content) for key, section in sections.items()}
        call_command(
            "import_volga_text_content",
            source=source,
            dry_run=True,
            stdout=StringIO(),
        )
        for key, section in sections.items():
            section.refresh_from_db()
            self.assertEqual(section.content, before_dry_run[key])

        call_command("import_volga_text_content", source=source, stdout=StringIO())
        for section in sections.values():
            section.refresh_from_db()

        self.assertEqual(sections["hero"].content["title"], "Лиза Стручкова")
        self.assertIn("Я переехала из Москвы", sections["hero"].content["description"])

        services = sections["services"].content["items_json"]
        self.assertEqual(len(services), 7)
        self.assertEqual(len(services) + sum(len(item["children"]) for item in services), 13)
        self.assertEqual(
            sum(len(item["tariffs"]) for item in services)
            + sum(len(child["tariffs"]) for item in services for child in item["children"]),
            22,
        )

        schedule = sections["schedule"].content["items_json"]
        schedule_days = [day for month in schedule for day in month["days"]]
        self.assertEqual(len(schedule_days), 90)
        self.assertEqual(sum(len(day["events"]) for day in schedule_days), 184)
        self.assertEqual(len(sections["reviews"].content["items_json"]), 5)
        self.assertEqual(len(sections["articles"].content["items_json"]), 5)
        self.assertEqual(len(sections["news"].content["items_json"]), 5)
        self.assertEqual(len(sections["pages"].content["items_json"]), 4)

        after_media = set()
        for section in sections.values():
            after_media.update(collect_media_values(section.content))
        self.assertTrue(before_media.issubset(after_media), before_media - after_media)
        self.assertNotIn("news/100.webp", after_media)
        self.assertNotIn("articles/1.png", after_media)

        first_import = {key: deepcopy(section.content) for key, section in sections.items()}
        updated_at = {key: section.updated_at for key, section in sections.items()}
        call_command("import_volga_text_content", source=source, stdout=StringIO())
        for key, section in sections.items():
            section.refresh_from_db()
            self.assertEqual(section.content, first_import[key])
            self.assertEqual(section.updated_at, updated_at[key])

        self.meditation_hero.refresh_from_db()
        self.assertEqual(self.meditation_hero.content, meditation_before)
