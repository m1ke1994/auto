MY_PORTFOLIO_SITE_NAME = "Портфолио Александра"
MY_PORTFOLIO_SITE_SLUG = "my-portfolio"
MY_PORTFOLIO_SITE_DOMAIN = "tishechkinalexandr.ru"
MY_PORTFOLIO_SITE_ALIAS_DOMAIN = "www.tishechkinalexandr.ru"

MY_PORTFOLIO_SITE_SEO = {
    "title": "Александр Тишечкин - Full-stack Web Developer",
    "description": (
        "Персональное портфолио Александра Тишечкина. Full-stack веб-разработчик: "
        "Vue.js, Django, REST API, frontend, backend и деплой."
    ),
    "keywords": "Александр Тишечкин, fullstack разработчик, веб разработчик, frontend, backend, Vue.js, Django",
    "canonical": "https://tishechkinalexandr.ru/",
    "og_title": "Александр Тишечкин - Full-stack Web Developer",
    "og_description": "Персональное портфолио: разработка веб-приложений, frontend и backend.",
    "og_image": "https://tishechkinalexandr.ru/og-image.jpg",
    "twitter_card": "summary_large_image",
}


def field(key, label, field_type="text", **extra):
    payload = {"key": key, "label": label, "type": field_type}
    payload.update(extra)
    return payload


NAV_ITEMS = [
    {"label": "Обо мне", "href": "#about"},
    {"label": "Услуги", "href": "#services"},
    {"label": "Навыки", "href": "#skills"},
    {"label": "Проекты", "href": "#projects"},
    {"label": "Контакты", "href": "#contact"},
]

CONTACTS = [
    {"icon": "message", "label": "Telegram", "value": "@M1ke994", "href": "https://t.me/M1ke994"},
    {"icon": "mail", "label": "Email", "value": "Tishechkin1994@gmail.com", "href": "mailto:Tishechkin1994@gmail.com"},
    {"icon": "github", "label": "GitHub", "value": "github.com/m1ke1994", "href": "https://github.com/m1ke1994"},
    {
        "icon": "instagram",
        "label": "Instagram",
        "value": "instagram.com/alexandr_tishechkin",
        "href": "https://instagram.com/alexandr_tishechkin",
    },
    {
        "icon": "linkedin",
        "label": "LinkedIn",
        "value": "linkedin.com/in/alexandr-tishechkin",
        "href": "https://linkedin.com/in/alexandr-tishechkin",
    },
]

