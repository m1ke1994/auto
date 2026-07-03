from copy import deepcopy


TRACKNODE_SITE_NAME = "TrackNode"
TRACKNODE_SITE_SLUG = "tracknode"
TRACKNODE_SITE_DOMAIN = "tracknode.ru"

TRACKNODE_SITE_SEO = {
    "title": "TrackNode — аналитика сайта, заявки, SEO-аудит и конкуренты в одном кабинете",
    "description": (
        "TrackNode объединяет веб-аналитику, тепловые карты, записи сессий, заявки, "
        "SEO-аудит, анализ конкурентов и отчёты для роста сайта и бизнеса."
    ),
    "keywords": (
        "аналитика сайта, поведенческая аналитика, тепловые карты, записи сессий, "
        "заявки с сайта, SEO-аудит сайта, анализ конкурентов, отчёты PDF, "
        "Telegram-уведомления, TrackNode"
    ),
    "canonical": "https://tracknode.ru/",
    "robots": "index,follow",
    "og_title": "TrackNode — аналитика сайта, заявки, SEO-аудит и конкуренты",
    "og_description": (
        "Веб-аналитика, SEO-аудит, анализ конкурентов, заявки и понятные рекомендации "
        "для роста сайта в одном кабинете."
    ),
    "og_image": "https://tracknode.ru/og-image.svg",
    "structured_data": {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "TrackNode",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": "https://tracknode.ru/",
        "description": (
            "TrackNode объединяет аналитику сайтов, заявки, SEO-аудит, "
            "анализ конкурентов и отчёты в одном кабинете."
        ),
        "offers": {"@type": "Offer", "price": "1299", "priceCurrency": "RUB"},
    },
}


def field(key, label, field_type="text", **extra):
    return {"key": key, "label": label, "type": field_type, **extra}


def repeater(key, label, fields):
    return field(key, label, "repeater", fields=fields)


def schema(*fields):
    return {"fields": list(fields)}


