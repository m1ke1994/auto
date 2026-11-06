"""Editable content for the cinematic Alexandr Vodopyanov site.

The defaults are a faithful copy of the existing static website. Future admin
edits live in SiteSection.content and are never replaced by ordinary seeding.
"""
SITE_SLUG = "vodopyanov"
SITE_DOMAIN = "stariy-site.ru"
SITE_NAME = "Александр Водопьянов — автор песен и стихов"
SITE_SEO = {
    "title": "Между строк — Александр Водопьянов",
    "description": "Александр Водопьянов — автор песен и стихов. Кинематографическое путешествие через слово, тишину и музыку.",
    "canonical": "https://stariy-site.ru/",
}


def field(key, label, type="text", **kwargs):
    return {"key": key, "label": label, "type": type, **kwargs}


POEMS = [
    {"id": "lit-window", "publishedAt": "2026-10-15", "demo": True, "title": "Пока горит окно", "theme": "О близости",
     "lines": "Пока горит окно на той стороне,\nУ ночи есть причина быть светлее.\nИ город, засыпая в тишине,\nКого-то ждёт. И оттого теплее."},
    {"id": "distance", "publishedAt": "2026-10-10", "demo": True, "title": "На расстоянии", "theme": "О любви",
     "lines": "Меж нами — города и поезда,\nНо расстояние не измеряют вёрстами.\nТы просто оставайся. Иногда\nДостаточно, что мы под теми ж звёздами."},
    {"id": "quiet-shore", "publishedAt": "2026-10-01", "demo": True, "title": "Тихий берег", "theme": "О себе",
     "lines": "Я возвращаюсь к берегу реки,\nГде время не торопится случиться.\nИ все мои несказанные строки\nЛожатся на ладони, словно птицы."},
]

SONGS = [
    {"id": "after-midnight", "publishedAt": "2026-10-14", "demo": True, "title": "После полуночи",
     "theme": "Ночной город", "audioSrc": "", "notes": "220,261.63,329.63,293.66"},
    {"id": "where-you-are", "publishedAt": "2026-10-07", "demo": True, "title": "Там, где ты",
     "theme": "Близость", "audioSrc": "", "notes": "196,246.94,293.66,369.99"},
    {"id": "warm-wind", "publishedAt": "2026-09-28", "demo": True, "title": "Тёплый ветер",
     "theme": "Дорога", "audioSrc": "", "notes": "174.61,220,261.63,349.23"},
]

CONTACTS = [
    {"label": "Telegram", "caption": "@A1exdr56", "href": "https://t.me/A1exdr56"},
    {"label": "ВКонтакте", "caption": "vk.ru/positiveactive", "href": "https://vk.ru/positiveactive"},
    {"label": "Email", "caption": "Для сотрудничества", "href": ""},
]

