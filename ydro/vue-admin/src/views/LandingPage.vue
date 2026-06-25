<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ArrowRight,
  BarChart3,
  Blocks,
  CheckCircle2,
  CircleAlert,
  FileSearch,
  FileText,
  Flame,
  Funnel,
  Gauge,
  Globe2,
  Inbox,
  ListVideo,
  Menu,
  MousePointerClick,
  Route,
  ScrollText,
  SearchCheck,
  Sparkles,
  X,
  Zap,
} from '@lucide/vue'

const mobileMenuOpen = ref(false)

const navItems = [
  { label: 'Возможности', href: '#features' },
  { label: 'Аналитика', href: '#analytics' },
  { label: 'SEO', href: '#seo' },
  { label: 'Тарифы', href: '#pricing' },
  { label: 'Блог', href: '#blog' },
  { label: 'FAQ', href: '#faq' },
]

const benefits = ['Лёгкое подключение', 'Безопасность данных', 'Данные в реальном времени']

const mockMenuItems = [
  ['Главная', BarChart3],
  ['Сайты', Globe2],
  ['Аналитика', BarChart3],
  ['Поведение', MousePointerClick],
  ['Заявки', Inbox],
  ['SEO-аудит', SearchCheck],
  ['Конкуренты', FileSearch],
  ['Отчёты', FileText],
  ['Настройки', Blocks],
]

const metricCards = [
  ['Посетители', '24 780', '+12.9%'],
  ['Просмотры', '71 842', '+8.1%'],
  ['Заявки', '342', '+15.7%'],
  ['Конверсия', '2.47%', '+0.3%'],
]

const trafficSources = [
  ['Прямые', '40%', 'w-[78%]', 'bg-sky-500'],
  ['Поиск', '30%', 'w-[62%]', 'bg-cyan-500'],
  ['Социальные сети', '20%', 'w-[44%]', 'bg-indigo-500'],
  ['Рефералы', '10%', 'w-[26%]', 'bg-violet-500'],
]

const topPages = [
  ['/', '12 480'],
  ['/services', '8 320'],
  ['/about', '6 240'],
  ['/blog', '4 160'],
  ['/contacts', '2 080'],
]

const problemCards = [
  ['Посетители есть, но заявок мало', CircleAlert],
  ['Неясно, куда кликают пользователи', MousePointerClick],
  ['Не понятно, почему люди уходят', Route],
  ['Сложно понять, какие страницы работают', FileText],
  ['SEO и конкуренты анализируются отдельно', SearchCheck],
  ['Заявки теряются между разными каналами', Inbox],
]

const featureCards = [
  ['Поведенческая аналитика', 'Понимайте, как люди реально взаимодействуют с сайтом.', BarChart3],
  ['Тепловые карты кликов', 'Видно, какие элементы получают внимание, а какие игнорируются.', Flame],
  ['Записи сессий', 'Смотрите путь пользователя как понятную timeline-ленту.', ListVideo],
  ['Карта скроллинга', 'Показывает, доходят ли посетители до важных блоков и формы.', ScrollText],
  ['Пути пользователей', 'Помогает увидеть маршруты до заявки и страницы выхода.', Route],
  ['Воронки заявок', 'Находит шаги, где теряются потенциальные клиенты.', Funnel],
  ['События и действия', 'Собирает клики, формы, ошибки и ключевые действия.', MousePointerClick],
  ['Аналитика страниц', 'Сравнивает страницы по просмотрам, времени, заявкам и конверсии.', FileText],
  ['Ошибки и производительность', 'Подсказывает технические проблемы, которые мешают заявкам.', Gauge],
  ['SEO-аудит', 'Проверяет title, description, H1 и технические ошибки сайта.', SearchCheck],
  ['Анализ конкурентов', 'Показывает, чем сильнее сайты в вашей нише.', FileSearch],
  ['PDF-отчёты', 'Формирует аккуратные отчёты для клиента или команды.', FileText],
  ['AI-рекомендации', 'Переводит цифры в понятные действия для роста заявок.', Sparkles],
  ['Мультисайтовость', 'Управляйте несколькими сайтами из одного кабинета.', Blocks],
].map(([title, text, icon]) => ({ title, text, icon }))

