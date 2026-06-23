from django.db import migrations


def _sync_page(Page, PageSection, PageGalleryImage, payload):
    page, _ = Page.objects.get_or_create(
        slug=payload["slug"],
        defaults={
            "title": payload["title"],
            "subtitle": payload["subtitle"],
            "hero_image": payload["hero_image"],
            "is_published": True,
            "order": payload["order"],
        },
    )

    page.title = payload["title"]
    page.subtitle = payload["subtitle"]
    page.hero_image = payload["hero_image"]
    page.is_published = True
    page.order = payload["order"]
    page.save(
        update_fields=["title", "subtitle", "hero_image", "is_published", "order", "updated_at"]
    )

    PageSection.objects.filter(page=page).delete()
    PageGalleryImage.objects.filter(page=page).delete()

    PageSection.objects.bulk_create(
        [
            PageSection(page=page, title=section["title"], text=section["text"], order=index)
            for index, section in enumerate(payload["sections"])
        ]
    )

    PageGalleryImage.objects.bulk_create(
        [
            PageGalleryImage(page=page, image=image_path, order=index)
            for index, image_path in enumerate(payload["gallery"])
        ]
    )


def seed_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    PageSection = apps.get_model("pages", "PageSection")
    PageGalleryImage = apps.get_model("pages", "PageGalleryImage")

    pages_payload = [
        {
            "slug": "brotherhood",
            "title": "Братство Лосей",
            "subtitle": "Экскурсии и встречи в ритме природы: наблюдение, движение и живой контакт с местом.",
            "hero_image": "pages/hero/placeholder.jpg",
            "sections": [
                {
                    "title": "Формат встреч",
                    "text": "Программы собираются в спокойном темпе: прогулки по маршрутам, короткие остановки и совместные практики внимания.",
                },
                {
                    "title": "Что важно",
                    "text": "Главный акцент на безопасной атмосфере, взаимной поддержке и возможности перезагрузиться без спешки.",
                },
                {
                    "title": "Результат",
                    "text": "После встреч участники уносят с собой чувство ясности, устойчивости и желание возвращаться к этому ритму.",
                },
            ],
            "gallery": [
                "pages/gallery/placeholder-1.jpg",
                "pages/gallery/placeholder-2.jpg",
                "pages/gallery/placeholder-3.jpg",
            ],
            "order": 1,
        },
        {
            "slug": "volunteers",
            "title": "Волонтерские программы",
            "subtitle": "Практические форматы участия в развитии пространства: от разовых выездов до регулярного участия.",
            "hero_image": "pages/hero/placeholder.jpg",
            "sections": [
                {
                    "title": "Как устроено участие",
                    "text": "Каждый волонтерский день включает вводный брифинг, практический блок и короткое подведение итогов.",
                },
                {
                    "title": "Поддержка команды",
                    "text": "Участникам доступны понятные задачи, сопровождение координаторов и комфортный вход без перегруза.",
                },
                {
                    "title": "Гибкий формат",
                    "text": "Можно выбрать удобный режим: разовое участие, ежемесячный выезд или сезонную серию задач.",
                },
            ],
            "gallery": [
                "pages/gallery/placeholder-1.jpg",
                "pages/gallery/placeholder-2.jpg",
                "pages/gallery/placeholder-3.jpg",
            ],
            "order": 2,
        },
        {
            "slug": "running-club",
            "title": "Беговой клуб",
            "subtitle": "Сообщество регулярных тренировок в природном ритме: с поддержкой, без давления и с устойчивой динамикой.",
            "hero_image": "pages/hero/placeholder.jpg",
            "sections": [
                {
                    "title": "Идея клуба",
                    "text": "Тренировки ориентированы на регулярность и бережную нагрузку, которую легко встроить в повседневную жизнь.",
                },
                {
                    "title": "Структура занятия",
                    "text": "Каждая встреча включает разминку, основной блок и мягкое восстановление с учетом уровня группы.",
                },
                {
                    "title": "Эффект регулярности",
                    "text": "Участники отмечают рост выносливости, более ровное состояние и устойчивую мотивацию тренироваться в команде.",
                },
            ],
            "gallery": [
                "pages/gallery/placeholder-1.jpg",
                "pages/gallery/placeholder-2.jpg",
                "pages/gallery/placeholder-3.jpg",
            ],
            "order": 3,
        },
    ]

    for payload in pages_payload:
        _sync_page(Page, PageSection, PageGalleryImage, payload)


def unseed_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    PageSection = apps.get_model("pages", "PageSection")
    PageGalleryImage = apps.get_model("pages", "PageGalleryImage")

    slugs = ["brotherhood", "volunteers", "running-club"]
    pages = Page.objects.filter(slug__in=slugs)
    PageSection.objects.filter(page__in=pages).delete()
    PageGalleryImage.objects.filter(page__in=pages).delete()
    pages.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0002_seed_about_page"),
    ]

    operations = [
        migrations.RunPython(seed_pages, reverse_code=unseed_pages),
    ]
