from copy import deepcopy


VOLGA_SITE_SLUG = "novaya-konakova"
VOLGA_SITE_NAME = "Новая Конакова"
VOLGA_SITE_DOMAIN = "novoe-konakovo.ru"


def field(key, label, field_type="text", default="", **extra):
    return {
        "key": key,
        "label": label,
        "type": field_type,
        "default": deepcopy(default),
        **extra,
    }


def repeater(key, label, fields, default=None, **extra):
    return field(
        key,
        label,
        "repeater",
        [] if default is None else default,
        fields=fields,
        **extra,
    )


def text_block_fields():
    return [
        field("title", "Заголовок"),
        field("text", "Текст", "textarea"),
    ]


SECTION_TITLES = {
    "hero": "Hero-блок",
    "site-settings": "Контакты и настройки",
    "navigation": "Навигация",
    "services": "Услуги и форматы",
    "schedule": "Расписание",
    "reviews": "Отзывы",
    "articles": "Статьи и видео",
    "news": "Новости",
    "pages": "Страницы",
    "footer": "Подвал сайта",
}


NAVIGATION_ITEMS = [
    {"label": "Обо мне", "to": "/about", "href": ""},
    {"label": "Братство Лосей", "to": "/brotherhood", "href": ""},
    {"label": "Волонтерские программы", "to": "/volunteer", "href": ""},
    {"label": "Беговой клуб", "to": "/running-club", "href": ""},
    {"label": "Услуги", "to": "", "href": "/#services"},
    {"label": "Новости", "to": "/news", "href": ""},
    {"label": "Расписание", "to": "/schedule", "href": ""},
    {"label": "Контакты", "to": "/contacts", "href": ""},
]