const insightCards = [
  'Трафик есть, но пользователи редко отправляют форму.',
  'Большинство посетителей заходят с телефона — проверьте мобильную версию.',
  'Кнопка заявки получает мало кликов — сделайте её заметнее.',
  'Пользователи уходят до блока преимуществ — перенесите его выше.',
  'Страница получает просмотры, но не приносит заявки.',
]

const pricingPlans = [
  {
    name: 'Start',
    price: '2 990 ₽',
    description: 'Для одного сайта и базовой аналитики.',
    features: ['1 сайт', 'базовая аналитика', 'заявки', 'источники', 'устройства', 'SEO-аудит', 'базовые рекомендации'],
  },
  {
    name: 'Pro',
    price: '6 990 ₽',
    description: 'Для роста заявок и глубокого анализа поведения.',
    popular: true,
    features: [
      'до 5 сайтов',
      'тепловые карты',
      'записи сессий',
      'карта скроллинга',
      'пути пользователей',
      'воронки',
      'анализ конкурентов',
      'PDF-отчёты',
      'AI-рекомендации',
      'Telegram-уведомления',
    ],
  },
  {
    name: 'Business',
    price: '14 990 ₽',
    description: 'Для компаний, агентств и нескольких проектов.',
    features: [
      'расширенная мультисайтовость',
      'вся аналитика',
      'командная работа',
      'расширенные отчёты',
      'приоритетная поддержка',
      'будущий API/экспорт данных',
    ],
  },
]

const trustLogos = [
  ['A MEDITATION', 'онлайн-медитации'],
  ['НОВОЕ КОНАКОВО', 'загородный комплекс'],
  ['AI4BUSINESS', 'нейросети для бизнеса'],
  ['LEELABIRD', 'студия дизайна'],
  ['VOLGA VILLAGE', 'коттеджный посёлок'],
  ['TRACKNODE', 'платформа аналитики'],
]

const blogCards = [
  ['Как понять, почему сайт не даёт заявки', 'Практический разбор аналитики, тепловых карт и формы заявки.'],
  ['Какие страницы стоит улучшать первыми', 'Приоритизация по трафику, скроллингу, кликам и конверсии.'],
  ['SEO-аудит без сложных терминов', 'На что смотреть владельцу бизнеса и какие ошибки исправлять сначала.'],
]

