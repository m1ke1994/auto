export interface Project {
  id: string;
  title: string;
  category: 'service' | 'landing' | 'multipage';
  shortDescription: string;
  fullDescription: string;
  techStack: string[];
  role: string;
  images: string[];
  demoUrl?: string;
  repoUrl?: string;
  results?: string;
}

export const projects: Project[] = [
  {
    id: "1",
    title: "Салон красоты",
    category: "landing",
    shortDescription: "Лендинг салона красоты с акцентом на услуги, мастеров и быстрый контакт.",
    fullDescription: "Сделал одностраничный сайт с блоками услуг, цен, отзывов и быстрых CTA. Продумал визуальную иерархию, адаптивы и оптимизацию медиа для быстрой загрузки.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Верстка, адаптив, настройка контентных блоков и оптимизация изображений.",
    images: ["/beauty-salon-website-psi.vercel.JPG"],
    demoUrl: "https://beauty-salon-website-psi.vercel.app/"
  },
  {
    id: "2",
    title: "Конструкторское бюро",
    category: "landing",
    shortDescription: "Презентационный лендинг инженерной компании с фокусом на услуги и кейсы.",
    fullDescription: "Собрал структуру секций: услуги, компетенции, выполненные проекты и контактные блоки. Упор на понятную подачу и аккуратную типографику, плюс адаптив для мобильных.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Frontend-разработка, адаптивная верстка, настройка контента и визуальных акцентов.",
    images: ["/website-ikb.vercel.JPG"],
    demoUrl: "https://website-ikb.vercel.app/"
  },
  {
    id: "3",
    title: "Инновационное конструкторское бюро",
    category: "landing",
    shortDescription: "Лендинг для инженерной команды с акцентом на экспертизу и направление работ.",
    fullDescription: "Сделал одностраничный сайт с акцентом на преимущества, портфолио и процесс работы. Продумал визуальные блоки, чтобы быстро объяснить ценность услуг.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Сборка секций, адаптивная верстка и настройка контента.",
    images: ["/ikb-theta.vercel.JPG"],
    demoUrl: "https://ikb-theta.vercel.app/"
  },
  {
    id: "4",
    title: "Maysama — главная страница (копия)",
    category: "landing",
    shortDescription: "Учебный проект: точное воспроизведение главной страницы с адаптивом.",
    fullDescription: "Практика вёрстки и композиции: повторил сетку, типографику и визуальные блоки. Отработал адаптив и структуру компонентов для дальнейшего масштабирования.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Верстка, адаптив, повторение компонентов и базовая оптимизация.",
    images: ["/maysamafrontend.vercel.JPG"],
    demoUrl: "https://maysamafrontend.vercel.app/"
  },
  {
    id: "5",
    title: "Smart Nara — витрина интернет-магазина",
    category: "multipage",
    shortDescription: "Pet-проект витрины интернет-магазина с каталогом и карточками товаров.",
    fullDescription: "Практический проект: каталог, фильтры, поиск и детальная карточка товара. Отработал состояние фильтров, сортировку и структуру каталога.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Frontend-разработка, логика фильтров и каталог.",
    images: ["/test-eight-weld-74.vercel.JPG"],
    demoUrl: "https://test-eight-weld-74.vercel.app/"
  },
  {
    id: "6",
    title: "Трекер-панель (доработка)",
    category: "service",
    shortDescription: "Доработка клиентской панели: фильтры, таблицы, правки интерфейса.",
    fullDescription: "В существующем проекте обновил UI, переработал экраны с таблицами и добавил новые фильтры. Подключил дополнительные endpoints и привёл состояния к единому поведению.",
    techStack: ["React", "TypeScript", "REST API", "Tailwind CSS"],
    role: "Доработка UI и логики, интеграция с API и исправление багов.",
    images: ["/quasar-test-gamma.vercel.JPG"],
    demoUrl: "https://quasar-test-gamma.vercel.app/#/"
  },
  {
    id: "7",
    title: "Горные лыжи",
    category: "landing",
    shortDescription: "Pet-проект лендинга о горнолыжном курорте с галереей и описанием трасс.",
    fullDescription: "Собрал атмосферный лендинг с блоками о трассах, инструкторе и сезонных предложениях. Проработал визуальные акценты и адаптив для мобильных.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Верстка, адаптив, работа с изображениями и контентом.",
    images: ["/skiing-frontend.vercel.JPG"],
    demoUrl: "https://skiing-frontend.vercel.app/"
  },
  {
    id: "8",
    title: "ARES — корпоративный сайт",
    category: "multipage",
    shortDescription: "Многостраничный корпоративный сайт с услугами, кейсами и контактами.",
    fullDescription: "Собрал структуру страниц, единые блоки и навигацию. Уделил внимание последовательной типографике и удобству чтения на разных экранах.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Frontend-разработка, композиция страниц и адаптив.",
    images: ["/project-site-tau.vercel.JPG"],
    demoUrl: "https://project-site-tau.vercel.app/"
  },
  {
    id: "9",
    title: "Портфолио на английском (доработка)",
    category: "multipage",
    shortDescription: "Доработка англоязычного портфолио: правки интерфейса и контента.",
    fullDescription: "Обновил структуру секций, текст и визуальные элементы. Привёл стили к единому виду и поправил адаптив для мобильных.",
    techStack: ["React", "TypeScript", "Tailwind CSS"],
    role: "Доработка UI, правки контента и адаптив.",
    images: ["/alex-presents-elegance.lovable.app.JPG"],
    demoUrl: "https://alex-presents-elegance.lovable.app/"
  },
  {
    id: "10",
    title: "Лендинг юриста",
    category: "landing",
    shortDescription: "Лендинг юридических услуг с акцентом на практику, кейсы и консультацию.",
    fullDescription: "Собрал одностраничный сайт с блоками об услугах, опыте и отзывах. Продумал ясную структуру и удобную навигацию по секциям.",
    techStack: ["React", "TypeScript", "Tailwind CSS", "Vite"],
    role: "Верстка, адаптив, настройка контента и визуальных блоков.",
    images: ["/юрист.JPG"],
    demoUrl: "https://greenleaf-law-hub.lovable.app/"
  },
  {
    id: "11",
    title: "Telegram-бот записи на массаж",
    category: "service",
    shortDescription: "Бот для записи клиентов с выбором услуги, времени и уведомлениями.",
    fullDescription: "Реализовал сценарии записи, напоминаний и отмены, а также админ-часть для управления расписанием. Сделал аккуратную логику диалогов и обработку статусов.",
    techStack: ["Python", "aiogram", "PostgreSQL", "Telegram Bot API"],
    role: "Проектирование диалогов, разработка бота и интеграция с расписанием.",
    images: ["/tg_bot_2.JPG"]
  },
  {
    id: "12",
    title: "Telegram-бот удалённого доступа к инфраструктуре",
    category: "service",
    shortDescription: "Служебный бот для безопасного доступа к внутренним сервисам и задачам.",
    fullDescription: "Настроил роли и сценарии команд, логирование действий и контроль прав. Интегрировал с внутренним REST API и добавил понятные статусы выполнения.",
    techStack: ["Python", "aiogram", "REST API", "Telegram Bot API"],
    role: "Доработка логики, интеграция с API и настройка ролей.",
    images: ["/tg_bot_1.JPG"]
  },
  {
    id: "13",
    title: "SaaS: сервис лояльности",
    category: "service",
    shortDescription: "Система лояльности с кабинетами, ролями и начислением/списанием баллов.",
    fullDescription: "Сервис для работы с баллами и уровнями лояльности: кабинет клиента и админа, роли и права доступа. Поддержка QR/карты лояльности и история операций.",
    techStack: ["React", "Node.js", "PostgreSQL", "REST API"],
    role: "Frontend-логика и интеграция с API, проработка кабинета и ролей.",
    images: ["/card_loyality.JPG"]
  },
  {
  id: "14",
  title: "TrackNode — SaaS аналитика сайтов",
  category: "multipage",
  shortDescription: "SaaS-платформа веб-аналитики с отслеживанием посещений, конверсий и SEO-аудитом.",
  fullDescription: "Полноценная система аналитики: отслеживание визитов, уникальных пользователей, конверсий, источников трафика и поведения пользователей. Реализованы личные кабинеты клиентов, генерация PDF-отчетов, SEO-аудит и Telegram-уведомления. Архитектура построена как multi-tenant SaaS.",
  techStack: ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Redis", "Celery", "Docker", "Nginx"],
  role: "Проектирование архитектуры, backend (API, аналитика, multi-tenant), frontend-панель, деплой и DevOps.",
  images: ["/tracknode.JPG"],
  demoUrl: "https://tracknode.ru/",
  results: "Реализована система отслеживания пользователей и событий, подключаемая к сторонним сайтам. Поддержка нескольких клиентов и изоляция данных."
},
{
  id: "15",
  title: "Новое Конаково",
  category: "multipage",
  shortDescription: "Многостраничный сайт загородного пространства с расписанием, услугами и блогом.",
  fullDescription: "Корпоративный сайт с динамическими страницами услуг, расписанием мероприятий, статьями и медиа-контентом. Реализована админ-панель на Django для управления контентом, тарифами и галереями. Проработана мобильная версия и UX.",
  techStack: ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Docker"],
  role: "Backend-разработка (модели, админка, API), frontend-интерфейс, архитектура проекта.",
  images: ["/novoe-konakovo.JPG"],
  demoUrl: "https://novoe-konakovo.ru/"
},
{
  id: "16",
  title: "E-Clock — интернет-магазин часов",
  category: "multipage",
  shortDescription: "Интернет-магазин часов с каталогом, карточками товаров и заявками.",
  fullDescription: "E-commerce проект с каталогом товаров, карточками, фильтрацией и оформлением заказа. Реализована админ-панель для управления товарами и заявками. Интеграция с аналитикой и системой отслеживания поведения пользователей.",
  techStack: ["Vue 3", "Django", "Django REST Framework", "PostgreSQL", "Docker", "Nginx"],
  role: "Полный цикл разработки: backend, frontend, интеграция аналитики и деплой.",
  images: ["/e-clock.JPG"],
  demoUrl: "http://e-clock.ru/"
}
];

export const categories = [
  { id: 'all', label: 'Все проекты' },
  { id: 'service', label: 'Сервисы' },
  { id: 'landing', label: 'Лендинги' },
  { id: 'multipage', label: 'Многостраничные' },
] as const;

export type CategoryId = typeof categories[number]['id'];