PROJECTS = [
    {
        "id": "1",
        "title": "Салон красоты",
        "category": "landing",
        "shortDescription": "Лендинг салона красоты с акцентом на услуги, мастеров и быстрый контакт.",
        "fullDescription": "Сделал одностраничный сайт с блоками услуг, цен, отзывов и быстрых CTA. Продумал визуальную иерархию, адаптивы и оптимизацию медиа для быстрой загрузки.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Верстка, адаптив, настройка контентных блоков и оптимизация изображений.",
        "images": ["/beauty-salon-website-psi.vercel.JPG"],
        "demoUrl": "https://beauty-salon-website-psi.vercel.app/",
    },
    {
        "id": "2",
        "title": "Конструкторское бюро",
        "category": "landing",
        "shortDescription": "Презентационный лендинг инженерной компании с фокусом на услуги и кейсы.",
        "fullDescription": "Собрал структуру секций: услуги, компетенции, выполненные проекты и контактные блоки. Упор на понятную подачу и аккуратную типографику, плюс адаптив для мобильных.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Frontend-разработка, адаптивная верстка, настройка контента и визуальных акцентов.",
        "images": ["/website-ikb.vercel.JPG"],
        "demoUrl": "https://website-ikb.vercel.app/",
    },
    {
        "id": "3",
        "title": "Инновационное конструкторское бюро",
        "category": "landing",
        "shortDescription": "Лендинг для инженерной команды с акцентом на экспертизу и направление работ.",
        "fullDescription": "Сделал одностраничный сайт с акцентом на преимущества, портфолио и процесс работы. Продумал визуальные блоки, чтобы быстро объяснить ценность услуг.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Сборка секций, адаптивная верстка и настройка контента.",
        "images": ["/ikb-theta.vercel.JPG"],
        "demoUrl": "https://ikb-theta.vercel.app/",
    },
    {
        "id": "4",
        "title": "Maysama - главная страница (копия)",
        "category": "landing",
        "shortDescription": "Учебный проект: точное воспроизведение главной страницы с адаптивом.",
        "fullDescription": "Практика верстки и композиции: повторил сетку, типографику и визуальные блоки. Отработал адаптив и структуру компонентов для дальнейшего масштабирования.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Верстка, адаптив, повторение компонентов и базовая оптимизация.",
        "images": ["/maysamafrontend.vercel.JPG"],
        "demoUrl": "https://maysamafrontend.vercel.app/",
    },
    {
        "id": "5",
        "title": "Smart Nara - витрина интернет-магазина",
        "category": "multipage",
        "shortDescription": "Pet-проект витрины интернет-магазина с каталогом и карточками товаров.",
        "fullDescription": "Практический проект: каталог, фильтры, поиск и детальная карточка товара. Отработал состояние фильтров, сортировку и структуру каталога.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Frontend-разработка, логика фильтров и каталог.",
        "images": ["/test-eight-weld-74.vercel.JPG"],
        "demoUrl": "https://test-eight-weld-74.vercel.app/",
    },
    {
        "id": "6",
        "title": "Трекер-панель (доработка)",
        "category": "service",
        "shortDescription": "Доработка клиентской панели: фильтры, таблицы, правки интерфейса.",
        "fullDescription": "В существующем проекте обновил UI, переработал экраны с таблицами и добавил новые фильтры. Подключил дополнительные endpoints и привел состояния к единому поведению.",
        "techStack": ["React", "TypeScript", "REST API", "Tailwind CSS"],
        "role": "Доработка UI и логики, интеграция с API и исправление багов.",
        "images": ["/quasar-test-gamma.vercel.JPG"],
        "demoUrl": "https://quasar-test-gamma.vercel.app/#/",
    },
    {
        "id": "7",
        "title": "Горные лыжи",
        "category": "landing",
        "shortDescription": "Pet-проект лендинга о горнолыжном курорте с галереей и описанием трасс.",
        "fullDescription": "Собрал атмосферный лендинг с блоками о трассах, инструкторе и сезонных предложениях. Проработал визуальные акценты и адаптив для мобильных.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Верстка, адаптив, работа с изображениями и контентом.",
        "images": ["/skiing-frontend.vercel.JPG"],
        "demoUrl": "https://skiing-frontend.vercel.app/",
    },
    {
        "id": "8",
        "title": "ARES - корпоративный сайт",
        "category": "multipage",
        "shortDescription": "Многостраничный корпоративный сайт с услугами, кейсами и контактами.",
        "fullDescription": "Собрал структуру страниц, единые блоки и навигацию. Уделил внимание последовательной типографике и удобству чтения на разных экранах.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Frontend-разработка, композиция страниц и адаптив.",
        "images": ["/project-site-tau.vercel.JPG"],
        "demoUrl": "https://project-site-tau.vercel.app/",
    },
    {
        "id": "9",
        "title": "Портфолио на английском (доработка)",
        "category": "multipage",
        "shortDescription": "Доработка англоязычного портфолио: правки интерфейса и контента.",
        "fullDescription": "Обновил структуру секций, текст и визуальные элементы. Привел стили к единому виду и поправил адаптив для мобильных.",
        "techStack": ["React", "TypeScript", "Tailwind CSS"],
        "role": "Доработка UI, правки контента и адаптив.",
        "images": ["/alex-presents-elegance.lovable.app.JPG"],
        "demoUrl": "https://alex-presents-elegance.lovable.app/",
    },
    {
        "id": "10",
        "title": "Лендинг юриста",
        "category": "landing",
        "shortDescription": "Лендинг юридических услуг с акцентом на практику, кейсы и консультацию.",
        "fullDescription": "Собрал одностраничный сайт с блоками об услугах, опыте и отзывах. Продумал ясную структуру и удобную навигацию по секциям.",
        "techStack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "role": "Верстка, адаптив, настройка контента и визуальных блоков.",
        "images": ["/юрист.JPG"],
        "demoUrl": "https://greenleaf-law-hub.lovable.app/",
    },
    {
        "id": "11",
        "title": "Telegram-бот записи на массаж",
        "category": "service",
        "shortDescription": "Бот для записи клиентов с выбором услуги, времени и уведомлениями.",
        "fullDescription": "Реализовал сценарии записи, напоминаний и отмены, а также админ-часть для управления расписанием. Сделал аккуратную логику диалогов и обработку статусов.",
        "techStack": ["Python", "aiogram", "PostgreSQL", "Telegram Bot API"],
        "role": "Проектирование диалогов, разработка бота и интеграция с расписанием.",
        "images": ["/tg_bot_2.JPG"],
    },
    {
        "id": "12",
        "title": "Telegram-бот удаленного доступа к инфраструктуре",
        "category": "service",
        "shortDescription": "Служебный бот для безопасного доступа к внутренним сервисам и задачам.",
        "fullDescription": "Настроил роли и сценарии команд, логирование действий и контроль прав. Интегрировал с внутренним REST API и добавил понятные статусы выполнения.",
        "techStack": ["Python", "aiogram", "REST API", "Telegram Bot API"],
        "role": "Доработка логики, интеграция с API и настройка ролей.",
        "images": ["/tg_bot_1.JPG"],
    },
    {
        "id": "13",
        "title": "SaaS: сервис лояльности",
        "category": "service",
        "shortDescription": "Система лояльности с кабинетами, ролями и начислением/списанием баллов.",
        "fullDescription": "Сервис для работы с баллами и уровнями лояльности: кабинет клиента и админа, роли и права доступа. Поддержка QR/карты лояльности и история операций.",
        "techStack": ["React", "Node.js", "PostgreSQL", "REST API"],
        "role": "Frontend-логика и интеграция с API, проработка кабинета и ролей.",
        "images": ["/card_loyality.JPG"],
    },
    {
        "id": "14",
        "title": "TrackNode - SaaS аналитика сайтов",
        "category": "multipage",
        "shortDescription": "SaaS-платформа веб-аналитики с отслеживанием посещений, конверсий и SEO-аудитом.",
        "fullDescription": "Полноценная система аналитики: отслеживание визитов, уникальных пользователей, конверсий, источников трафика и поведения пользователей. Реализованы личные кабинеты клиентов, генерация PDF-отчетов, SEO-аудит и Telegram-уведомления. Архитектура построена как multi-tenant SaaS.",
        "techStack": ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Redis", "Celery", "Docker", "Nginx"],
        "role": "Проектирование архитектуры, backend (API, аналитика, multi-tenant), frontend-панель, деплой и DevOps.",
        "images": ["/tracknode.JPG"],
        "demoUrl": "https://tracknode.ru/",
        "results": "Реализована система отслеживания пользователей и событий, подключаемая к сторонним сайтам. Поддержка нескольких клиентов и изоляция данных.",
    },
    {
        "id": "15",
        "title": "Новое Конаково",
        "category": "multipage",
        "shortDescription": "Многостраничный сайт загородного пространства с расписанием, услугами и блогом.",
        "fullDescription": "Корпоративный сайт с динамическими страницами услуг, расписанием мероприятий, статьями и медиа-контентом. Реализована админ-панель на Django для управления контентом, тарифами и галереями. Проработана мобильная версия и UX.",
        "techStack": ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Docker"],
        "role": "Backend-разработка (модели, админка, API), frontend-интерфейс, архитектура проекта.",
        "images": ["/novoe-konakovo.JPG"],
        "demoUrl": "https://novoe-konakovo.ru/",
    },
    {
        "id": "16",
        "title": "E-Clock - интернет-магазин часов",
        "category": "multipage",
        "shortDescription": "Интернет-магазин часов с каталогом, карточками товаров и заявками.",
        "fullDescription": "E-commerce проект с каталогом товаров, карточками, фильтрацией и оформлением заказа. Реализована админ-панель для управления товарами и заявками. Интеграция с аналитикой и системой отслеживания поведения пользователей.",
        "techStack": ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Docker", "Nginx"],
        "role": "Полный цикл разработки: backend, frontend, интеграция аналитики и деплой.",
        "images": ["/e-clock.JPG"],
        "demoUrl": "http://e-clock.ru/",
    },
]