const faqItems = [
  ['Что такое TrackNode?', 'TrackNode — это сервис аналитики сайта, заявок, SEO-аудита, анализа конкурентов и понятных рекомендаций в одном кабинете.'],
  ['Как подключить сайт?', 'Добавьте сайт в кабинете, скопируйте код трекера и установите его на страницы публичного сайта.'],
  ['Нужно ли устанавливать код трекера?', 'Да, для тепловых карт, записей сессий, событий и поведенческой аналитики нужен короткий код трекера.'],
  ['Можно ли подключить несколько сайтов?', 'Да, TrackNode работает как мультисайтовая платформа для владельцев сайтов, маркетологов и агентств.'],
  ['Где смотреть заявки?', 'Заявки отображаются в личном кабинете вместе с источником, датой, статусом и связанной аналитикой.'],
  ['Чем TrackNode отличается от обычной аналитики?', 'Он не просто показывает цифры, а объясняет, что они значат и какие действия помогут увеличить заявки.'],
  ['Безопасно ли собирать поведение пользователей?', 'Да. Трекер не сохраняет пароли, значения полей форм и персональные сообщения пользователей.'],
  ['Есть ли SEO-аудит и анализ конкурентов?', 'Да. В кабинете есть SEO-аудит, сравнение с конкурентами и PDF-отчёты с рекомендациями.'],
]

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="min-h-screen overflow-x-hidden bg-[#f8faff] text-slate-950">
    <header class="sticky top-0 z-50 border-b border-slate-200/70 bg-white/82 backdrop-blur-xl">
      <div class="mx-auto flex min-h-[72px] w-full max-w-[1320px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <a href="#top" class="flex items-center gap-3" aria-label="TrackNode">
          <span class="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-[#5B5CFF] to-[#8B5CF6] text-white shadow-[0_12px_32px_rgba(91,92,255,0.28)]">
            <Zap :size="22" fill="currentColor" />
          </span>
          <span class="text-xl font-semibold text-slate-950">TrackNode</span>
        </a>

        <nav class="hidden items-center gap-9 lg:flex" aria-label="Основная навигация">
          <a v-for="item in navItems" :key="item.href" :href="item.href" class="text-sm font-semibold text-slate-700 transition hover:text-[#5B5CFF]">
            {{ item.label }}
          </a>
        </nav>

        <div class="hidden items-center gap-5 lg:flex">
          <RouterLink to="/login" class="text-sm font-semibold text-slate-800 transition hover:text-[#5B5CFF]">
            Войти
          </RouterLink>
          <RouterLink to="/login" class="inline-flex min-h-11 items-center justify-center rounded-lg bg-gradient-to-r from-[#5B5CFF] to-[#8B5CF6] px-5 text-sm font-semibold text-white shadow-[0_16px_36px_rgba(91,92,255,0.28)] transition hover:shadow-[0_18px_44px_rgba(91,92,255,0.38)]">
            Войти в кабинет
          </RouterLink>
        </div>

        <button
          type="button"
          class="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-900 shadow-sm lg:hidden"
          :aria-expanded="mobileMenuOpen"
          aria-label="Открыть меню"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <X v-if="mobileMenuOpen" :size="20" />
          <Menu v-else :size="20" />
        </button>
      </div>

      <div v-if="mobileMenuOpen" class="border-t border-slate-200 bg-white px-4 py-4 lg:hidden">
        <nav class="mx-auto grid max-w-[1320px] gap-2" aria-label="Мобильная навигация">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="rounded-lg px-3 py-3 text-sm font-semibold text-slate-700 hover:bg-indigo-50"
            @click="closeMobileMenu"
          >
            {{ item.label }}
          </a>
          <RouterLink to="/login" class="mt-2 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#5B5CFF] px-4 text-sm font-semibold text-white" @click="closeMobileMenu">
            Войти в кабинет
          </RouterLink>
        </nav>
      </div>
    </header>

    <main id="top">
      <section class="relative overflow-hidden bg-[radial-gradient(circle_at_70%_22%,rgba(139,92,246,0.18),transparent_35%),radial-gradient(circle_at_18%_38%,rgba(59,130,246,0.14),transparent_32%),linear-gradient(180deg,#ffffff_0%,#f8faff_72%,#f4f1ff_100%)]">
        <div class="mx-auto grid min-h-[700px] w-full max-w-[1320px] items-center gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[0.92fr_1.08fr] lg:px-8 lg:py-16">
          <div class="relative z-10 max-w-[22rem] sm:max-w-none">
            <p class="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/72 px-4 py-2 text-sm font-semibold text-slate-500 shadow-sm backdrop-blur">
              <Sparkles :size="16" class="text-[#5B5CFF]" />
              Аналитика нового поколения
            </p>
            <h1 class="mt-7 max-w-[720px] text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl lg:text-6xl">
              Понимайте, что происходит
              <span class="block bg-gradient-to-r from-[#2563EB] via-[#5B5CFF] to-[#8B5CF6] bg-clip-text text-transparent">с вашим сайтом</span>
            </h1>
            <p class="mt-7 max-w-2xl text-lg leading-8 text-slate-600">
              TrackNode объединяет аналитику, тепловые карты, записи сессий, заявки, SEO-аудит и AI-рекомендации в одном личном кабинете. Не просто цифры — понятные выводы и действия для роста заявок.
            </p>
            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <RouterLink to="/login" class="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#5B5CFF] to-[#8B5CF6] px-6 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(91,92,255,0.28)] transition hover:shadow-[0_20px_48px_rgba(91,92,255,0.38)]">
                Войти в кабинет
                <ArrowRight :size="17" />
              </RouterLink>
              <a href="#features" class="inline-flex min-h-12 items-center justify-center rounded-lg border border-[#5B5CFF]/35 bg-white/70 px-6 text-sm font-semibold text-[#5B5CFF] shadow-sm transition hover:bg-indigo-50">
                Посмотреть возможности
              </a>
            </div>
            <div class="mt-8 grid gap-4 text-sm font-medium text-slate-600 sm:grid-cols-3">
              <div v-for="item in benefits" :key="item" class="flex items-center gap-2">
                <span class="grid h-7 w-7 place-items-center rounded-full bg-indigo-50 text-[#5B5CFF]">
                  <CheckCircle2 :size="15" />
                </span>
                {{ item }}
              </div>
            </div>
          </div>

          <div class="relative">
            <div class="absolute -inset-8 rounded-[32px] bg-[radial-gradient(circle,rgba(139,92,246,0.22),transparent_62%)] blur-2xl" />
            <div class="relative overflow-hidden rounded-[28px] border border-slate-200/70 bg-white/76 shadow-[0_30px_100px_rgba(91,92,255,0.18)] backdrop-blur-xl">
              <div class="grid min-h-[500px] grid-cols-1 sm:grid-cols-[170px_1fr]">
                <aside class="hidden border-r border-slate-200/80 bg-white/60 p-4 sm:block">
                  <div class="flex items-center gap-2 text-sm font-semibold text-slate-950">
                    <span class="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#5B5CFF] to-[#8B5CF6] text-white">
                      <Zap :size="16" fill="currentColor" />
                    </span>
                    TrackNode
                  </div>
                  <nav class="mt-6 space-y-1">
                    <div
                      v-for="([item, icon], index) in mockMenuItems"
                      :key="item"
                      class="flex min-h-9 items-center gap-2 rounded-lg px-2 text-[11px] font-semibold"
                      :class="index === 0 ? 'bg-indigo-50 text-[#5B5CFF]' : 'text-slate-600'"
                    >
                      <component :is="icon" :size="14" />
                      <span class="truncate">{{ item }}</span>
                    </div>
                  </nav>
                </aside>

                <div class="min-w-0 bg-slate-50/40 p-4 sm:p-5">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <h2 class="text-sm font-semibold text-slate-950">Главная</h2>
                    <div class="flex flex-wrap gap-2 text-[11px] text-slate-500">
                      <span class="rounded-lg border border-slate-200 bg-white px-3 py-2">25 янв — 24 июн 2026</span>
                      <span class="rounded-lg border border-slate-200 bg-white px-3 py-2">Все сайты</span>
                    </div>
                  </div>

                  <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <article v-for="[label, value, change] in metricCards" :key="label" class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <p class="text-[11px] font-semibold text-slate-400">{{ label }}</p>
                      <div class="mt-3 flex items-end justify-between gap-2">
                        <strong class="text-xl font-semibold text-slate-950">{{ value }}</strong>
                        <span class="text-[10px] font-semibold text-emerald-500">{{ change }}</span>
                      </div>
                    </article>
                  </div>

                  <div class="mt-3 grid gap-3 xl:grid-cols-[1.1fr_0.72fr]">
                    <article class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <h3 class="text-xs font-semibold text-slate-950">Посетители</h3>
                      <div class="mt-4 h-40 rounded-lg bg-[linear-gradient(180deg,#ffffff,#f8faff)]">
                        <svg viewBox="0 0 520 150" class="h-full w-full" role="img" aria-label="График посещений">
                          <path d="M0 120H520" stroke="#E2E8F0" stroke-width="1" />
                          <path d="M0 80H520" stroke="#E2E8F0" stroke-width="1" />
                          <path d="M0 40H520" stroke="#E2E8F0" stroke-width="1" />
                          <path d="M8 78 C32 92, 46 24, 72 38 C96 52, 108 92, 135 68 C162 44, 178 102, 205 76 C232 50, 244 35, 268 70 C292 104, 310 68, 335 82 C360 96, 375 40, 402 50 C428 60, 444 95, 468 70 C492 45, 506 72, 516 64" fill="none" stroke="#5B5CFF" stroke-width="4" stroke-linecap="round" />
                        </svg>
                      </div>
                    </article>

                    <article class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <h3 class="text-xs font-semibold text-slate-950">Тепловая карта кликов</h3>
                      <div class="relative mt-4 h-40 overflow-hidden rounded-lg border border-indigo-100 bg-[linear-gradient(135deg,#eef4ff,#ffffff)]">
                        <div class="absolute inset-4 rounded-lg bg-white/60" />
                        <span class="absolute left-[18%] top-[22%] h-12 w-12 rounded-full bg-cyan-300/65 blur-md" />
                        <span class="absolute left-[50%] top-[30%] h-16 w-16 rounded-full bg-emerald-300/70 blur-md" />
                        <span class="absolute left-[66%] top-[48%] h-20 w-20 rounded-full bg-rose-400/70 blur-md" />
                        <span class="absolute left-[33%] top-[58%] h-16 w-16 rounded-full bg-amber-300/70 blur-md" />
                        <span class="absolute left-[76%] top-[15%] h-12 w-12 rounded-full bg-orange-300/70 blur-md" />
                      </div>
                    </article>
                  </div>

                  <div class="mt-3 grid gap-3 xl:grid-cols-3">
                    <article class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <h3 class="text-xs font-semibold text-slate-950">Источники трафика</h3>
                      <div class="mt-4 space-y-3">
                        <div v-for="[source, value, widthClass, colorClass] in trafficSources" :key="source" class="grid grid-cols-[70px_1fr_34px] items-center gap-2 text-[11px]">
                          <span class="text-slate-500">{{ source }}</span>
                          <span class="h-1.5 overflow-hidden rounded-full bg-slate-100">
                            <span class="block h-full rounded-full" :class="[widthClass, colorClass]" />
                          </span>
                          <strong class="text-right text-slate-700">{{ value }}</strong>
                        </div>
                      </div>
                    </article>

                    <article class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <h3 class="text-xs font-semibold text-slate-950">Топ страниц</h3>
                      <div class="mt-4 space-y-2">
                        <div v-for="[page, count] in topPages" :key="page" class="flex items-center justify-between text-[11px]">
                          <span class="font-medium text-slate-600">{{ page }}</span>
                          <span class="text-slate-500">{{ count }}</span>
                        </div>
                      </div>
                    </article>

                    <article class="rounded-lg border border-slate-200/70 bg-white p-4 shadow-sm">
                      <h3 class="text-xs font-semibold text-slate-950">AI-рекомендации</h3>
                      <div class="mt-4 space-y-3 text-[11px] leading-5 text-slate-600">
                        <p class="flex gap-2"><Sparkles :size="13" class="mt-1 shrink-0 text-[#5B5CFF]" />Увеличьте контраст кнопки на главном экране</p>
                        <p class="flex gap-2"><Sparkles :size="13" class="mt-1 shrink-0 text-[#5B5CFF]" />Добавьте отзывы клиентов на страницу услуг</p>
                        <p class="flex gap-2"><Sparkles :size="13" class="mt-1 shrink-0 text-[#5B5CFF]" />Оптимизируйте изображения для мобильных</p>
                      </div>
                    </article>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-white py-12">
        <div class="mx-auto w-full max-w-[1320px] px-4 text-center sm:px-6 lg:px-8">
          <p class="text-sm font-semibold text-slate-600">Нам доверяют компании и предприниматели</p>
          <div class="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-6">
            <div v-for="[name, caption] in trustLogos" :key="name" class="flex items-center justify-center gap-3 text-left text-slate-500">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 text-slate-500">
                <Zap v-if="name === 'TRACKNODE'" :size="20" fill="currentColor" />
                <Globe2 v-else :size="19" />
              </span>
              <span>
                <strong class="block text-sm font-semibold uppercase tracking-wide text-slate-500">{{ name }}</strong>
                <small class="text-xs text-slate-400">{{ caption }}</small>
              </span>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-white py-16 sm:py-20">
        <div class="mx-auto w-full max-w-[1320px] px-4 sm:px-6 lg:px-8">
          <div class="mx-auto max-w-3xl text-center">
            <p class="inline-flex rounded-full bg-indigo-50 px-4 py-2 text-xs font-semibold text-[#5B5CFF]">Проблемы знакомы?</p>
            <h2 class="mt-6 text-3xl font-semibold leading-tight text-slate-950 sm:text-4xl">
              Обычная аналитика показывает цифры. TrackNode объясняет, <span class="text-[#5B5CFF]">что они значат.</span>
            </h2>
          </div>
          <div class="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <article v-for="[title, icon] in problemCards" :key="title" class="rounded-lg border border-slate-200/80 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
              <span class="grid h-12 w-12 place-items-center rounded-lg bg-indigo-50 text-[#5B5CFF]">
                <component :is="icon" :size="20" />
              </span>
              <h3 class="mt-8 text-base font-semibold leading-6 text-slate-950">{{ title }}</h3>
            </article>
          </div>
        </div>
      </section>

      <section id="features" class="bg-[#f8faff] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-[1320px] px-4 sm:px-6 lg:px-8">
          <div class="mx-auto max-w-3xl text-center">
            <p class="text-sm font-semibold text-[#5B5CFF]">Возможности</p>
            <h2 class="mt-3 text-3xl font-semibold text-slate-950 sm:text-4xl">Всё, что нужно для понимания сайта</h2>
          </div>
          <div class="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <article v-for="item in featureCards" :key="item.title" class="rounded-lg border border-slate-200/80 bg-white/78 p-5 shadow-[0_18px_50px_rgba(91,92,255,0.06)] backdrop-blur">
              <span class="grid h-11 w-11 place-items-center rounded-lg bg-gradient-to-br from-indigo-50 to-violet-50 text-[#5B5CFF]">
                <component :is="item.icon" :size="20" />
              </span>
              <h3 class="mt-5 text-base font-semibold text-slate-950">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section id="analytics" class="bg-white py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-[1320px] gap-10 px-4 sm:px-6 lg:grid-cols-[0.86fr_1.14fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-[#5B5CFF]">Не просто статистика</p>
            <h2 class="mt-3 text-3xl font-semibold leading-tight text-slate-950 sm:text-4xl">Не просто статистика — понятные решения</h2>
            <p class="mt-5 text-lg leading-8 text-slate-600">
              TrackNode превращает данные в понятные выводы: что работает, где пользователи теряются и какие действия помогут увеличить заявки.
            </p>
          </div>
          <div class="grid gap-4">
            <article v-for="item in insightCards" :key="item" class="flex gap-3 rounded-lg border border-slate-200/80 bg-[#f8faff] p-4 text-sm leading-6 text-slate-700">
              <CheckCircle2 :size="18" class="mt-0.5 shrink-0 text-[#5B5CFF]" />
              <span>{{ item }}</span>
            </article>
          </div>
        </div>
      </section>

      <section id="seo" class="bg-[linear-gradient(180deg,#ffffff,#f8faff)] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-[1320px] gap-5 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
          <article class="rounded-lg border border-slate-200/80 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
            <SearchCheck :size="25" class="text-[#5B5CFF]" />
            <h2 class="mt-5 text-2xl font-semibold text-slate-950">SEO-аудит сайта</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">Проверяйте title, description, H1, технические ошибки и получайте понятные рекомендации.</p>
          </article>
          <article class="rounded-lg border border-slate-200/80 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
            <FileSearch :size="25" class="text-[#5B5CFF]" />
            <h2 class="mt-5 text-2xl font-semibold text-slate-950">Анализ конкурентов</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">Сравнивайте сайт с конкурентами и находите точки роста в нише.</p>
          </article>
          <article class="rounded-lg border border-slate-200/80 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
            <Inbox :size="25" class="text-[#5B5CFF]" />
            <h2 class="mt-5 text-2xl font-semibold text-slate-950">Заявки в кабинете</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">Смотрите источник, дату, статус и связь заявки с аналитикой сайта.</p>
          </article>
        </div>
      </section>

      <section id="pricing" class="bg-white py-16 sm:py-20">
        <div class="mx-auto w-full max-w-[1320px] px-4 sm:px-6 lg:px-8">
          <div class="mx-auto max-w-3xl text-center">
            <p class="text-sm font-semibold text-[#5B5CFF]">Тарифы</p>
            <h2 class="mt-3 text-3xl font-semibold text-slate-950 sm:text-4xl">Выберите формат для вашего сайта</h2>
          </div>
          <div class="mt-10 grid gap-5 lg:grid-cols-3">
            <article
              v-for="plan in pricingPlans"
              :key="plan.name"
              class="relative rounded-lg border bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.07)]"
              :class="plan.popular ? 'border-[#5B5CFF]/45 ring-2 ring-[#5B5CFF]/10' : 'border-slate-200/80'"
            >
              <span v-if="plan.popular" class="mb-4 inline-flex rounded-full bg-[#5B5CFF] px-3 py-1 text-xs font-semibold text-white">Популярный</span>
              <h3 class="text-2xl font-semibold text-slate-950">{{ plan.name }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ plan.description }}</p>
              <p class="mt-6 text-4xl font-semibold text-slate-950">{{ plan.price }}<span class="text-base font-medium text-slate-500">/мес</span></p>
              <ul class="mt-7 space-y-3">
                <li v-for="feature in plan.features" :key="feature" class="flex gap-3 text-sm leading-6 text-slate-700">
                  <CheckCircle2 :size="17" class="mt-0.5 shrink-0 text-[#5B5CFF]" />
                  <span>{{ feature }}</span>
                </li>
              </ul>
              <RouterLink to="/login" class="mt-7 inline-flex min-h-11 w-full items-center justify-center rounded-lg bg-gradient-to-r from-[#5B5CFF] to-[#8B5CF6] px-4 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(91,92,255,0.2)] transition hover:shadow-[0_16px_36px_rgba(91,92,255,0.28)]">
                Войти в кабинет
              </RouterLink>
            </article>
          </div>
        </div>
      </section>

      <section id="blog" class="bg-[#f8faff] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-[1320px] px-4 sm:px-6 lg:px-8">
          <div class="mx-auto max-w-3xl text-center">
            <p class="text-sm font-semibold text-[#5B5CFF]">Блог</p>
            <h2 class="mt-3 text-3xl font-semibold text-slate-950 sm:text-4xl">Материалы для роста сайта</h2>
          </div>
          <div class="mt-10 grid gap-5 md:grid-cols-3">
            <article v-for="[title, text] in blogCards" :key="title" class="rounded-lg border border-slate-200/80 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
              <h3 class="text-lg font-semibold text-slate-950">{{ title }}</h3>
              <p class="mt-3 text-sm leading-6 text-slate-600">{{ text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section id="faq" class="bg-white py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-[1320px] gap-10 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-[#5B5CFF]">FAQ</p>
            <h2 class="mt-3 text-3xl font-semibold text-slate-950 sm:text-4xl">Ответы на частые вопросы</h2>
          </div>
          <div class="grid gap-3">
            <details v-for="[question, answer] in faqItems" :key="question" class="group rounded-lg border border-slate-200/80 bg-[#f8faff] p-5">
              <summary class="flex cursor-pointer list-none items-center justify-between gap-4 text-base font-semibold text-slate-950">
                {{ question }}
                <ArrowRight :size="18" class="shrink-0 text-[#5B5CFF] transition group-open:rotate-90" />
              </summary>
              <p class="mt-3 text-sm leading-6 text-slate-600">{{ answer }}</p>
            </details>
          </div>
        </div>
      </section>

      <section class="bg-white px-4 pb-16 sm:px-6 sm:pb-20 lg:px-8">
        <div class="mx-auto max-w-[1320px] rounded-[28px] border border-indigo-100 bg-[radial-gradient(circle_at_20%_20%,rgba(91,92,255,0.18),transparent_30%),linear-gradient(135deg,#ffffff,#eef2ff)] px-6 py-12 text-center shadow-[0_30px_90px_rgba(91,92,255,0.12)] sm:px-10 sm:py-16">
          <h2 class="text-3xl font-semibold text-slate-950 sm:text-5xl">Начните понимать свой сайт уже сегодня</h2>
          <p class="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Откройте личный кабинет TrackNode и смотрите аналитику, заявки, SEO и рекомендации в одном месте.
          </p>
          <RouterLink to="/login" class="mt-8 inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#5B5CFF] to-[#8B5CF6] px-6 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(91,92,255,0.28)]">
            Войти в кабинет
            <ArrowRight :size="17" />
          </RouterLink>
        </div>
      </section>
    </main>
  </div>
</template>
