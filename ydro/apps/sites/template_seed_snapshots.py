from copy import deepcopy

from .a_meditation import A_MEDITATION_SECTION_SEEDS
from .models import Site


ART_STROY_BUILDER_KEY = "art-troy"
A_MEDITATION_BUILDER_KEY = "a-meditation"


def _field(key, label, field_type="text", default=""):
    return {"key": key, "label": label, "type": field_type, "default": deepcopy(default)}


def _field_for_value(key, value):
    if isinstance(value, list):
        nested_keys = []
        for item in value:
            if isinstance(item, dict):
                for nested_key in item:
                    if nested_key not in nested_keys:
                        nested_keys.append(nested_key)
        sample = next((item for item in value if isinstance(item, dict)), {})
        field = _field(key, key.replace("_", " ").title(), "repeater", value)
        field["fields"] = [_field_for_value(nested_key, sample.get(nested_key, "")) for nested_key in nested_keys]
        return field
    if isinstance(value, bool):
        return _field(key, key.replace("_", " ").title(), "boolean", value)
    if isinstance(value, (int, float)):
        return _field(key, key.replace("_", " ").title(), "number", value)
    field_type = "image" if key.lower() in {"image", "avatar", "poster"} else "textarea"
    return _field(key, key.replace("_", " ").title(), field_type, value)


def _section(key, title, order, content, component_key=None, section_type=None):
    return {
        "title": title,
        "key": key,
        "section_type": section_type or key,
        "order": order,
        "is_active": True,
        "schema": {"fields": [_field_for_value(item, value) for item, value in content.items()]},
        "content": deepcopy(content),
        "component_key": component_key or key,
        "settings": {},
        "seo": {},
    }


def art_stroy_snapshot():
    builder_config = {
        "company_name": "Art Stroy",
        "description": "Проектирование и монтаж стеклянных конструкций, ограждений и душевых перегородок.",
        "phone": "+7 900 000-00-00",
        "email": "hello@artstroy.example",
        "city": "Москва",
        "hero": {
            "title": "Art Stroy",
            "subtitle": "Стекло, металл и точная инженерия для частных и коммерческих пространств",
            "image": "/art-stroy/images/hero.jpg",
            "video": "/art-stroy/videos/video-bg.MP4",
        },
        "navigation": [
            {"label": "Проекты", "href": "#projects"},
            {"label": "Отзывы", "href": "#reviews"},
            {"label": "Контакты", "href": "#contacts"},
        ],
        "theme": {
            "colors": {"primary": "#c8a24a", "ink": "#151515", "background": "#f7f4ee"},
            "fonts": {"heading": "Inter", "body": "Inter"},
        },
        "pages": [{"key": "home", "title": "Главная", "path": "/"}],
    }
    sections = [
        _section(
            "hero",
            "Hero",
            1,
            {
                "company_name": "Art Stroy",
                "title": "Стеклянные конструкции под ключ",
                "description": "Производим и монтируем душевые, ограждения, зеркальные панели и перегородки.",
                "image": "/art-stroy/images/hero.jpg",
                "phone": "+7 900 000-00-00",
            },
            "art-troy-hero",
        ),
        _section(
            "about",
            "About",
            2,
            {
                "title": "Инженерия. Эстетика. Надёжность.",
                "description": "Объединяем инженерную точность и современный дизайн. Ведём проект от замера и расчёта до монтажа.",
            },
            "art-troy-about",
        ),
        _section(
            "projects",
            "Projects",
            3,
            {
                "title": "Реализованные проекты",
                "description": "Душевые перегородки, лестничные ограждения, зеркальные панели и интерьерные решения.",
                "items": [
                    {"title": "Стеклянные ограждения", "description": "Безопасное стекло и точная геометрия.", "image": "/art-stroy/projects/bg.webp"},
                    {"title": "Душевые перегородки", "description": "Индивидуальное изготовление под помещение.", "image": "/art-stroy/showers/1-1.JPG"},
                    {"title": "Зеркальные панели", "description": "Монтаж панелей сложной конфигурации.", "image": "/art-stroy/mirror-panel/1-1.JPG"},
                ],
            },
            "art-troy-projects",
        ),
        _section(
            "reviews",
            "Reviews",
            4,
            {
                "title": "Нам доверяют сложные проекты",
                "items": [
                    {"author": "Алексей", "text": "Точно выдержали размеры и завершили монтаж в согласованный срок."},
                    {"author": "Марина", "text": "Помогли выбрать конструкцию и аккуратно установили стеклянную перегородку."},
                    {"author": "Илья", "text": "Понятная смета, качественные материалы и внимательная команда."},
                ],
            },
            "art-troy-reviews",
        ),
        _section(
            "contacts",
            "Contacts",
            5,
            {
                "title": "Обсудить проект",
                "description": "Оставьте контакты, и мы подготовим расчет по размерам и задачам объекта.",
                "phone": "+7 900 000-00-00",
                "email": "hello@artstroy.example",
                "city": "Москва",
            },
            "art-troy-contacts",
        ),
        _section(
            "footer",
            "Footer",
            6,
            {"copyright": "Art Stroy. Проектирование и монтаж стеклянных конструкций."},
            "art-troy-footer",
        ),
    ]
    return _snapshot("tracknode-template-art-stroy-source", "Art Stroy", ART_STROY_BUILDER_KEY, builder_config, sections)


def a_meditation_snapshot():
    builder_config = {
        "company_name": "A Meditation",
        "description": "Практики осознанности, медитации и игра Лила в Москве.",
        "phone": "+7 900 000-00-00",
        "email": "hello@a-meditation.example",
        "city": "Москва",
        "theme": {
            "colors": {"primary": "#7c6746", "ink": "#201b16", "background": "#fbf8f1"},
            "fonts": {"heading": "Cormorant Garamond", "body": "Manrope"},
        },
        "assets": {
            "hero_video": "/images/Lila_Olga_2.2_compressed.mp4",
            "hero_poster": "/images/Lila_Olga_2.2.poster.jpg",
        },
        "pages": [{"key": "home", "title": "Главная", "path": "/"}],
    }
    sections = []
    for seed in A_MEDITATION_SECTION_SEEDS:
        section = deepcopy(seed)
        section.setdefault("section_type", section["key"])
        section.setdefault("component_key", f"a-meditation-{section['key'].replace('_', '-')}")
        section.setdefault("is_active", True)
        section.setdefault("settings", {})
        section.setdefault("seo", {})
        sections.append(section)
    return _snapshot("tracknode-template-a-meditation-source", "A Meditation", A_MEDITATION_BUILDER_KEY, builder_config, sections)


def _snapshot(source_slug, source_name, builder_template_key, builder_config, sections):
    return {
        "version": 1,
        "source": {"site_slug": source_slug, "site_name": source_name},
        "site": {
            "seo": {"title": source_name, "description": builder_config.get("description", "")},
            "design_preset": Site.DesignPreset.WARM_NATURE,
            "builder_template_key": builder_template_key,
            "builder_config": deepcopy(builder_config),
            "design_tokens": deepcopy(builder_config.get("theme", {})),
            "pages_config": {},
            "theme": deepcopy(builder_config.get("theme", {})),
        },
        "pages": deepcopy(builder_config.get("pages", [])),
        "sections": deepcopy(sections),
    }