SERVICES = [
    {
        "id": "moose",
        "slug": "moose",
        "title": "Экскурсия в Братство Лосей",
        "full_title": "Экскурсия в «Братство Лосей»",
        "description": "Заповедный маршрут, живые истории о природе и глубокое погружение в ритм местности.",
        "duration_label": "3-4 часа",
        "image": "/images/service-moose-cover.jpg",
        "intro": (
            "Авторская экскурсия для тех, кто хочет не просто пройти по маршруту, а прочувствовать "
            "пространство: от тишины леса до живого диалога с проводником и группой."
        ),
        "note": "Рекомендуем удобную обувь и ветровку по погоде. Детали встречи направляем после подтверждения.",
        "order": 10,
        "is_category": False,
        "children": [],
        "images": [
            {"id": "moose-1", "image_url": "/images/service-moose-1.jpg", "order": 10},
            {"id": "moose-2", "image_url": "/images/service-moose-2.jpg", "order": 20},
            {"id": "moose-3", "image_url": "/images/service-moose-3.jpg", "order": 30},
        ],
        "content_sections": [
            {
                "title": "Как проходит программа",
                "text": (
                    "Мы начинаем встречу с короткого знакомства и настройки темпа, чтобы всем участникам "
                    "было комфортно в группе.\n\nМаршрут включает лесную часть, выход к воде и финальную "
                    "рефлексию с рекомендациями по восстановлению."
                ),
            },
            {
                "title": "Кому подходит",
                "text": (
                    "Формат открыт для новичков и семейных групп, не требует спортивной подготовки.\n\n"
                    "Для команд и пар можно провести закрытую версию маршрута с акцентом на ваш запрос."
                ),
            },
        ],
        "tariffs": [
            {
                "id": "moose-standard",
                "slug": "standard",
                "title": "Стандартная экскурсия",
                "description": "Групповой формат до 8 человек с проводником и чаем на привале.",
                "duration": "3 часа",
                "price": 2500,
                "order": 10,
            },
            {
                "id": "moose-extended",
                "slug": "extended",
                "title": "Расширенный маршрут",
                "description": "Дополнительные точки маршрута и практики на внимание к телу и дыханию.",
                "duration": "4 часа",
                "price": 3600,
                "order": 20,
            },
            {
                "id": "moose-family",
                "slug": "family",
                "title": "Семейный формат",
                "description": "Мягкий темп и адаптация маршрута для семьи с детьми.",
                "duration": "4 часа",
                "price": 4200,
                "order": 30,
            },
            {
                "id": "moose-individual",
                "slug": "individual",
                "title": "Индивидуальная экскурсия",
                "description": "Персональный маршрут, фото-точки и разбор под ваши цели.",
                "duration": "3 часа",
                "price": 5000,
                "order": 40,
            },
        ],
    },
    {
        "id": "author",
        "slug": "author",
        "title": "Авторские программы",
        "full_title": "Авторские программы «Новое Конаково»",
        "description": "Сценарные однодневные и двухдневные программы с персональной настройкой под запрос.",
        "duration_label": "2-6 часов",
        "image": "/images/service-tea-cover.jpg",
        "intro": (
            "Авторские программы собираются как конструктор: ритм дня, практики, маршруты и форматы "
            "общения выбираются под вашу команду или семью."
        ),
        "note": "Возможна адаптация сценария по уровню нагрузки, возрасту и численности группы.",
        "order": 20,
        "is_category": False,
        "children": [],
        "images": [
            {"id": "author-1", "image_url": "/images/service-tea-1.jpg", "order": 10},
            {"id": "author-2", "image_url": "/images/service-tea-2.jpg", "order": 20},
            {"id": "author-3", "image_url": "/images/service-tea-3.jpg", "order": 30},
        ],
        "content_sections": [
            {
                "title": "Что входит",
                "text": (
                    "Перед встречей проводим короткое интервью и собираем карту задач: отдых, фокус, "
                    "командное взаимодействие.\n\nВнутри программы можно сочетать прогулки, практики, "
                    "чайный формат и модерацию групповых обсуждений."
                ),
            },
            {
                "title": "Результат",
                "text": (
                    "Вы получаете согласованный сценарий дня с понятным таймингом и ролями участников.\n\n"
                    "После программы отправляем рекомендации для самостоятельной практики и дальнейшей интеграции."
                ),
            },
        ],
        "tariffs": [
            {
                "id": "author-basic",
                "slug": "basic",
                "title": "Базовый сценарий",
                "description": "Готовый шаблон программы с одной активностью на выбор.",
                "duration": "2 часа",
                "price": 3200,
                "order": 10,
            },
            {
                "id": "author-moderation",
                "slug": "moderation",
                "title": "Сценарий + модерация",
                "description": "Персональная настройка и сопровождение ведущего на протяжении всей встречи.",
                "duration": "4 часа",
                "price": 4700,
                "order": 20,
            },
            {
                "id": "author-team",
                "slug": "team",
                "title": "Командный формат",
                "description": "Программа для команды до 12 человек с адаптацией под цели коллектива.",
                "duration": "5 часов",
                "price": 6200,
                "order": 30,
            },
            {
                "id": "author-retreat",
                "slug": "retreat",
                "title": "Ретрит-день",
                "description": "Однодневный формат с перерывами, практиками и финальной сборкой выводов.",
                "duration": "6 часов",
                "price": 7800,
                "order": 40,
            },
        ],
    },
    {
        "id": "master",
        "slug": "master",
        "title": "Мастер-классы",
        "full_title": "Мастер-классы и практические форматы",
        "description": "Камерные занятия с ведущим: от телесных практик до креативных форматов.",
        "duration_label": "90-180 минут",
        "image": "/images/service-energy-cover.jpg",
        "intro": (
            "Мастер-класс построен вокруг практики и обратной связи. Участники получают не только опыт "
            "на месте, но и инструменты для самостоятельной работы."
        ),
        "note": "Тему мастер-класса и уровень сложности согласовываем заранее.",
        "order": 30,
        "is_category": False,
        "children": [],
        "images": [
            {"id": "master-1", "image_url": "/images/service-energy-1.jpg", "order": 10},
            {"id": "master-2", "image_url": "/images/service-energy-2.jpg", "order": 20},
        ],
        "content_sections": [
            {
                "title": "Формат занятия",
                "text": (
                    "Каждый мастер-класс состоит из вводного блока, основной практики и финального круга "
                    "обратной связи.\n\nПри необходимости добавляем методические материалы и персональные чек-листы."
                ),
            },
            {
                "title": "Для кого",
                "text": (
                    "Подходит новичкам, малым группам и командам, которым нужен практичный формат без "
                    "перегруза теорией.\n\nУровень сложности и темп адаптируются под состав группы."
                ),
            },
        ],
        "tariffs": [
            {
                "id": "master-standard",
                "slug": "standard",
                "title": "Стандартный мастер-класс",
                "description": "Группа до 10 человек, базовая программа и материалы.",
                "duration": "90 минут",
                "price": 2800,
                "order": 10,
            },
            {
                "id": "master-feedback",
                "slug": "feedback",
                "title": "Практика + разбор",
                "description": "Расширенный формат с индивидуальной обратной связью по участникам.",
                "duration": "120 минут",
                "price": 3900,
                "order": 20,
            },
            {
                "id": "master-intensive",
                "slug": "intensive",
                "title": "Интенсив",
                "description": "Углубленный блок с дополнительными упражнениями и сопровождением.",
                "duration": "180 минут",
                "price": 5200,
                "order": 30,
            },
            {
                "id": "master-individual",
                "slug": "individual",
                "title": "Индивидуальный формат",
                "description": "Персональный мастер-класс 1:1 с программой под ваш запрос.",
                "duration": "120 минут",
                "price": 6100,
                "order": 40,
            },
        ],
    },
    {
        "id": "running",
        "slug": "running",
        "title": "Беговые встречи",
        "full_title": "Беговой клуб «Новое Конаково»",
        "description": "Мягкие беговые форматы по живописным маршрутам с акцентом на технику и восстановление.",
        "duration_label": "60-120 минут",
        "image": "/images/service-moose-cover.jpg",
        "intro": (
            "Беговые встречи помогают встроить движение в устойчивый ритм. Мы сочетаем разминку, "
            "технику, маршрут и восстановительный блок."
        ),
        "note": "Берите удобную обувь и одежду по погоде. При необходимости корректируем дистанцию на месте.",
        "order": 40,
        "is_category": False,
        "children": [],
        "images": [
            {"id": "running-1", "image_url": "/images/service-moose-2.jpg", "order": 10},
            {"id": "running-2", "image_url": "/images/service-moose-1.jpg", "order": 20},
            {"id": "running-3", "image_url": "/images/service-moose-3.jpg", "order": 30},
        ],
        "content_sections": [
            {
                "title": "Как построена встреча",
                "text": (
                    "Стартуем с разогрева и техники, затем выходим на маршрут с контролем темпа и самочувствия.\n\n"
                    "Завершаем восстановлением, дыханием и коротким разбором ощущений после бега."
                ),
            },
            {
                "title": "Польза",
                "text": (
                    "Регулярные встречи повышают выносливость, улучшают технику и снижают риск перегрузки.\n\n"
                    "Подходит как для начинающих, так и для участников с опытом."
                ),
            },
        ],
        "tariffs": [
            {
                "id": "running-open",
                "slug": "open",
                "title": "Открытая встреча",
                "description": "Групповой формат с маршрутом и разбором техники.",
                "duration": "60 минут",
                "price": 1400,
                "order": 10,
            },
            {
                "id": "running-technique",
                "slug": "technique",
                "title": "Техника бега",
                "description": "Фокус на постановке шага, работе корпуса и дыхании.",
                "duration": "90 минут",
                "price": 2100,
                "order": 20,
            },
            {
                "id": "running-route",
                "slug": "route",
                "title": "Длинный маршрут",
                "description": "Увеличенная дистанция с контрольными остановками и сопровождением.",
                "duration": "120 минут",
                "price": 2900,
                "order": 30,
            },
            {
                "id": "running-personal",
                "slug": "personal",
                "title": "Персональная тренировка",
                "description": "Индивидуальный план, разбор видео и домашние задания.",
                "duration": "90 минут",
                "price": 3800,
                "order": 40,
            },
        ],
    },
]


