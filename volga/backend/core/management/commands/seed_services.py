import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import transaction

from core.models import Service, Tariff


class Command(BaseCommand):
    help = "Seed services and tariffs from converted frontend services seed data."

    def _load_seed(self):
        seed_path = Path(__file__).resolve().parents[2] / "data" / "services_seed.json"
        if not seed_path.exists():
            raise CommandError(f"Seed file not found: {seed_path}")
        try:
            return json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {seed_path}: {exc}") from exc

    def _create_service_tree(self, items, parent=None):
        created_services = 0
        created_tariffs = 0

        for item in items:
            service = Service.objects.create(
                title=item.get("title", ""),
                slug=item.get("slug", ""),
                description=item.get("description", ""),
                is_category=bool(item.get("is_category", False)),
                order=int(item.get("order", 0) or 0),
                parent=parent,
            )
            created_services += 1

            for tariff in item.get("tariffs", []) or []:
                Tariff.objects.create(
                    service=service,
                    title=tariff.get("title", ""),
                    slug=tariff.get("slug", ""),
                    description=tariff.get("description", ""),
                    duration=tariff.get("duration", ""),
                    price=int(tariff.get("price", 0) or 0),
                    order=int(tariff.get("order", 0) or 0),
                )
                created_tariffs += 1

            child_services, child_tariffs = self._create_service_tree(
                item.get("children", []) or [],
                parent=service,
            )
            created_services += child_services
            created_tariffs += child_tariffs

        return created_services, created_tariffs

    @transaction.atomic
    def handle(self, *args, **options):
        seed_data = self._load_seed()

        # Keep compatibility with older schedule schema where core_scheduleitem
        # still references core_service via FK and model is not loaded in ORM.
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.core_scheduleitem')")
            if cursor.fetchone()[0]:
                cursor.execute("UPDATE core_scheduleitem SET service_id = NULL")

        Tariff.objects.all().delete()
        Service.objects.all().delete()

        created_services, created_tariffs = self._create_service_tree(seed_data)

        self.stdout.write(self.style.SUCCESS("Services seeded successfully."))
        self.stdout.write(f"Services created: {created_services}")
        self.stdout.write(f"Tariffs created: {created_tariffs}")