SECTION_SEEDS = [
    {
        "key": "hero", "title": "Первый экран", "order": 10,
        "fields": [
            field("first_name", "Имя на первом экране"),
            field("last_name", "Фамилия на первом экране"),
            field("subtitle_first", "Подзаголовок — первая строка"),
            field("subtitle_second", "Подзаголовок — вторая строка"),
            field("intro_label", "Надпись над заголовком"),
        ],
        "content": {
            "first_name": "Александр", "last_name": "Водопьянов",
            "subtitle_first": "Стихи обретают голос.", "subtitle_second": "Песни обретают смысл.",
            "intro_label": "МЕЖДУ СТРОК / АВТОРСКИЙ МИР",
        },
    },
    {
        "key": "word", "title": "Рождение слова", "order": 20,
        "fields": [
            field("title", "Первая строка заголовка"),
            field("accent", "Выделенное слово"),
            field("text_first", "Описание — первая строка"),
            field("text_second", "Описание — вторая строка"),
        ],
        "content": {
            "title": "Всё начинается", "accent": "с одной строки.",
            "text_first": "Иногда она становится стихотворением.",
            "text_second": "Иногда — песней.",
        },
    },
    {
        "key": "about", "title": "Об авторе", "order": 30,
        "fields": [
            field("name", "Имя автора"), field("role", "Род занятий"),
            field("bio", "Биография", "textarea"),
            field("portrait_image", "Фото автора", "image"),
            field("headline_first", "Заголовок — первая строка"),
            field("headline_second", "Заголовок — вторая строка"),
            field("headline_accent", "Заголовок — выделенное слово"),
            field("note_first", "Подпись — первая строка"),
            field("note_second", "Подпись — выделенная строка"),
        ],
        "content": {
            "name": "Александр Водопьянов", "role": "Автор песен и стихов",
            "bio": "У каждого чувства есть свой голос. У каждой тишины — свои слова.",
            "portrait_image": "/images/portrait.webp",
            "headline_first": "Чувствовать.", "headline_second": "Находить",
            "headline_accent": "слова.", "note_first": "Разные темы.",
            "note_second": "Одно желание — быть услышанным.",
        },
    },
    {
        "key": "poems", "title": "Стихотворения", "order": 40,
        "fields": [
            field("title", "Заголовок — первая строка"),
            field("accent", "Заголовок — выделенное слово"),
            field("description_first", "Описание — первая строка"),
            field("description_second", "Описание — вторая строка"),
            field("items", "Стихотворения", "repeater", fields=[
                field("id", "Уникальный идентификатор", help_text="Латиница и дефисы, не меняйте после публикации."),
                field("title", "Название"),
                field("theme", "Тема"),
                field("publishedAt", "Дата публикации (ГГГГ-ММ-ДД)"),
                field("demo", "Демонстрационная работа", "boolean"),
                field("lines", "Текст стихотворения (каждая строка с новой строки)", "textarea"),
            ]),
        ],
        "content": {
            "title": "То, что говорят", "accent": "шёпотом.",
            "description_first": "О близости и расстояниях.",
            "description_second": "О том, что остаётся внутри.", "items": POEMS,
        },
    },
    {
        "key": "songs", "title": "Песни", "order": 50,
        "fields": [
            field("title", "Заголовок — первая строка"),
            field("accent", "Заголовок — выделенное слово"),
            field("description_first", "Описание — первая строка"),
            field("description_second", "Описание — вторая строка"),
            field("items", "Песни", "repeater", fields=[
                field("id", "Уникальный идентификатор", help_text="Латиница и дефисы, не меняйте после публикации."),
                field("title", "Название"), field("theme", "Тема"),
                field("publishedAt", "Дата публикации (ГГГГ-ММ-ДД)"),
                field("demo", "Звуковой эскиз (демо)", "boolean"),
                field("audioSrc", "Ссылка на аудиофайл (HTTPS или /media/...)",
                      help_text="Укажите прямую ссылку на аудиофайл; текущая медиатека TrackNode не принимает MP3."),
                field("notes", "Частоты звукового эскиза через запятую",
                      help_text="Используются, только если аудиофайл не указан. Например: 220,261.63,329.63,293.66"),
            ]),
        ],
        "content": {
            "title": "Когда словам", "accent": "нужны крылья.",
            "description_first": "Истории, которые хочется",
            "description_second": "услышать ещё раз.", "items": SONGS,
        },
    },
    {
        "key": "outro", "title": "Послесловие", "order": 60,
        "fields": [
            field("title", "Заголовок — первая строка"),
            field("accent", "Заголовок — выделенная строка"),
        ],
        "content": {"title": "Песня заканчивается.", "accent": "Слова остаются."},
    },
    {
        "key": "contacts", "title": "Контакты", "order": 70,
        "fields": [
            field("title", "Заголовок — первая строка"),
            field("accent", "Заголовок — выделенная строка"),
            field("description_first", "Описание — первая строка"),
            field("description_second", "Описание — вторая строка"),
            field("items", "Контактные каналы", "repeater", fields=[
                field("label", "Название"),
                field("caption", "Подпись"),
                field("href", "Адрес ссылки (HTTPS, mailto: или tel:)"),
            ]),
        ],
        "content": {
            "title": "Услышим", "accent": "друг друга.",
            "description_first": "Для творческого сотрудничества,",
            "description_second": "новых песен и простых человеческих слов.",
            "items": CONTACTS,
        },
    },
]