PAGES = [
    {
        "slug": "about",
        "title": "Обо мне",
        "subtitle": "История проекта, ценности и подход к работе с людьми и местом.",
        "hero_image": "/card.png",
        "order": 0,
        "sections": [
            {
                "title": "Как появился проект",
                "text": (
                    "Новое Конаково выросло из практики маленьких встреч и маршрутов по местам, "
                    "где можно замедлиться, услышать себя и побыть в живом диалоге с природой."
                ),
                "order": 0,
            },
            {
                "title": "Во что я верю",
                "text": (
                    "Мне важны бережность к человеку, уважение к ритму группы и ясная структура программы, "
                    "в которой есть место свободе, тишине и совместному опыту."
                ),
                "order": 1,
            },
            {
                "title": "Что вы получите",
                "text": (
                    "На странице и в программах вы найдете понятные форматы участия: от авторских маршрутов "
                    "до камерных практик, с прозрачной организацией и сопровождением."
                ),
                "order": 2,
            },
        ],
        "gallery": [
            {"id": "about-1", "image": "/1.jpeg", "order": 0},
            {"id": "about-2", "image": "/2.jpeg", "order": 1},
            {"id": "about-3", "image": "/3.jpeg", "order": 2},
        ],
    },
    {
        "slug": "brotherhood",
        "title": "Братство Лосей",
        "subtitle": "Экскурсии и встречи в ритме природы: наблюдение, движение и живой контакт с местом.",
        "hero_image": "/images/service-moose-cover.jpg",
        "order": 1,
        "sections": [
            {
                "title": "Формат встреч",
                "text": "Программы собираются в спокойном темпе: прогулки по маршрутам, короткие остановки и совместные практики внимания.",
                "order": 0,
            },
            {
                "title": "Что важно",
                "text": "Главный акцент на безопасной атмосфере, взаимной поддержке и возможности перезагрузиться без спешки.",
                "order": 1,
            },
            {
                "title": "Результат",
                "text": "После встреч участники уносят с собой чувство ясности, устойчивости и желание возвращаться к этому ритму.",
                "order": 2,
            },
        ],
        "gallery": [
            {"id": "brotherhood-1", "image": "/images/service-moose-1.jpg", "order": 0},
            {"id": "brotherhood-2", "image": "/images/service-moose-2.jpg", "order": 1},
            {"id": "brotherhood-3", "image": "/images/service-moose-3.jpg", "order": 2},
        ],
    },
    {
        "slug": "volunteers",
        "title": "Волонтерские программы",
        "subtitle": "Практические форматы участия в развитии пространства: от разовых выездов до регулярного участия.",
        "hero_image": "/5.jpeg",
        "order": 2,
        "sections": [
            {
                "title": "Как устроено участие",
                "text": "Каждый волонтерский день включает вводный брифинг, практический блок и короткое подведение итогов.",
                "order": 0,
            },
            {
                "title": "Поддержка команды",
                "text": "Участникам доступны понятные задачи, сопровождение координаторов и комфортный вход без перегруза.",
                "order": 1,
            },
            {
                "title": "Гибкий формат",
                "text": "Можно выбрать удобный режим: разовое участие, ежемесячный выезд или сезонную серию задач.",
                "order": 2,
            },
        ],
        "gallery": [
            {"id": "volunteers-1", "image": "/6.jpeg", "order": 0},
            {"id": "volunteers-2", "image": "/7.jpeg", "order": 1},
            {"id": "volunteers-3", "image": "/8.jpeg", "order": 2},
        ],
    },
    {
        "slug": "running-club",
        "title": "Беговой клуб",
        "subtitle": "Сообщество регулярных тренировок в природном ритме: с поддержкой, без давления и с устойчивой динамикой.",
        "hero_image": "/images/service-energy-cover.jpg",
        "order": 3,
        "sections": [
            {
                "title": "Идея клуба",
                "text": "Тренировки ориентированы на регулярность и бережную нагрузку, которую легко встроить в повседневную жизнь.",
                "order": 0,
            },
            {
                "title": "Структура занятия",
                "text": "Каждая встреча включает разминку, основной блок и мягкое восстановление с учетом уровня группы.",
                "order": 1,
            },
            {
                "title": "Эффект регулярности",
                "text": "Участники отмечают рост выносливости, более ровное состояние и устойчивую мотивацию тренироваться в команде.",
                "order": 2,
            },
        ],
        "gallery": [
            {"id": "running-1", "image": "/images/service-energy-1.jpg", "order": 0},
            {"id": "running-2", "image": "/images/service-energy-2.jpg", "order": 1},
            {"id": "running-3", "image": "/9.jpeg", "order": 2},
        ],
    },
]