TRACKNODE_SECTION_SEEDS = [
    {
        "key": "navigation",
        "title": "Навигация",
        "order": 10,
        "schema": schema(
            field("brand_kicker", "Надпись над логотипом"),
            field("brand_name", "Название бренда"),
            field("cube_alt", "Alt логотипа"),
            repeater(
                "left_links",
                "Ссылки слева",
                [field("label", "Подпись"), field("href", "Ссылка"), field("section_id", "ID секции")],
            ),
            repeater(
                "right_links",
                "Ссылки справа",
                [field("label", "Подпись"), field("href", "Ссылка"), field("section_id", "ID секции")],
            ),
            field("login_label", "Текст кнопки входа"),
            field("login_route", "Маршрут входа"),
        ),
        "content": {
            "brand_kicker": "Система",
            "brand_name": "TrackNode",
            "cube_alt": "Фирменный куб TrackNode",
            "left_links": [
                {"label": "Возможности", "href": "#features", "section_id": "features"},
                {"label": "Аналитика", "href": "#ecosystem", "section_id": "ecosystem"},
                {"label": "SEO-анализ", "href": "#seo-audit", "section_id": "seo-audit"},
            ],
            "right_links": [
                {"label": "Тарифы", "href": "#pricing", "section_id": "pricing"},
                {"label": "FAQ", "href": "#faq", "section_id": "faq"},
            ],
            "login_label": "Войти в кабинет",
            "login_route": "/login",
        },
    },
    {
        "key": "hero",
        "title": "Первый экран",
        "order": 20,
        "schema": schema(
            field("eyebrow", "Надзаголовок"),
            field("title_line_1", "Заголовок — строка 1"),
            field("title_line_2", "Заголовок — строка 2"),
            field("title_accent", "Акцентная строка"),
            field("description", "Описание", "textarea"),
            field("primary_label", "Основная кнопка"),
            field("primary_route", "Маршрут основной кнопки"),
            field("secondary_label", "Дополнительная кнопка"),
            field("secondary_href", "Ссылка дополнительной кнопки"),
            field("cube_alt", "Alt куба"),
            field("visitors_card_label", "Карточка посетителей"),
            field("conversion_card_label", "Карточка конверсии"),
            field("heatmap_card_label", "Карточка тепловой карты"),
            field("traffic_card_label", "Карточка источников"),
            repeater("benefits", "Преимущества", [field("label", "Текст"), field("icon", "Иконка")]),
            repeater(
                "stats",
                "Интерактивные показатели",
                [
                    field("key", "Ключ"),
                    field("label", "Подпись"),
                    field("target", "Значение", "number"),
                    field("format", "Формат", "select", options=["integer", "percent"]),
                    field("delta", "Изменение"),
                    field("icon", "Иконка"),
                ],
            ),
        ),
        "content": {
            "eyebrow": "Аналитика для роста бизнеса",
            "title_line_1": "Понимайте аудиторию.",
            "title_line_2": "Принимайте решения.",
            "title_accent": "Растите быстрее.",
            "description": (
                "TrackNode собирает данные о посетителях, источниках трафика и действиях на сайте. "
                "Превращает цифры в понятные инсайты, которые помогают увеличивать конверсию и прибыль."
            ),
            "primary_label": "Подключиться",
            "primary_route": "/register",
            "secondary_label": "Посмотреть демо",
            "secondary_href": "#ecosystem",
            "cube_alt": "Фирменный куб TrackNode",
            "visitors_card_label": "Посетители",
            "conversion_card_label": "Конверсия",
            "heatmap_card_label": "Тепловая карта",
            "traffic_card_label": "Источники трафика",
            "benefits": [
                {"label": "Установка за 5 минут", "icon": "zap"},
                {"label": "Данные в реальном времени", "icon": "route"},
                {"label": "Понятные тарифы", "icon": "check"},
                {"label": "Российский сервер", "icon": "blocks"},
            ],
            "stats": [
                {"key": "visitors", "label": "Посетителей", "target": 24780, "format": "integer", "delta": "+12.3%", "icon": "analytics"},
                {"key": "views", "label": "Просмотра", "target": 71842, "format": "integer", "delta": "+8.1%", "icon": "route"},
                {"key": "leads", "label": "Заявки", "target": 342, "format": "integer", "delta": "+15.7%", "icon": "inbox"},
                {"key": "conversion", "label": "Конверсия", "target": 2.47, "format": "percent", "delta": "+8.3%", "icon": "funnel"},
            ],
        },
    },
    {
        "key": "features",
        "title": "Возможности",
        "order": 30,
        "schema": schema(
            field("eyebrow", "Надзаголовок"),
            field("title", "Заголовок"),
            field("title_line_2", "Вторая строка заголовка"),
            field("title_accent", "Акцент заголовка"),
            field("description", "Описание", "textarea"),
            repeater(
                "promises",
                "Ключевые преимущества",
                [field("title", "Заголовок"), field("text", "Описание"), field("icon", "Иконка")],
            ),
            repeater(
                "items",
                "Карточки возможностей",
                [
                    field("number", "Номер"), field("title", "Заголовок"),
                    field("text", "Описание", "textarea"), field("icon", "Иконка"),
                    field("visual_type", "Тип визуализации"),
                    repeater("visual_items", "Подписи визуализации", [field("label", "Текст")]),
                ],
            ),
        ),
        "content": {
            "eyebrow": "Всё для роста вашего бизнеса",
            "title": "Возможности,",
            "title_line_2": "которые",
            "title_accent": "дают результат",
            "description": "TrackNode объединяет ключевые инструменты для анализа, оптимизации и роста сайта в одном сервисе.",
            "promises": [
                {"title": "Точные данные", "text": "Без искажений", "icon": "check"},
                {"title": "Реальное время", "text": "Метрики онлайн", "icon": "zap"},
                {"title": "Практические инсайты", "text": "Понятный план роста", "icon": "sparkles"},
            ],
            "items": [
                {"number": "01", "title": "Веб-аналитика", "text": "Посетители, источники трафика и ключевые события в одном отчёте.", "icon": "analytics", "visual_type": "chart", "visual_items": []},
                {"number": "02", "title": "Карта кликов и скролла", "text": "Находите зоны внимания и точки, где аудитория теряет интерес.", "icon": "click", "visual_type": "heatmap", "visual_items": []},
                {"number": "03", "title": "Конверсии и цели", "text": "Собирайте воронки и отслеживайте путь от просмотра до заявки.", "icon": "funnel", "visual_type": "funnel", "visual_items": []},
                {"number": "04", "title": "SEO-аудит", "text": "Проверяйте техническое SEO и получайте понятные рекомендации.", "icon": "seo", "visual_type": "score", "visual_items": [{"label": "87"}, {"label": "/100"}]},
                {"number": "05", "title": "Анализ конкурентов", "text": "Сравнивайте трафик, страницы и видимость с конкурентами.", "icon": "search", "visual_type": "compare", "visual_items": []},
                {"number": "06", "title": "Уведомления", "text": "Получайте важные события и новые заявки без задержек.", "icon": "bell", "visual_type": "alerts", "visual_items": [{"label": "Новая заявка"}, {"label": "Цель достигнута"}, {"label": "Ошибка на сайте"}]},
                {"number": "07", "title": "Отчёты и экспорт", "text": "Экспортируйте данные в PDF и CSV по расписанию.", "icon": "report", "visual_type": "reports", "visual_items": [{"label": "PDF"}, {"label": "CSV"}]},
                {"number": "08", "title": "Устройства и технологии", "text": "Узнавайте, с каких устройств и браузеров приходит аудитория.", "icon": "device", "visual_type": "devices", "visual_items": [{"label": "Desktop 55%"}, {"label": "Mobile 35%"}, {"label": "Tablet 10%"}]},
                {"number": "09", "title": "AI-инсайты и рекомендации", "text": "Находите скрытые точки роста и получайте план действий.", "icon": "sparkles", "visual_type": "ai", "visual_items": [{"label": "+23%"}]},
            ],
        },
    },
    {
        "key": "analytics",
        "title": "Экосистема аналитики",
        "order": 40,
        "schema": schema(
            field("eyebrow", "Надзаголовок"), field("title", "Заголовок"),
            field("title_accent", "Акцент заголовка"), field("description", "Описание", "textarea"),
            field("cube_alt", "Alt куба"),
            repeater(
                "items", "Элементы экосистемы",
                [field("title", "Заголовок"), field("text", "Описание"), field("icon", "Иконка"), field("position", "Позиция")],
            ),
        ),
        "content": {
            "eyebrow": "Экосистема TrackNode",
            "title": "Вся сила аналитики в",
            "title_accent": "единой экосистеме",
            "description": "Все инструменты TrackNode работают вместе, чтобы данные превращались в понятные решения для роста.",
            "cube_alt": "Фирменный куб — центр экосистемы TrackNode",
            "items": [
                {"title": "Аналитика", "text": "Вся динамика сайта в реальном времени", "icon": "analytics", "position": "p1"},
                {"title": "SEO-анализ", "text": "Ошибки и поисковые возможности", "icon": "seo", "position": "p2"},
                {"title": "Карта кликов", "text": "Визуальная карта внимания", "icon": "click", "position": "p3"},
                {"title": "Поведение", "text": "Путь каждого пользователя", "icon": "route", "position": "p4"},
                {"title": "AI-инсайты", "text": "Рекомендации по росту", "icon": "sparkles", "position": "p5"},
                {"title": "Воронки", "text": "Контроль этапов конверсии", "icon": "funnel", "position": "p6"},
                {"title": "Уведомления", "text": "Важное — без задержек", "icon": "bell", "position": "p7"},
                {"title": "Производительность", "text": "Скорость и стабильность сайта", "icon": "zap", "position": "p8"},
                {"title": "Конкуренты", "text": "Сравнение позиций и страниц", "icon": "search", "position": "p9"},
                {"title": "Конверсии", "text": "Цели, заявки и результат", "icon": "check", "position": "p10"},
            ],
        },
    },
    {
        "key": "seo_analysis",
        "title": "SEO-анализ",
        "order": 50,
        "schema": schema(
            field("eyebrow", "Надзаголовок"), field("title", "Заголовок"),
            field("title_accent", "Акцент заголовка"), field("description", "Описание", "textarea"),
            field("cta_label", "Текст кнопки"), field("cta_route", "Маршрут кнопки"),
            field("dashboard_domain", "Домен в макете"), field("health_label", "Подпись оценки"),
            field("health_value", "Оценка", "number"), field("health_status", "Статус оценки"),
            field("health_scale", "Шкала оценки"),
            field("health_description", "Описание оценки", "textarea"),
            field("recommendation_label", "Подпись рекомендации"), field("recommendation_title", "Заголовок рекомендации"),
            field("recommendation_text", "Текст рекомендации", "textarea"),
            repeater("summary", "Сводка", [field("value", "Значение"), field("label", "Подпись")]),
            repeater("checks", "Проверки", [field("label", "Проверка"), field("status", "Статус"), field("result", "Результат")]),
        ),
        "content": {
            "eyebrow": "SEO-анализ",
            "title": "SEO-анализ, который показывает,",
            "title_accent": "что мешает сайту расти",
            "description": "TrackNode сканирует сайт, расставляет приоритеты и объясняет, что исправить в первую очередь — без сложных таблиц и технического шума.",
            "cta_label": "Подключиться", "cta_route": "/register", "dashboard_domain": "your-site.ru",
            "health_label": "SEO Health", "health_value": 87, "health_scale": "/100", "health_status": "Хороший результат",
            "health_description": "Сайт готов к росту. Осталось исправить несколько важных пунктов.",
            "recommendation_label": "AI-рекомендация", "recommendation_title": "Сожмите изображения на 4 страницах",
            "recommendation_text": "Это ускорит загрузку на мобильных устройствах примерно на 1,2 секунды.",
            "summary": [{"value": "12", "label": "ошибок"}, {"value": "8", "label": "предупреждений"}, {"value": "34", "label": "проверки пройдено"}],
            "checks": [
                {"label": "Title и Description", "status": "ok", "result": "Пройдено"},
                {"label": "Скорость загрузки", "status": "warn", "result": "Проверить"},
                {"label": "Мобильная адаптация", "status": "ok", "result": "Пройдено"},
                {"label": "Индексация", "status": "ok", "result": "Пройдено"},
                {"label": "Технические ошибки", "status": "error", "result": "Исправить"},
                {"label": "Дубли страниц", "status": "warn", "result": "Проверить"},
                {"label": "Изображения", "status": "ok", "result": "Пройдено"},
                {"label": "Структура заголовков", "status": "ok", "result": "Пройдено"},
            ],
        },
    },
    {
        "key": "tariffs",
        "title": "Тарифы",
        "order": 60,
        "schema": schema(
            field("eyebrow", "Надзаголовок"), field("title", "Заголовок"),
            field("title_accent", "Акцент заголовка"), field("description", "Описание"),
            field("popular_label", "Метка популярного тарифа"), field("cta_label", "Кнопка тарифа"),
            field("cta_route", "Маршрут кнопки"),
            repeater("tabs", "Периоды", [field("id", "ID"), field("label", "Подпись"), field("saving", "Скидка")]),
            repeater(
                "plans", "Тарифные карточки",
                [
                    field("duration", "Период"), field("title", "Название"), field("price", "Цена"),
                    field("period", "Подпись периода"), field("featured", "Популярный", "boolean"),
                    field("description", "Описание", "textarea"),
                    repeater("features", "Возможности", [field("label", "Возможность")]),
                ],
            ),
        ),
        "content": {
            "eyebrow": "Простые тарифы", "title": "Выберите формат", "title_accent": "для вашего роста",
            "description": "Выберите подходящий тариф и зарегистрируйте проект.",
            "popular_label": "Популярный", "cta_label": "Подключиться", "cta_route": "/register",
            "tabs": [
                {"id": "monthly", "label": "1 месяц", "saving": ""},
                {"id": "halfYear", "label": "6 месяцев", "saving": "−5%"},
                {"id": "year", "label": "12 месяцев", "saving": "−10%"},
            ],
            "plans": [
                {"duration": "monthly", "title": "Контент и хостинг", "price": "1 299", "period": "/ месяц", "featured": False, "description": "Надёжная техническая основа для вашего сайта.", "features": [{"label": "Хостинг сайта"}, {"label": "Управление контентом"}, {"label": "Резервное копирование"}, {"label": "Техническая поддержка"}]},
                {"duration": "monthly", "title": "Бизнес-аналитика", "price": "1 999", "period": "/ месяц", "featured": True, "description": "Полный набор инструментов для роста сайта и бизнеса.", "features": [{"label": "Веб-аналитика и цели"}, {"label": "SEO-аудит и конкуренты"}, {"label": "AI-рекомендации"}, {"label": "Отчёты и уведомления"}]},
                {"duration": "halfYear", "title": "Контент и хостинг", "price": "7 404", "period": "за 6 месяцев", "featured": False, "description": "Надёжная техническая основа для вашего сайта.", "features": [{"label": "Хостинг сайта"}, {"label": "Управление контентом"}, {"label": "Резервное копирование"}, {"label": "Техническая поддержка"}]},
                {"duration": "halfYear", "title": "Бизнес-аналитика", "price": "11 394", "period": "за 6 месяцев", "featured": True, "description": "Полный набор инструментов для роста сайта и бизнеса.", "features": [{"label": "Веб-аналитика и цели"}, {"label": "SEO-аудит и конкуренты"}, {"label": "AI-рекомендации"}, {"label": "Отчёты и уведомления"}]},
                {"duration": "year", "title": "Контент и хостинг", "price": "14 029", "period": "за 12 месяцев", "featured": False, "description": "Надёжная техническая основа для вашего сайта.", "features": [{"label": "Хостинг сайта"}, {"label": "Управление контентом"}, {"label": "Резервное копирование"}, {"label": "Техническая поддержка"}]},
                {"duration": "year", "title": "Бизнес-аналитика", "price": "21 589", "period": "за 12 месяцев", "featured": True, "description": "Полный набор инструментов для роста сайта и бизнеса.", "features": [{"label": "Веб-аналитика и цели"}, {"label": "SEO-аудит и конкуренты"}, {"label": "AI-рекомендации"}, {"label": "Отчёты и уведомления"}]},
            ],
        },
    },
    {
        "key": "faq",
        "title": "Частые вопросы",
        "order": 70,
        "schema": schema(
            field("eyebrow", "Надзаголовок"), field("title", "Заголовок"),
            field("description", "Описание"),
            repeater("items", "Вопросы и ответы", [field("question", "Вопрос"), field("answer", "Ответ", "textarea")]),
        ),
        "content": {
            "eyebrow": "FAQ", "title": "Ответы на частые вопросы",
            "description": "Не нашли ответ? Напишите нам — поможем разобраться.",
            "items": [
                {"question": "Сколько занимает подключение TrackNode?", "answer": "Обычно не больше пяти минут: добавьте сайт, установите короткий код и дождитесь первых событий."},
                {"question": "Как начать работу с TrackNode?", "answer": "Зарегистрируйтесь, выберите подходящий тариф и подключите сайт по инструкции в личном кабинете."},
                {"question": "Данные хранятся в России?", "answer": "Да, инфраструктура TrackNode и основные данные размещены на российских серверах."},
                {"question": "Можно ли подключить несколько сайтов?", "answer": "Да. В кабинете можно управлять несколькими проектами и переключаться между ними."},
                {"question": "TrackNode заменяет Яндекс Метрику?", "answer": "TrackNode дополняет привычную аналитику SEO-аудитом, конкурентным анализом и единым планом действий."},
            ],
        },
    },
    {
        "key": "final_cta",
        "title": "Финальный призыв",
        "order": 80,
        "schema": schema(field("eyebrow", "Надзаголовок"), field("title", "Заголовок"), field("button_label", "Кнопка"), field("button_route", "Маршрут")),
        "content": {"eyebrow": "Один сервис — вся аналитика", "title": "Начните принимать решения на основе данных", "button_label": "Регистрация", "button_route": "/register"},
    },
    {
        "key": "footer",
        "title": "Подвал сайта",
        "order": 90,
        "schema": schema(
            field("brand_name", "Название бренда"), field("cube_alt", "Alt логотипа"),
            field("description", "Описание"), field("copyright", "Текст copyright"),
            repeater("links", "Ссылки", [field("label", "Подпись"), field("href", "Ссылка")]),
        ),
        "content": {
            "brand_name": "TrackNode", "cube_alt": "Фирменный куб TrackNode",
            "description": "Аналитика, SEO и инсайты для роста сайта в одном сервисе.",
            "copyright": "TrackNode",
            "links": [{"label": "Возможности", "href": "#features"}, {"label": "Тарифы", "href": "#pricing"}, {"label": "FAQ", "href": "#faq"}, {"label": "Войти", "href": "/login"}],
        },
    },
]


def get_tracknode_section_seed(key):
    seed = next((item for item in TRACKNODE_SECTION_SEEDS if item["key"] == key), None)
    return deepcopy(seed) if seed else None