# Additional editor pages. New rows are created only if missing: prior edits to
# the original seven sections and to these pages remain intact on every rerun.
SECTION_SEEDS.extend([
    {
        "key": "catalog-poems", "title": "Страница «Все стихи»", "order": 80,
        "fields": [
            field("eyebrow", "Подпись над заголовком"),
            field("heading_start", "Начало заголовка"),
            field("heading_accent", "Выделенная часть заголовка"),
            field("intro", "Текст под заголовком", "textarea"),
            field("back_label", "Кнопка возврата на главную"),
            field("count_label", "Подпись количества работ"),
            field("sort_label", "Подпись выбора сортировки"),
            field("sort_newest", "Сортировка: сначала новые"),
            field("sort_oldest", "Сортировка: сначала старые"),
            field("more_label", "Кнопка «Показать ещё»"),
            field("empty_message", "Текст при отсутствии стихов"),
            field("footer_link", "Переход к странице песен"),
            field("seo_title", "SEO: Title для страницы", help_text="Статический Title задаётся в HTML, здесь меняется после загрузки CMS."),
            field("seo_description", "SEO: описание страницы", "textarea", help_text="Заменяет описание в браузере после загрузки CMS; начальное описание для роботов задаётся в HTML."),
        ],
        "content": {
            "eyebrow": "МЕЖДУ СТРОК / ПОЭЗИЯ",
            "heading_start": "Все", "heading_accent": "стихи.",
            "intro": "Строки о близости, расстояниях и внутреннем мире.",
            "back_label": "← Вернуться к истории",
            "count_label": "Всего работ", "sort_label": "По дате публикации",
            "sort_newest": "Сначала новые", "sort_oldest": "Сначала старые",
            "more_label": "Показать ещё",
            "empty_message": "Здесь скоро появятся стихи автора.",
            "footer_link": "Перейти к песням",
            "seo_title": "Стихи Александра Водопьянова — читать онлайн",
            "seo_description": "Стихотворения Александра Водопьянова: тексты, темы и даты публикаций. Читайте произведения автора в каталоге.",
        },
    },
    {
        "key": "catalog-songs", "title": "Страница «Все песни»", "order": 90,
        "fields": [
            field("eyebrow", "Подпись над заголовком"),
            field("heading_start", "Начало заголовка"),
            field("heading_accent", "Выделенная часть заголовка"),
            field("intro", "Текст под заголовком", "textarea"),
            field("back_label", "Кнопка возврата на главную"),
            field("count_label", "Подпись количества работ"),
            field("sort_label", "Подпись выбора сортировки"),
            field("sort_newest", "Сортировка: сначала новые"),
            field("sort_oldest", "Сортировка: сначала старые"),
            field("more_label", "Кнопка «Показать ещё»"),
            field("empty_message", "Текст при отсутствии песен"),
            field("footer_link", "Переход к странице стихов"),
            field("seo_title", "SEO: Title для страницы",
                  help_text="Начальный Title задаётся в HTML; CMS обновляет его после загрузки."),
            field("seo_description", "SEO: описание страницы", "textarea",
                  help_text="Начальное описание задаётся в HTML; CMS обновляет его после загрузки."),
        ],
        "content": {
            "eyebrow": "МЕЖДУ СТРОК / МУЗЫКА",
            "heading_start": "Все", "heading_accent": "песни.",
            "intro": "Истории, которые обретают голос.",
            "back_label": "← Вернуться к истории",
            "count_label": "Всего работ", "sort_label": "По дате публикации",
            "sort_newest": "Сначала новые", "sort_oldest": "Сначала старые",
            "more_label": "Показать ещё",
            "empty_message": "Здесь скоро появятся песни автора.",
            "footer_link": "Перейти к стихам",
            "seo_title": "Песни Александра Водопьянова — каталог",
            "seo_description": "Песни Александра Водопьянова: темы, даты публикаций и доступные звуковые эскизы.",
        },
    },
    {
        "key": "home-seo", "title": "Главная — SEO", "order": 100,
        "fields": [
            field("seo_title", "Заголовок вкладки и SEO Title"),
            field("seo_description", "Описание страницы", "textarea"),
        ],
        "content": {
            "seo_title": "Между строк — Александр Водопьянов | Стихи и песни",
            "seo_description": "Александр Водопьянов — автор песен и стихов. Кинематографическая история о творчестве, музыке и поэзии.",
        },
    },
])

for seed in SECTION_SEEDS:
    seed["schema"] = {"fields": seed.pop("fields")}