ARTICLES = [
    {
        "title": "Как выбрать формат отдыха в Конаково",
        "slug": "kak-vybrat-format-otdyha",
        "preview_image": "/images/article-1.jpg",
        "preview_description": "Короткий гид по маршрутам, программам и камерным форматам проекта.",
        "content": (
            "Начните с простого вопроса: сколько у вас времени и какой ритм сейчас нужен. "
            "Для мягкого знакомства подойдет короткая прогулка, для перезагрузки - авторская программа "
            "с несколькими блоками.\n\nЕсли вы едете группой, заранее определите общий запрос: отдых, "
            "движение, тишина или командное взаимодействие. Это помогает собрать день без перегруза."
        ),
        "content_type": "article",
        "video_url": "",
        "published_date": "2026-02-12",
        "created_at": "2026-02-12T10:00:00+03:00",
    },
    {
        "title": "Сценарий дня: прогулка, практика и чай",
        "slug": "scenariy-dnya-progulka-praktika-chay",
        "preview_image": "/images/article-2.jpg",
        "preview_description": "Пример спокойной программы, которую можно адаптировать под группу.",
        "content": (
            "Хороший сценарий дня держится на трех опорах: понятный маршрут, паузы для восстановления "
            "и один главный акцент. Например, прогулка у воды, дыхательная практика и чайный формат "
            "дают достаточно впечатлений без ощущения спешки.\n\nВажна не плотность программы, а ясная "
            "последовательность и комфортный темп."
        ),
        "content_type": "article",
        "video_url": "",
        "published_date": "2026-02-18",
        "created_at": "2026-02-18T10:00:00+03:00",
    },
    {
        "title": "Видео: как проходит встреча",
        "slug": "video-kak-prohodit-vstrecha",
        "preview_image": "/images/video-1.jpg",
        "preview_description": "Короткое видео о структуре встречи и атмосфере программы.",
        "content": "Видео помогает заранее почувствовать темп встречи и понять, подойдет ли формат именно вам.",
        "content_type": "video",
        "video_url": "https://www.youtube.com/embed/ScMzIvxBSi4",
        "published_date": "2026-02-24",
        "created_at": "2026-02-24T10:00:00+03:00",
    },
    {
        "title": "Почему важны паузы в маршруте",
        "slug": "pochemu-vazhny-pauzy-v-marshrute",
        "preview_image": "/images/article-3.jpg",
        "preview_description": "О том, как короткие остановки делают программу глубже и спокойнее.",
        "content": (
            "Паузы нужны не только для отдыха. Они помогают участникам заметить состояние, задать вопросы "
            "и не превращать маршрут в гонку за точками.\n\nВ хорошей программе остановки встроены заранее: "
            "для разговора, чая, фотографии или простой тишины."
        ),
        "content_type": "article",
        "video_url": "",
        "published_date": "2026-03-02",
        "created_at": "2026-03-02T10:00:00+03:00",
    },
    {
        "title": "Видео: утренняя практика",
        "slug": "video-utrennyaya-praktika",
        "preview_image": "/images/video-2.jpg",
        "preview_description": "Небольшой фрагмент практики для включения тела и внимания.",
        "content": "Мягкое начало дня помогает выстроить спокойный ритм и не перегрузить программу.",
        "content_type": "video",
        "video_url": "https://www.youtube.com/embed/ysz5S6PUM-U",
        "published_date": "2026-03-10",
        "created_at": "2026-03-10T10:00:00+03:00",
    },
]


