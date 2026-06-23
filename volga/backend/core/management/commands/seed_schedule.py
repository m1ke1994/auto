import datetime as dt
import random

from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction

from core.models import ScheduleDay, ScheduleEvent, Service


EVENT_TEMPLATES = [
    {
        "title": "Чайная церемония",
        "category": "Авторская программа",
        "price_min": 2800,
        "price_max": 4200,
        "description": "Камерный формат с практикой внимания и спокойным ритмом.",
        "color": "#E9B949",
        "service_slug": "avtorskie-programmy",
    },
    {
        "title": "Экскурсия в Братство лосей",
        "category": "Экскурсия",
        "price_min": 3200,
        "price_max": 5400,
        "description": "Маршрут по природной зоне с проводником и остановками в ключевых точках.",
        "color": "#6BA368",
        "service_slug": "ekskursiya-v-bratstvo-losey",
    },
    {
        "title": "Беговой клуб",
        "category": "Спорт",
        "price_min": 1200,
        "price_max": 2600,
        "description": "Легкая тренировка с акцентом на технику, темп и восстановление.",
        "color": "#C88B3A",
        "service_slug": "begovye-vstrechi",
    },
    {
        "title": "Мастер-класс по дыханию",
        "category": "Мастер-класс",
        "price_min": 1800,
        "price_max": 3200,
        "description": "Практика для фокуса, снижения напряжения и восстановления энергии.",
        "color": "#7AA2F7",
        "service_slug": "master-klassy",
    },
    {
        "title": "Волонтерская программа",
        "category": "Сообщество",
        "price_min": 900,
        "price_max": 1900,
        "description": "Практические задачи в команде с поддержкой координатора.",
        "color": "#A68BFF",
        "service_slug": "",
    },
    {
        "title": "Вечерний маршрут у воды",
        "category": "Экскурсия",
        "price_min": 2400,
        "price_max": 3900,
        "description": "Неспешный формат с наблюдением природы и финальной рефлексией.",
        "color": "#4FB3BF",
        "service_slug": "ekskursiya-v-bratstvo-losey",
    },
]


class Command(BaseCommand):
    help = "Seed schedule days and events using frontend mock structure."

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)
        today = dt.date.today()

        months_ahead = 8
        min_events_target = 110

        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.core_scheduleitem')")
            if cursor.fetchone()[0]:
                cursor.execute("DELETE FROM core_scheduleitem")

        ScheduleEvent.objects.all().delete()
        ScheduleDay.objects.all().delete()

        services_by_slug = {item.slug: item for item in Service.objects.all()}
        events_by_day = {}

        for month_offset in range(months_ahead):
            first_day = (today.replace(day=1) + dt.timedelta(days=31 * month_offset)).replace(day=1)
            year = first_day.year
            month = first_day.month
            days_in_month = (first_day.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)

            active_days_count = rng.randint(8, 15)
            target_size = min(active_days_count, days_in_month.day)
            day_numbers = sorted(rng.sample(range(1, days_in_month.day + 1), target_size))

            for day_number in day_numbers:
                day_date = dt.date(year, month, day_number)
                events_per_day = rng.randint(1, 3)
                base_hour = rng.randint(8, 15)

                day = ScheduleDay.objects.create(date=day_date, is_published=True)
                events_by_day[day_date] = 0

                for idx in range(events_per_day):
                    template = rng.choice(EVENT_TEMPLATES)
                    start_hour = min(base_hour + idx * 2, 20)
                    duration_minutes = rng.choice([60, 90, 120])
                    end_total_minutes = start_hour * 60 + duration_minutes
                    end_hour = end_total_minutes // 60
                    end_minutes = end_total_minutes % 60
                    service = services_by_slug.get(template["service_slug"]) if template["service_slug"] else None

                    ScheduleEvent.objects.create(
                        day=day,
                        service=service,
                        title=template["title"],
                        category=template["category"],
                        description=template["description"],
                        time_start=dt.time(start_hour, 0),
                        time_end=dt.time(end_hour, end_minutes),
                        price=rng.randint(template["price_min"], template["price_max"]),
                        color=template["color"],
                        order=idx,
                    )
                    events_by_day[day_date] += 1

        current_events = sum(events_by_day.values())
        if current_events < min_events_target:
            days = sorted(events_by_day.keys())
            day_cursor = 0

            while current_events < min_events_target and days:
                day_date = days[day_cursor % len(days)]
                load = events_by_day[day_date]
                if load < 3:
                    template = rng.choice(EVENT_TEMPLATES)
                    start_hour = 9 + load * 2
                    duration_minutes = rng.choice([60, 90, 120])
                    end_total_minutes = start_hour * 60 + duration_minutes
                    end_hour = end_total_minutes // 60
                    end_minutes = end_total_minutes % 60
                    service = services_by_slug.get(template["service_slug"]) if template["service_slug"] else None

                    day = ScheduleDay.objects.get(date=day_date)
                    ScheduleEvent.objects.create(
                        day=day,
                        service=service,
                        title=template["title"],
                        category=template["category"],
                        description=template["description"],
                        time_start=dt.time(start_hour, 0),
                        time_end=dt.time(end_hour, end_minutes),
                        price=rng.randint(template["price_min"], template["price_max"]),
                        color=template["color"],
                        order=load,
                    )
                    events_by_day[day_date] = load + 1
                    current_events += 1
                day_cursor += 1

        self.stdout.write(self.style.SUCCESS("Schedule seeded successfully."))
        self.stdout.write(f"Days created: {ScheduleDay.objects.count()}")
        self.stdout.write(f"Events created: {ScheduleEvent.objects.count()}")