PROJECT_CATEGORIES = [
    {"id": "all", "label": "Все проекты"},
    {"id": "service", "label": "Сервисы"},
    {"id": "landing", "label": "Лендинги"},
    {"id": "multipage", "label": "Многостраничные"},
]

for project in PROJECTS:
    image_paths = project.get("images", [])
    project["techStack"] = [{"label": item} for item in project.get("techStack", [])]
    project["image"] = project.get("image") or (image_paths[0] if image_paths else "")
    project["image_alt"] = project.get("image_alt") or project.get("title", "")
    project["images"] = [{"src": item} for item in image_paths]

PORTFOLIO_CASES = [
    {
        "id": project["id"],
        "title": project["title"],
        "summary": project.get("fullDescription") or project.get("shortDescription", ""),
        "image": project.get("image", ""),
        "image_alt": project.get("image_alt", ""),
        "link": project.get("demoUrl", ""),
        "results": project.get("results", ""),
    }
    for project in PROJECTS[:6]
]

PORTFOLIO_GALLERY = [
    {
        "id": project["id"],
        "image": project.get("image", ""),
        "image_alt": project.get("image_alt", ""),
        "caption": project.get("title", ""),
    }
    for project in PROJECTS
    if project.get("image")
]

SKILL_GROUPS = [
    {"id": "frontend", "title": "Frontend", "icon": "code", "skills": [{"label": item} for item in ["Vue 3", "Composition API", "TypeScript", "HTML5 / CSS3", "Tailwind CSS", "Адаптивная верстка", "SPA-архитектура", "State Management", "Формы и валидация"]]},
    {"id": "backend", "title": "Backend", "icon": "server", "skills": [{"label": item} for item in ["Python", "Django", "Django REST Framework", "Flask", "REST API", "PostgreSQL", "SQLAlchemy", "Auth / Roles", "Redis / Celery"]]},
    {"id": "tools", "title": "Инструменты", "icon": "wrench", "skills": [{"label": item} for item in ["Git / GitHub", "Docker / Compose", "Linux / VPS", "Nginx", "CI/CD (basic)", "VS Code", "Postman", "Figma (базово)"]]},
    {"id": "practices", "title": "Практики", "icon": "book", "skills": [{"label": item} for item in ["Clean Code", "Рефакторинг", "Code Review", "Git Flow", "Документация", "Тестируемость", "API-контракты", "Agile / Kanban"]]},
]