NEWS = [
    {
        "id": 1,
        "title": "Открыта запись на летние маршруты",
        "slug": "letnie-marshruty",
        "description": "Появились новые даты прогулок, программ и камерных встреч.",
        "image": "/images/news1.jpg",
        "published_date": "2026-06-20",
        "content": (
            "Мы открыли запись на летние маршруты и авторские программы. В расписании появятся новые "
            "даты для индивидуальных и групповых форматов.\n\nЕсли вы планируете поездку заранее, "
            "оставьте заявку - поможем выбрать подходящий сценарий."
        ),
    },
    {
        "id": 2,
        "title": "Добавлены новые форматы мастер-классов",
        "slug": "novye-master-klassy",
        "description": "В программе появились практические занятия для малых групп.",
        "image": "/images/news2.jpg",
        "published_date": "2026-06-16",
        "content": (
            "Мы расширили блок мастер-классов: теперь можно выбрать камерное занятие, практику с разбором "
            "или индивидуальный формат.\n\nТемы и уровень сложности согласовываются заранее."
        ),
    },
    {
        "id": 3,
        "title": "Обновлено расписание занятий",
        "slug": "obnovleno-raspisanie",
        "description": "В календарь добавлены даты на июль и август.",
        "image": "/images/news3.jpg",
        "published_date": "2026-06-12",
        "content": "Расписание обновлено: добавлены новые встречи, прогулки и практики на ближайшие месяцы.",
    },
    {
        "id": 4,
        "title": "Появился конструктор сценария дня",
        "slug": "konstruktor-scenariya-dnya",
        "description": "Теперь можно собрать программу из нескольких услуг и отправить заявку.",
        "image": "/images/news4.jpg",
        "published_date": "2026-06-07",
        "content": (
            "На главной странице появился конструктор сценария дня. Выберите интересные форматы, укажите "
            "дату и количество гостей - заявка попадет в Ядро."
        ),
    },
    {
        "id": 5,
        "title": "Новые материалы в разделе статей",
        "slug": "novye-materialy",
        "description": "Опубликованы тексты и видео о маршрутах, практиках и подготовке к поездке.",
        "image": "/images/news5.jpg",
        "published_date": "2026-06-01",
        "content": "Раздел статей и видео пополнился новыми материалами для гостей проекта.",
    },
]


REVIEWS = [
    {
        "id": "review-1",
        "name": "Анна",
        "event_name": "Авторская программа",
        "rating": 5,
        "text": "Очень спокойный и продуманный день. Было ощущение, что маршрут собран именно под наш ритм.",
        "date": "2026-05-22",
        "avatar": "/avatar.png",
    },
    {
        "id": "review-2",
        "name": "Мария",
        "event_name": "Экскурсия",
        "rating": 5,
        "text": "Понравилась бережная подача, много живых деталей и отсутствие спешки.",
        "date": "2026-05-18",
        "avatar": "/avatar.png",
    },
    {
        "id": "review-3",
        "name": "Ирина",
        "event_name": "Мастер-класс",
        "rating": 5,
        "text": "Камерный формат, понятная структура и много внимания к состоянию участников.",
        "date": "2026-05-10",
        "avatar": "/avatar.png",
    },
]


SCHEDULE = [
    {
        "month": "Июль 2026",
        "year": 2026,
        "month_number": 7,
        "days": [
            {
                "date": "2026-07-04",
                "weekday": "Суббота",
                "events": [
                    {
                        "id": "2026-07-04-1",
                        "time_start": "10:00",
                        "time_end": "13:00",
                        "title": "Экскурсия в Братство лосей",
                        "category": "Экскурсия",
                        "description": "Маршрут по природной зоне с проводником и остановками в ключевых точках.",
                        "price": 3200,
                        "color": "#6BA368",
                        "image": "/images/service-moose-cover.jpg",
                    },
                    {
                        "id": "2026-07-04-2",
                        "time_start": "15:00",
                        "time_end": "17:00",
                        "title": "Чайная церемония",
                        "category": "Авторская программа",
                        "description": "Камерный формат с практикой внимания и спокойным ритмом.",
                        "price": 2800,
                        "color": "#E9B949",
                        "image": "/images/service-tea-cover.jpg",
                    },
                ],
            },
            {
                "date": "2026-07-12",
                "weekday": "Воскресенье",
                "events": [
                    {
                        "id": "2026-07-12-1",
                        "time_start": "09:00",
                        "time_end": "10:30",
                        "title": "Беговой клуб",
                        "category": "Спорт",
                        "description": "Легкая тренировка с акцентом на технику, темп и восстановление.",
                        "price": 1400,
                        "color": "#C88B3A",
                        "image": "/images/service-energy-cover.jpg",
                    }
                ],
            },
            {
                "date": "2026-07-25",
                "weekday": "Суббота",
                "events": [
                    {
                        "id": "2026-07-25-1",
                        "time_start": "11:00",
                        "time_end": "14:00",
                        "title": "Мастер-класс по дыханию",
                        "category": "Мастер-класс",
                        "description": "Практика для фокуса, снижения напряжения и восстановления энергии.",
                        "price": 2600,
                        "color": "#7AA2F7",
                        "image": "/images/service-energy-1.jpg",
                    }
                ],
            },
        ],
    },
    {
        "month": "Август 2026",
        "year": 2026,
        "month_number": 8,
        "days": [
            {
                "date": "2026-08-08",
                "weekday": "Суббота",
                "events": [
                    {
                        "id": "2026-08-08-1",
                        "time_start": "12:00",
                        "time_end": "16:00",
                        "title": "Авторская программа",
                        "category": "Авторская программа",
                        "description": "Сценарный дневной формат с прогулкой, практикой и финальной сборкой.",
                        "price": 4700,
                        "color": "#E9B949",
                        "image": "/images/service-tea-1.jpg",
                    }
                ],
            },
            {
                "date": "2026-08-22",
                "weekday": "Суббота",
                "events": [
                    {
                        "id": "2026-08-22-1",
                        "time_start": "10:00",
                        "time_end": "13:00",
                        "title": "Вечерний маршрут у воды",
                        "category": "Экскурсия",
                        "description": "Неспешный формат с наблюдением природы и финальной рефлексией.",
                        "price": 3000,
                        "color": "#4FB3BF",
                        "image": "/images/service-moose-2.jpg",
                    }
                ],
            },
        ],
    },
]