SERVICE_CATEGORY_LABELS = {
    "development": "Разработка",
    "administration": "Администрирование",
    "technical_support": "Техническая помощь",
}

MY_PORTFOLIO_SERVICES = [
    {"id": "website", "title": "Разработка сайта", "description": "Современный сайт под задачи бизнеса: от идеи и дизайна до запуска.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "code", "is_active": True, "order": 10},
    {"id": "site-fixes", "title": "Доработка существующего сайта", "description": "Исправление интерфейса, логики, адаптивности и существующих функций.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "wrench", "is_active": True, "order": 20},
    {"id": "shop", "title": "Интернет-магазин", "description": "Каталог, карточки товаров, заявки, корзина и необходимые интеграции.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "briefcase", "is_active": True, "order": 30},
    {"id": "api-crm", "title": "API и CRM интеграции", "description": "Подключение внешних сервисов, CRM, форм, заявок и обмена данными.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "plug", "is_active": True, "order": 40},
    {"id": "telegram-bots", "title": "Telegram-боты", "description": "Боты для заявок, уведомлений, автоматизации и внутренних процессов.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "bot", "is_active": True, "order": 50},
    {"id": "automation", "title": "Автоматизация процессов", "description": "Автоматизация повторяющихся операций, интеграции и внутренние инструменты.", "category": "development", "category_label": SERVICE_CATEGORY_LABELS["development"], "icon": "zap", "is_active": True, "order": 60},
    {"id": "server-setup", "title": "Настройка сервера", "description": "Подготовка VPS или сервера, установка сервисов и настройка рабочего окружения.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "server", "is_active": True, "order": 110},
    {"id": "docker-compose", "title": "Docker и Docker Compose", "description": "Контейнеризация приложений, Compose-конфигурации и настройка окружения.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "settings", "is_active": True, "order": 120},
    {"id": "nginx", "title": "Nginx", "description": "Reverse proxy, домены, статика, маршрутизация и настройка веб-серверов.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "server", "is_active": True, "order": 130},
    {"id": "ssl", "title": "HTTPS / SSL", "description": "Установка сертификатов, HTTPS, редиректы и проверка безопасного соединения.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "shield", "is_active": True, "order": 140},
    {"id": "domains-dns", "title": "Домены и DNS", "description": "Настройка DNS-записей, поддоменов и привязка домена к серверу.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "globe-2", "is_active": True, "order": 150},
    {"id": "backup", "title": "Резервное копирование", "description": "Настройка резервных копий файлов, сервисов и баз данных.", "category": "administration", "category_label": SERVICE_CATEGORY_LABELS["administration"], "icon": "download", "is_active": True, "order": 160},
    {"id": "cryptopro-eds", "title": "КриптоПро и ЭЦП", "description": "Установка КриптоПро CSP, сертификатов и настройка электронной подписи.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "key", "is_active": True, "order": 210},
    {"id": "software-setup", "title": "Установка и настройка ПО", "description": "Установка программ, компонентов, драйверов и настройка рабочего окружения.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "download", "is_active": True, "order": 220},
    {"id": "windows-linux", "title": "Windows и Linux", "description": "Настройка системы, пользователей, прав доступа и решение программных проблем.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "settings", "is_active": True, "order": 230},
    {"id": "vpn-remote-access", "title": "VPN и удалённый доступ", "description": "Настройка VPN и безопасного удалённого подключения к компьютеру или серверу.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "network", "is_active": True, "order": 240},
    {"id": "network-equipment", "title": "Сеть и оборудование", "description": "Настройка сети, принтеров, сканеров и другого рабочего оборудования.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "settings", "is_active": True, "order": 250},
    {"id": "diagnostics-help", "title": "Диагностика и техническая помощь", "description": "Поиск причин ошибок и решение нестандартных программных и системных задач.", "category": "technical_support", "category_label": SERVICE_CATEGORY_LABELS["technical_support"], "icon": "activity", "is_active": True, "order": 260},
]


MY_PORTFOLIO_SECTION_SEEDS = [
    {
        "key": "settings",
        "title": "Общие настройки",
        "order": 1,
        "schema": {"fields": [
            field("site_title", "Заголовок сайта"),
            field("logo_text", "Логотип"),
            field("logo_image", "Изображение логотипа", "image"),
            field("description", "Описание", "textarea"),
            field("favicon", "Favicon", "image"),
            field("contacts", "Контакты", "repeater", fields=[field("icon", "Иконка"), field("label", "Название"), field("value", "Значение"), field("href", "Ссылка")]),
            field("nav_items", "Навигация", "repeater", fields=[field("label", "Текст"), field("href", "Ссылка")]),
        ]},
        "content": {
            "site_title": "Александр Тишечкин - Full-stack Web Developer",
            "logo_text": "Alexandr_Tishechkin",
            "logo_image": "",
            "description": "Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.",
            "favicon": "/favicon.ico",
            "contacts": CONTACTS,
            "nav_items": NAV_ITEMS,
        },
    },
    {
        "key": "hero",
        "title": "Первый экран",
        "order": 2,
        "schema": {"fields": [
            field("status_text", "Статус"),
            field("title", "Заголовок", "textarea"),
            field("accent_title", "Акцент"),
            field("subtitle", "Подзаголовок", "textarea"),
            field("portrait_image", "Фото разработчика", "image"),
            field("portrait_alt", "Alt-текст фото"),
            field("primary_button_text", "Текст основной кнопки"),
            field("primary_button_target", "Ссылка основной кнопки"),
            field("secondary_button_text", "Текст второй кнопки"),
            field("secondary_button_target", "Ссылка второй кнопки"),
            field("badges", "Бейджи", "repeater", fields=[field("icon", "Иконка"), field("label", "Текст")]),
        ]},
        "content": {
            "status_text": "Открыт для проектов",
            "title": "Создаю современные веб-приложения",
            "accent_title": "Web Developer",
            "subtitle": "Vue.js + Django - REST API - Fixing & Building Web Apps",
            "portrait_image": "",
            "portrait_alt": "Александр Тишечкин",
            "primary_button_text": "Смотреть проекты",
            "primary_button_target": "#projects",
            "secondary_button_text": "Связаться",
            "secondary_button_target": "#contact",
            "badges": [
                {"icon": "code", "label": "Fullstack"},
                {"icon": "briefcase", "label": "Проектная работа"},
                {"icon": "wrench", "label": "Поддержка / доработки"},
                {"icon": "user", "label": "Самозанятый"},
            ],
        },
    },
    {
        "key": "about",
        "title": "Обо мне и услуги",
        "order": 3,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("accent", "Акцент"),
            field("paragraphs", "Тексты", "repeater", fields=[field("text", "Абзац", "textarea")]),
            field("profile_image", "Фото или иллюстрация", "image"),
            field("profile_image_alt", "Alt-текст изображения"),
            field("services_title", "Заголовок услуг"),
            field("services", "Услуги", "repeater", fields=[field("icon", "Иконка"), field("title", "Название"), field("description", "Описание", "textarea")]),
        ]},
        "content": {
            "title": "Обо",
            "accent": "мне",
            "profile_image": "",
            "profile_image_alt": "",
            "paragraphs": [
                {"text": "Я fullstack-разработчик с опытом создания веб-приложений на стеке Vue.js + Django. Работаю с проектами от MVP до production-ready решений."},
                {"text": "Моя сильная сторона - быстро разбираться в чужом коде, находить и исправлять проблемы, доводить задачи до рабочего результата. Понимаю полный цикл разработки: от проектирования БД и API до frontend-компонентов и деплоя."},
                {"text": "Открыт для проектной работы, доработки существующих систем и долгосрочного сотрудничества."},
            ],
            "services_title": "Чем я могу помочь",
            "services": [
                {"icon": "code", "title": "Разработка веб-приложений", "description": "SPA, дашборды, CRM-системы под ваши бизнес-задачи"},
                {"icon": "refresh", "title": "Доработка и стабилизация", "description": "Исправление багов, рефакторинг, оптимизация legacy-кода"},
                {"icon": "plug", "title": "API и интеграции", "description": "REST API, webhooks, подключение внешних сервисов"},
                {"icon": "bot", "title": "Telegram-боты", "description": "Боты для автоматизации процессов и работы с клиентами"},
                {"icon": "server", "title": "Деплой и инфраструктура", "description": "VPS, Docker, Nginx - настройка и поддержка окружений"},
            ],
        },
    },
    {
        "key": "services",
        "title": "Услуги",
        "order": 4,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("accent", "Акцент"),
            field("description", "Описание", "textarea"),
            field("services", "Услуги", "repeater", fields=[
                field("id", "ID"),
                field("title", "Название"),
                field("description", "Описание", "textarea"),
                field("category", "Категория"),
                field("category_label", "Название категории"),
                field("icon", "Иконка"),
                field("is_active", "Активна", "boolean"),
                field("order", "Порядок", "number"),
            ]),
        ]},
        "content": {
            "title": "Услуги",
            "accent": "",
            "description": "Разработка, администрирование и техническая помощь — выберите нужное направление.",
            "services": MY_PORTFOLIO_SERVICES,
        },
    },
    {
        "key": "skills",
        "title": "Навыки",
        "order": 5,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("accent", "Акцент"),
            field("description", "Описание", "textarea"),
            field("groups", "Группы навыков", "repeater", fields=[field("id", "ID"), field("title", "Название"), field("icon", "Иконка"), field("skills", "Навыки", "repeater", fields=[field("label", "Навык")])]),
        ]},
        "content": {
            "title": "Технические",
            "accent": "навыки",
            "description": "Стек технологий, с которыми работаю ежедневно на уровне профессионала.",
            "groups": SKILL_GROUPS,
        },
    },
    {
        "key": "projects",
        "title": "Проекты",
        "order": 6,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("accent", "Акцент"),
            field("description", "Описание", "textarea"),
            field("categories", "Категории", "repeater", fields=[field("id", "ID"), field("label", "Название")]),
            field("projects", "Проекты", "repeater", fields=[
                field("id", "ID"),
                field("title", "Название"),
                field("category", "Категория"),
                field("shortDescription", "Короткое описание", "textarea"),
                field("fullDescription", "Полное описание", "textarea"),
                field("techStack", "Стек", "repeater", fields=[field("label", "Технология")]),
                field("role", "Роль", "textarea"),
                field("image", "Главное изображение", "image"),
                field("image_alt", "Alt-текст изображения"),
                field("images", "Дополнительные изображения", "repeater", fields=[field("src", "Путь", "image")]),
                field("demoUrl", "Demo URL"),
                field("repoUrl", "Repo URL"),
                field("results", "Результат", "textarea"),
            ]),
        ]},
        "content": {
            "title": "Мои",
            "accent": "проекты",
            "description": "Примеры работ из разных сфер - от сервисов и дашбордов до лендингов",
            "categories": PROJECT_CATEGORIES,
            "projects": PROJECTS,
        },
    },
    {
        "key": "why-me",
        "title": "Почему я",
        "order": 7,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("accent", "Акцент"),
            field("description", "Описание", "textarea"),
            field("reasons", "Причины", "repeater", fields=[field("icon", "Иконка"), field("text", "Текст", "textarea")]),
        ]},
        "content": {
            "title": "Почему",
            "accent": "я подойду",
            "description": "Качества, которые ценят работодатели и заказчики",
            "reasons": [
                {"icon": "code", "text": "Быстро разбираюсь в чужом коде и legacy-проектах"},
                {"icon": "target", "text": "Довожу задачи до рабочего результата"},
                {"icon": "layout", "text": "Понимаю полный цикл: frontend + backend + деплой"},
                {"icon": "users", "text": "Умею оценивать сроки/риски, коммуницировать с командой"},
                {"icon": "shield", "text": "Аккуратность к деталям UI и API-контрактам"},
                {"icon": "zap", "text": "Могу брать ответственность за модуль или фичу"},
                {"icon": "bug", "text": "Умею фиксить прод-проблемы и стабилизировать систему"},
            ],
        },
    },
    {
        "key": "checklist",
        "title": "Чек-лист компетенций",
        "order": 8,
        "schema": {"fields": [
            field("title", "Заголовок", "textarea"),
            field("accent", "Акцент"),
            field("description", "Описание", "textarea"),
            field("items", "Пункты", "repeater", fields=[field("text", "Текст", "textarea")]),
        ]},
        "content": {
            "title": "Компетенции, закрывающие задачи",
            "accent": "веб-разработки",
            "description": "Чек-лист компетенций, которыми я владею",
            "items": [
                {"text": "Самостоятельно реализовывать фичи end-to-end (UI -> API -> БД)"},
                {"text": "Работать с Git-ветками, PR, код-ревью"},
                {"text": "Понимать архитектуру проекта, слои, разделение ответственности"},
                {"text": "Уверенно работать с REST, статус-кодами, контрактами, валидацией"},
                {"text": "Уметь диагностировать баги (логи, воспроизведение, фиксы)"},
                {"text": "Писать понятный код, соблюдать стиль, делать рефакторинг"},
                {"text": "Базово понимать деплой и окружения (dev/stage/prod)"},
                {"text": "Коммуницировать: уточнять требования, предлагать решения, оценивать сроки"},
            ],
        },
    },
    {
        "key": "contact",
        "title": "Контакты",
        "order": 9,
        "schema": {"fields": [
            field("title", "Заголовок"),
            field("description", "Описание", "textarea"),
            field("contacts", "Контакты", "repeater", fields=[field("icon", "Иконка"), field("label", "Название"), field("value", "Значение"), field("href", "Ссылка")]),
        ]},
        "content": {
            "title": "Контакты",
            "description": "Свяжитесь со мной удобным способом - я отвечу на все вопросы.",
            "contacts": CONTACTS,
        },
    },
    {
        "key": "footer",
        "title": "Footer",
        "order": 10,
        "schema": {"fields": [
            field("logo_text", "Логотип"),
            field("logo_image", "Изображение логотипа", "image"),
            field("description", "Описание", "textarea"),
            field("nav_title", "Заголовок навигации"),
            field("contact_title", "Заголовок контактов"),
            field("nav_items", "Навигация", "repeater", fields=[field("label", "Текст"), field("href", "Ссылка")]),
            field("social_links", "Соцсети", "repeater", fields=[field("icon", "Иконка"), field("label", "Название"), field("href", "Ссылка")]),
            field("copyright", "Copyright"),
        ]},
        "content": {
            "logo_text": "Alexandr_Tishechkin",
            "logo_image": "",
            "description": "Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.",
            "nav_title": "Навигация",
            "contact_title": "Связаться",
            "nav_items": NAV_ITEMS,
            "social_links": [
                {"icon": "github", "label": "GitHub", "href": "https://github.com/m1ke1994"},
                {"icon": "message", "label": "Telegram", "href": "https://t.me/M1ke994"},
                {"icon": "mail", "label": "Email", "href": "mailto:Tishechkin1994@gmail.com"},
                {"icon": "instagram", "label": "Instagram", "href": "https://instagram.com/alexandr_tishechkin"},
            ],
            "copyright": "Все права защищены. Разработано с",
        },
    },
]


def _section_seed(section_key: str) -> dict:
    for seed in MY_PORTFOLIO_SECTION_SEEDS:
        if seed["key"] == section_key:
            return seed
    raise KeyError(section_key)


def _append_field_once(fields: list[dict], payload: dict, *, after: str | None = None) -> None:
    if any(field.get("key") == payload.get("key") for field in fields):
        return
    if after:
        for index, field_payload in enumerate(fields):
            if field_payload.get("key") == after:
                fields.insert(index + 1, payload)
                return
    fields.append(payload)


def _repeater_fields(seed: dict, repeater_key: str) -> list[dict]:
    for payload in seed["schema"]["fields"]:
        if payload.get("key") == repeater_key and payload.get("type") == "repeater":
            return payload.setdefault("fields", [])
    raise KeyError(f"{seed['key']}.{repeater_key}")


def _extend_portfolio_media_schema() -> None:
    skills = _section_seed("skills")
    _append_field_once(skills["schema"]["fields"], field("illustration_image", "Section image", "image"), after="description")
    _append_field_once(skills["schema"]["fields"], field("illustration_alt", "Section image alt"), after="illustration_image")
    skills["content"].setdefault("illustration_image", "")
    skills["content"].setdefault("illustration_alt", "")
    skill_group_fields = _repeater_fields(skills, "groups")
    _append_field_once(skill_group_fields, field("image", "Group image", "image"), after="icon")
    _append_field_once(skill_group_fields, field("image_alt", "Group image alt"), after="image")

    why_me = _section_seed("why-me")
    _append_field_once(why_me["schema"]["fields"], field("illustration_image", "Section image", "image"), after="description")
    _append_field_once(why_me["schema"]["fields"], field("illustration_alt", "Section image alt"), after="illustration_image")
    why_me["content"].setdefault("illustration_image", "")
    why_me["content"].setdefault("illustration_alt", "")
    reason_fields = _repeater_fields(why_me, "reasons")
    _append_field_once(reason_fields, field("image", "Reason image", "image"), after="icon")
    _append_field_once(reason_fields, field("image_alt", "Reason image alt"), after="image")

    checklist = _section_seed("checklist")
    _append_field_once(checklist["schema"]["fields"], field("illustration_image", "Section image", "image"), after="description")
    _append_field_once(checklist["schema"]["fields"], field("illustration_alt", "Section image alt"), after="illustration_image")
    checklist["content"].setdefault("illustration_image", "")
    checklist["content"].setdefault("illustration_alt", "")
    item_fields = _repeater_fields(checklist, "items")
    _append_field_once(item_fields, field("image", "Item image", "image"))
    _append_field_once(item_fields, field("image_alt", "Item image alt"), after="image")

    contact = _section_seed("contact")
    _append_field_once(contact["schema"]["fields"], field("contact_image", "Contact image", "image"), after="description")
    _append_field_once(contact["schema"]["fields"], field("contact_image_alt", "Contact image alt"), after="contact_image")
    contact["content"].setdefault("contact_image", "")
    contact["content"].setdefault("contact_image_alt", "")
    contact["order"] = 10

    _section_seed("footer")["order"] = 11


MY_PORTFOLIO_SECTION_SEEDS.extend(
    [
        {
            "key": "cases",
            "title": "Cases",
            "order": 8,
            "schema": {"fields": [
                field("title", "Title"),
                field("accent", "Accent"),
                field("description", "Description", "textarea"),
                field("cases", "Cases", "repeater", fields=[
                    field("id", "ID"),
                    field("title", "Title"),
                    field("summary", "Summary", "textarea"),
                    field("image", "Image", "image"),
                    field("image_alt", "Image alt"),
                    field("link", "Link"),
                    field("results", "Results", "textarea"),
                ]),
            ]},
            "content": {
                "title": "Cases",
                "accent": "and results",
                "description": "Selected work with editable images, summaries, and links.",
                "cases": PORTFOLIO_CASES,
            },
        },
        {
            "key": "gallery",
            "title": "Gallery",
            "order": 9,
            "schema": {"fields": [
                field("title", "Title"),
                field("description", "Description", "textarea"),
                field("images", "Images", "repeater", fields=[
                    field("id", "ID"),
                    field("image", "Image", "image"),
                    field("image_alt", "Image alt"),
                    field("caption", "Caption"),
                ]),
            ]},
            "content": {
                "title": "Gallery",
                "description": "Editable project screenshots and visual materials.",
                "images": PORTFOLIO_GALLERY,
            },
        },
    ]
)

_extend_portfolio_media_schema()


def get_my_portfolio_schema_key(section_key: str, site_slug: str = MY_PORTFOLIO_SITE_SLUG) -> str:
    return f"{site_slug}-{section_key}"