def service_child_fields():
    return [
        field("id", "ID"),
        field("slug", "Slug"),
        field("title", "Название"),
        field("full_title", "Полное название"),
        field("description", "Описание", "textarea"),
        field("duration_label", "Длительность"),
        field("intro", "Вводный текст", "textarea"),
        field("note", "Примечание", "textarea"),
        field("image", "Обложка", "image"),
        field("order", "Порядок", "number", 0),
        field("is_category", "Категория", "boolean", False),
        repeater(
            "images",
            "Галерея",
            [
                field("id", "ID"),
                field("image_url", "Изображение", "image"),
                field("order", "Порядок", "number", 0),
            ],
        ),
        repeater("content_sections", "Контентные блоки", text_block_fields()),
        repeater(
            "tariffs",
            "Тарифы",
            [
                field("id", "ID"),
                field("slug", "Slug"),
                field("title", "Название"),
                field("description", "Описание", "textarea"),
                field("duration", "Длительность"),
                field("price", "Цена", "number", 0),
                field("order", "Порядок", "number", 0),
            ],
        ),
    ]


VOLGA_SECTION_SEEDS = [
    {
        "key": "hero",
        "title": SECTION_TITLES["hero"],
        "order": 1,
        "schema": {
            "fields": [
                field("title", "Имя"),
                field("description", "Описание", "textarea"),
                field("background_image", "Фоновое изображение", "image"),
                field("avatar", "Аватар", "image"),
            ]
        },
        "content": {
            "title": "Лиза Стручкова",
            "description": "Делюсь событиями, тишиной и тёплыми практиками в Конаково.",
            "background_image": "/card.png",
            "avatar": "/avatar.png",
        },
    },
    {
        "key": "site-settings",
        "title": SECTION_TITLES["site-settings"],
        "order": 2,
        "schema": {
            "fields": [
                field("phone", "Телефон"),
                field("email", "Email"),
                field("telegram_url", "Ссылка Telegram"),
                field("telegram_username", "Подпись Telegram"),
                field("address", "Адрес", "textarea"),
            ]
        },
        "content": {
            "phone": "+7 (985) 200-63-22",
            "email": "elizaveta-struchkova@yandex.ru",
            "telegram_url": "https://t.me/novoe_konakovo",
            "telegram_username": "@novoe_konakovo",
            "address": "Тверская область, Конаковский район, природный кластер «Новое Конаково».",
        },
    },
    {
        "key": "navigation",
        "title": SECTION_TITLES["navigation"],
        "order": 3,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Пункты меню",
                    [
                        field("label", "Название"),
                        field("to", "Vue route"),
                        field("href", "Ссылка"),
                    ],
                )
            ]
        },
        "content": {"items_json": NAVIGATION_ITEMS},
    },
    {
        "key": "services",
        "title": SECTION_TITLES["services"],
        "order": 4,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Услуги",
                    [
                        *service_child_fields(),
                        repeater("children", "Подуслуги", service_child_fields()),
                    ],
                )
            ]
        },
        "content": {"items_json": SERVICES},
    },
    {
        "key": "schedule",
        "title": SECTION_TITLES["schedule"],
        "order": 5,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Месяцы расписания",
                    [
                        field("month", "Месяц"),
                        field("year", "Год", "number", 2026),
                        field("month_number", "Номер месяца", "number", 1),
                        repeater(
                            "days",
                            "Дни",
                            [
                                field("date", "Дата YYYY-MM-DD"),
                                field("weekday", "День недели"),
                                repeater(
                                    "events",
                                    "События",
                                    [
                                        field("id", "ID"),
                                        field("time_start", "Начало"),
                                        field("time_end", "Конец"),
                                        field("title", "Название"),
                                        field("category", "Категория"),
                                        field("description", "Описание", "textarea"),
                                        field("price", "Цена", "number", 0),
                                        field("color", "Цвет"),
                                        field("image", "Изображение", "image"),
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ]
        },
        "content": {"items_json": SCHEDULE},
    },
    {
        "key": "reviews",
        "title": SECTION_TITLES["reviews"],
        "order": 6,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Отзывы",
                    [
                        field("id", "ID"),
                        field("name", "Имя"),
                        field("event_name", "Событие"),
                        field("rating", "Оценка", "number", 5),
                        field("text", "Текст", "textarea"),
                        field("date", "Дата"),
                        field("avatar", "Аватар", "image"),
                    ],
                )
            ]
        },
        "content": {"items_json": REVIEWS},
    },
    {
        "key": "articles",
        "title": SECTION_TITLES["articles"],
        "order": 7,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Статьи и видео",
                    [
                        field("title", "Заголовок"),
                        field("slug", "Slug"),
                        field("preview_image", "Изображение", "image"),
                        field("preview_description", "Краткое описание", "textarea"),
                        field("content", "Контент", "textarea"),
                        field(
                            "content_type",
                            "Тип",
                            "select",
                            "article",
                            options=[
                                {"value": "article", "label": "Статья"},
                                {"value": "video", "label": "Видео"},
                            ],
                        ),
                        field("video_url", "Видео URL"),
                        field("published_date", "Дата публикации"),
                        field("created_at", "Дата создания"),
                    ],
                )
            ]
        },
        "content": {"items_json": ARTICLES},
    },
    {
        "key": "news",
        "title": SECTION_TITLES["news"],
        "order": 8,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Новости",
                    [
                        field("id", "ID", "number", 0),
                        field("title", "Заголовок"),
                        field("slug", "Slug"),
                        field("description", "Краткое описание", "textarea"),
                        field("image", "Изображение", "image"),
                        field("published_date", "Дата публикации"),
                        field("content", "Контент", "textarea"),
                    ],
                )
            ]
        },
        "content": {"items_json": NEWS},
    },
    {
        "key": "pages",
        "title": SECTION_TITLES["pages"],
        "order": 9,
        "schema": {
            "fields": [
                repeater(
                    "items_json",
                    "Страницы",
                    [
                        field("slug", "Slug"),
                        field("title", "Заголовок"),
                        field("subtitle", "Подзаголовок", "textarea"),
                        field("hero_image", "Hero-изображение", "image"),
                        field("order", "Порядок", "number", 0),
                        repeater(
                            "sections",
                            "Секции",
                            [
                                field("title", "Заголовок"),
                                field("text", "Текст", "textarea"),
                                field("order", "Порядок", "number", 0),
                            ],
                        ),
                        repeater(
                            "gallery",
                            "Галерея",
                            [
                                field("id", "ID"),
                                field("image", "Изображение", "image"),
                                field("order", "Порядок", "number", 0),
                            ],
                        ),
                    ],
                )
            ]
        },
        "content": {"items_json": PAGES},
    },
    {
        "key": "footer",
        "title": SECTION_TITLES["footer"],
        "order": 10,
        "schema": {
            "fields": [
                field("brand", "Название"),
                field("description", "Описание", "textarea"),
                field("copyright", "Copyright"),
                repeater(
                    "links_json",
                    "Ссылки",
                    [
                        field("label", "Название"),
                        field("href", "Ссылка"),
                    ],
                ),
            ]
        },
        "content": {
            "brand": "Новое Конаково",
            "description": "Природный отдых, экскурсии, события и камерные практики в Конаково.",
            "copyright": "© 2026 Новое Конаково. Все права защищены.",
            "links_json": [
                {"label": "Услуги", "href": "/#services"},
                {"label": "Расписание", "href": "/schedule"},
                {"label": "Контакты", "href": "/contacts"},
                {"label": "Telegram", "href": "https://t.me/novoe_konakovo"},
            ],
        },
    },
]


def get_section_seed(key):
    return next((seed for seed in VOLGA_SECTION_SEEDS if seed["key"] == key), None)


def get_site_specific_schema_key(section_key, site_slug=VOLGA_SITE_SLUG):
    return f"{site_slug}-{section_key}"
