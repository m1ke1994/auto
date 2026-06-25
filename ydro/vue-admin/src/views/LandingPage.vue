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
  MonitorSmartphone,
  MousePointerClick,
  Route,
  ScrollText,
  SearchCheck,
  Sparkles,
  X,
} from '@lucide/vue'

import heroImage from '../assets/hero.png'

const mobileMenuOpen = ref(false)

const navItems = [
  { label: 'Возможности', href: '#features' },
  { label: 'Аналитика', href: '#analytics' },
  { label: 'SEO', href: '#seo' },
  { label: 'Тарифы', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
]

const problemCards = [
  'Посетители есть, но заявок мало.',
  'Неясно, куда кликают пользователи.',
  'Непонятно, почему люди уходят.',
  'Сложно понять, какие страницы работают.',
  'SEO и конкуренты анализируются отдельно.',
  'Заявки теряются между разными каналами.',
]

const productCards = [
  {
    title: 'Аналитика поведения',
    text: 'Видно, какие страницы смотрят, куда кликают и где теряют интерес.',
    icon: BarChart3,
  },
  {
    title: 'Управление заявками',
    text: 'Все обращения с сайта собираются в одном кабинете вместе с источниками.',
    icon: Inbox,
  },
  {
    title: 'SEO и конкуренты',
    text: 'Проверки сайта, ошибки, сравнение с конкурентами и понятные отчёты.',
    icon: SearchCheck,
  },
  {
    title: 'AI-рекомендации',
    text: 'Система переводит данные в конкретные действия для роста заявок.',
    icon: Sparkles,
  },
]

const featureCards = [
  ['Поведенческая аналитика', 'Показывает, что пользователи делают на сайте.', BarChart3],
  ['Тепловые карты кликов', 'Помогают увидеть самые заметные и проблемные зоны.', Flame],
  ['Записи сессий', 'Показывают путь пользователя как timeline действий.', ListVideo],
  ['Карта скроллинга', 'Показывает, до каких блоков реально доходят посетители.', ScrollText],
  ['Пути пользователей', 'Объясняют, какие маршруты ведут к заявке или выходу.', Route],
  ['Воронки заявок', 'Показывают, на каком шаге теряются потенциальные клиенты.', Funnel],
  ['События и действия', 'Собирают клики, формы, ошибки и важные действия.', MousePointerClick],
  ['Аналитика страниц', 'Сравнивает страницы по просмотрам, заявкам и конверсии.', FileText],
  ['Ошибки и производительность', 'Находит технические проблемы, которые мешают заявкам.', Gauge],
  ['SEO-аудит', 'Проверяет title, description, H1 и технические ошибки.', SearchCheck],
  ['Анализ конкурентов', 'Помогает понять, чем сильнее сайты в вашей нише.', FileSearch],
  ['PDF-отчёты', 'Формирует понятные отчёты для клиента или команды.', FileText],
  ['AI-рекомендации', 'Подсказывает, что улучшить в первую очередь.', Sparkles],
  ['Мультисайтовость', 'Удобно управлять несколькими сайтами из одного кабинета.', Blocks],
].map(([title, text, icon]) => ({ title, text, icon }))

const insightExamples = [
  'Трафик есть, но пользователи редко отправляют форму.',
  'Большинство посетителей заходят с телефона — проверьте мобильную версию.',
  'Кнопка заявки получает мало кликов — её стоит сделать заметнее.',
  'Пользователи уходят до блока с преимуществами — перенесите его выше.',
  'Страница получает просмотры, но не приносит заявки.',
]

const behaviorItems = [
  ['Тепловые карты', 'Показывают, куда посетители нажимают чаще всего.'],
  ['Записи сессий', 'Помогают увидеть путь пользователя без сложных отчётов.'],
  ['Скроллинг', 'Показывает, видят ли люди важные блоки и формы.'],
  ['Пути', 'Объясняют, какие страницы ведут к заявке или выходу.'],
  ['Воронки', 'Находят шаг, где теряются потенциальные клиенты.'],
]

const steps = [
  ['Добавьте сайт', 'Подключите один или несколько проектов в личном кабинете.'],
  ['Установите код трекера', 'Скопируйте короткий скрипт на публичный сайт.'],
  ['Получайте аналитику и заявки', 'TrackNode начнёт собирать визиты, события и обращения.'],
  ['Улучшайте сайт', 'Используйте рекомендации, чтобы повышать конверсию.'],
]

const audienceCards = [
  'Владельцы сайтов',
  'Малый бизнес',
  'Маркетологи',
  'Веб-студии',
  'Компании с несколькими сайтами',
]

const securityItems = [
  'не сохраняются пароли',
  'не сохраняются значения полей форм',
  'не собираются персональные сообщения',
  'пользователь видит только свои сайты',
  'работает мультисайтовая изоляция',
  'доступ идёт через личный кабинет',
]

const pricingPlans = [
  {
    name: 'Start',
    price: '2 990 ₽',
    description: 'Для одного сайта и базовой аналитики.',
    features: [
      '1 сайт',
      'посещения и уникальные посетители',
      'источники и устройства',
      'заявки с сайта',
      'SEO-аудит',
      'базовые рекомендации',
    ],
  },
  {
    name: 'Pro',
    price: '6 990 ₽',
    description: 'Для роста конверсии и глубокого анализа.',
    popular: true,
    features: [
      'до 5 сайтов',
      'тепловые карты',
      'записи сессий',
      'карта скроллинга',
      'пути пользователей и воронки',
      'анализ конкурентов',
      'PDF-отчёты',
      'AI-рекомендации',
      'Telegram-уведомления',
    ],
  },
  {
    name: 'Business',
    price: '14 990 ₽',
    description: 'Для компаний, агентств и нескольких команд.',
    features: [
      'расширенная мультисайтовость',
      'вся аналитика',
      'командная работа',
      'расширенные отчёты',
      'приоритетная поддержка',
      'будущие API и экспорт данных',
    ],
  },
]

const faqItems = [
  ['Что такое TrackNode?', 'TrackNode — это сервис аналитики сайта, заявок, SEO-аудита, анализа конкурентов и понятных рекомендаций в одном кабинете.'],
  ['Нужно ли устанавливать код на сайт?', 'Да. Для поведенческой аналитики, тепловой карты кликов, записей сессий и событий нужно установить короткий код трекера.'],
  ['Можно ли подключить несколько сайтов?', 'Да. TrackNode работает как мультисайтовая платформа, поэтому можно вести несколько проектов из одного личного кабинета.'],
  ['Где смотреть заявки?', 'Заявки с сайта отображаются в кабинете вместе с датой, статусом, источником и связанной аналитикой.'],
  ['Чем TrackNode отличается от обычной аналитики?', 'Он показывает не только цифры, но и объясняет, что происходит, почему это важно и что делать дальше.'],
  ['Безопасно ли собирать поведение пользователей?', 'Да. Трекер не сохраняет пароли, значения полей форм и персональные сообщения пользователей.'],
  ['Можно ли смотреть SEO-аудит?', 'Да. В кабинете есть SEO-аудит сайта с проверкой мета-тегов, заголовков, технических ошибок и рекомендаций.'],
  ['Есть ли анализ конкурентов?', 'Да. TrackNode помогает сравнить сайт с конкурентами и сформировать PDF-отчёты.'],
  ['Куда ведёт кнопка входа?', 'Кнопка входа ведёт на существующий маршрут /login, после авторизации работает текущий личный кабинет.'],
]

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="min-h-screen overflow-x-hidden bg-[#05070a] text-white">
    <header class="sticky top-0 z-50 border-b border-white/10 bg-[#05070a]/88 backdrop-blur-xl">
      <div class="mx-auto flex min-h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <a href="#top" class="flex items-center gap-3" aria-label="TrackNode">
          <span class="grid h-9 w-9 place-items-center rounded-lg border border-cyan-300/40 bg-cyan-300/10 text-cyan-200 shadow-[0_0_24px_rgba(34,211,238,0.22)]">
            <BarChart3 :size="19" />
          </span>
          <span class="text-base font-semibold text-white">TrackNode</span>
        </a>

        <nav class="hidden items-center gap-6 md:flex" aria-label="Основная навигация">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="text-sm font-medium text-slate-300 transition hover:text-white"
          >
            {{ item.label }}
          </a>
        </nav>

        <div class="hidden items-center gap-3 md:flex">
          <RouterLink to="/login" class="inline-flex min-h-10 items-center justify-center rounded-lg border border-white/15 bg-white/8 px-4 text-sm font-semibold text-white transition hover:border-cyan-300/50 hover:bg-cyan-300/10">
            Войти
          </RouterLink>
        </div>

        <button
          type="button"
          class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-white/15 bg-white/8 text-white md:hidden"
          :aria-expanded="mobileMenuOpen"
          aria-label="Открыть меню"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <X v-if="mobileMenuOpen" :size="20" />
          <Menu v-else :size="20" />
        </button>
      </div>

      <div v-if="mobileMenuOpen" class="border-t border-white/10 bg-[#070b10] px-4 py-4 md:hidden">
        <nav class="mx-auto grid max-w-7xl gap-2" aria-label="Мобильная навигация">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="rounded-lg px-3 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/8"
            @click="closeMobileMenu"
          >
            {{ item.label }}
          </a>
          <RouterLink to="/login" class="mt-2 inline-flex min-h-11 items-center justify-center rounded-lg bg-cyan-300 px-4 text-sm font-semibold text-slate-950" @click="closeMobileMenu">
            Войти
          </RouterLink>
        </nav>
      </div>
    </header>

    <main id="top">
      <section class="relative overflow-hidden border-b border-white/10">
        <div class="absolute inset-0 bg-[linear-gradient(120deg,rgba(8,145,178,0.22),rgba(5,7,10,0)_42%,rgba(16,185,129,0.16))]" />
        <img
          :src="heroImage"
          alt=""
          class="pointer-events-none absolute right-0 top-20 w-36 opacity-20 mix-blend-screen sm:right-[4%] sm:w-56 lg:top-16 lg:w-64 lg:opacity-55"
          aria-hidden="true"
        >

        <div class="relative mx-auto grid min-h-[76svh] w-full max-w-7xl content-center gap-10 px-4 py-16 sm:px-6 lg:px-8">
          <div class="relative z-10 max-w-[22rem] sm:max-w-3xl">
            <p class="mb-5 inline-block max-w-full rounded-lg border border-cyan-300/30 bg-cyan-300/10 px-3 py-1 text-sm font-semibold leading-5 text-cyan-100">
              Аналитика сайта, заявки и SEO-аудит в одном кабинете
            </p>
            <h1 class="max-w-4xl text-3xl font-semibold leading-tight text-white sm:text-5xl lg:text-6xl">
              Понимайте, что происходит с вашим сайтом
            </h1>
            <p class="mt-6 max-w-2xl text-base leading-7 text-slate-200 sm:text-lg sm:leading-8">
              TrackNode объединяет аналитику, заявки, тепловые карты, SEO-аудит, анализ конкурентов и AI-рекомендации в одном личном кабинете.
            </p>
            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <RouterLink to="/login" class="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-cyan-300 px-5 text-sm font-semibold text-slate-950 shadow-[0_0_32px_rgba(34,211,238,0.22)] transition hover:bg-cyan-200">
                Войти в кабинет
                <ArrowRight :size="17" />
              </RouterLink>
              <a href="#features" class="inline-flex min-h-12 items-center justify-center rounded-lg border border-white/15 bg-white/8 px-5 text-sm font-semibold text-white transition hover:border-cyan-300/50 hover:bg-cyan-300/10">
                Посмотреть возможности
              </a>
            </div>
          </div>

          <div class="pointer-events-none absolute bottom-10 right-8 z-0 hidden w-[48%] lg:block">
            <div class="absolute inset-x-0 bottom-0 mx-auto max-w-[680px] rounded-lg border border-white/14 bg-[#0b1117]/80 p-3 shadow-[0_28px_80px_rgba(0,0,0,0.42)] backdrop-blur-xl">
              <div class="rounded-lg border border-white/10 bg-[#101821]/92 p-4">
                <div class="flex items-center justify-between gap-3 border-b border-white/10 pb-4">
                  <div>
                    <p class="text-sm font-semibold text-white">TrackNode Analytics</p>
                    <p class="mt-1 text-xs text-slate-400">Итоги за последние 14 дней</p>
                  </div>
                  <span class="rounded-lg bg-emerald-300/12 px-3 py-1 text-xs font-semibold text-emerald-200">Конверсия растёт</span>
                </div>

                <div class="mt-4 grid gap-3 sm:grid-cols-3">
                  <div class="rounded-lg border border-white/10 bg-white/7 p-3">
                    <p class="text-xs text-slate-400">Посещения</p>
                    <p class="mt-2 text-2xl font-semibold text-white">1 284</p>
                  </div>
                  <div class="rounded-lg border border-white/10 bg-white/7 p-3">
                    <p class="text-xs text-slate-400">Заявки</p>
                    <p class="mt-2 text-2xl font-semibold text-cyan-200">64</p>
                  </div>
                  <div class="rounded-lg border border-white/10 bg-white/7 p-3">
                    <p class="text-xs text-slate-400">Конверсия</p>
                    <p class="mt-2 text-2xl font-semibold text-emerald-200">5.2%</p>
                  </div>
                </div>

                <div class="mt-4 grid gap-3 lg:grid-cols-[1fr_0.9fr]">
                  <div class="rounded-lg border border-white/10 bg-[#071014] p-4">
                    <div class="mb-3 flex items-center justify-between">
                      <p class="text-sm font-semibold text-white">Тепловая карта</p>
                      <Flame :size="17" class="text-amber-200" />
                    </div>
                    <div class="relative h-36 overflow-hidden rounded-lg bg-[linear-gradient(135deg,rgba(8,145,178,0.24),rgba(15,23,42,0.1),rgba(244,63,94,0.2))]">
                      <span class="absolute left-[18%] top-[28%] h-11 w-11 rounded-full bg-amber-300/55 blur-md" />
                      <span class="absolute left-[54%] top-[42%] h-14 w-14 rounded-full bg-rose-400/50 blur-md" />
                      <span class="absolute left-[72%] top-[64%] h-9 w-9 rounded-full bg-cyan-300/50 blur-md" />
                    </div>
                  </div>
                  <div class="rounded-lg border border-cyan-300/20 bg-cyan-300/10 p-4">
                    <div class="mb-3 flex items-center gap-2 text-cyan-100">
                      <Sparkles :size="17" />
                      <p class="text-sm font-semibold">AI-рекомендация</p>
                    </div>
                    <p class="text-sm leading-6 text-slate-100">
                      Кнопка заявки получает мало кликов. Поднимите её выше и сделайте контрастнее на мобильной версии.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#070b10] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="max-w-[22rem] sm:max-w-3xl">
            <h2 class="text-3xl font-semibold text-white sm:text-4xl">
              Обычная аналитика показывает цифры. TrackNode объясняет, что они значат.
            </h2>
          </div>
          <div class="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <article v-for="item in problemCards" :key="item" class="rounded-lg border border-white/10 bg-white/6 p-5 text-sm leading-6 text-slate-200 backdrop-blur">
              <CircleAlert :size="18" class="mb-4 text-amber-200" />
              {{ item }}
            </article>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-cyan-200">Что такое TrackNode</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Мультисайтовая платформа для роста заявок</h2>
            <p class="mt-5 text-base leading-8 text-slate-300">
              TrackNode — это мультисайтовая платформа для владельцев сайтов, маркетологов и агентств. Она помогает видеть поведение пользователей, собирать заявки, анализировать SEO, сравнивать сайт с конкурентами и получать понятные рекомендации.
            </p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <article v-for="item in productCards" :key="item.title" class="rounded-lg border border-white/10 bg-white/6 p-5 backdrop-blur transition hover:border-cyan-300/35 hover:bg-cyan-300/8">
              <component :is="item.icon" :size="22" class="text-cyan-200" />
              <h3 class="mt-4 text-lg font-semibold text-white">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-300">{{ item.text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section id="features" class="border-b border-white/10 bg-[#071015] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="max-w-[22rem] sm:max-w-3xl">
            <p class="text-sm font-semibold text-emerald-200">Возможности</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Всё, что нужно для понимания сайта</h2>
          </div>
          <div class="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <article v-for="item in featureCards" :key="item.title" class="rounded-lg border border-white/10 bg-[#0d151b]/88 p-5 shadow-[0_18px_48px_rgba(0,0,0,0.16)] transition hover:-translate-y-0.5 hover:border-cyan-300/35">
              <component :is="item.icon" :size="21" class="text-cyan-200" />
              <h3 class="mt-4 text-base font-semibold text-white">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-300">{{ item.text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-cyan-200">Понятные решения</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Не просто статистика — понятные решения</h2>
            <p class="mt-5 text-base leading-8 text-slate-300">
              TrackNode превращает аналитику сайта, тепловые карты кликов, записи сессий и SEO-аудит сайта в конкретные рекомендации для владельца бизнеса.
            </p>
          </div>
          <div class="grid gap-3">
            <article v-for="item in insightExamples" :key="item" class="flex gap-3 rounded-lg border border-cyan-300/18 bg-cyan-300/8 p-4 text-sm leading-6 text-slate-100">
              <CheckCircle2 :size="18" class="mt-0.5 shrink-0 text-emerald-200" />
              <span>{{ item }}</span>
            </article>
          </div>
        </div>
      </section>

      <section id="analytics" class="border-b border-white/10 bg-[#070b10] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid gap-10 lg:grid-cols-[0.95fr_1.05fr]">
            <div>
              <p class="text-sm font-semibold text-amber-200">Аналитика поведения</p>
              <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Смотрите не только сколько людей пришло, но и что они делали на сайте</h2>
              <p class="mt-5 text-base leading-8 text-slate-300">
                Поведенческая аналитика помогает понять, какие блоки видят пользователи, где кликают, на каком шаге уходят и почему заявок меньше, чем должно быть.
              </p>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <article v-for="[title, text] in behaviorItems" :key="title" class="rounded-lg border border-white/10 bg-white/6 p-5 backdrop-blur">
                <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
                <p class="mt-2 text-sm leading-6 text-slate-300">{{ text }}</p>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div class="rounded-lg border border-white/10 bg-white/6 p-6 backdrop-blur">
            <Inbox :size="24" class="text-cyan-200" />
            <h2 class="mt-5 text-3xl font-semibold text-white">Все заявки в одном кабинете</h2>
            <p class="mt-4 text-base leading-8 text-slate-300">
              TrackNode собирает заявки с сайта, показывает источник, дату, статус и связь с аналитикой. Вы понимаете, какие страницы приводят клиентов, а какие требуют улучшения.
            </p>
          </div>
          <div id="seo" class="rounded-lg border border-white/10 bg-white/6 p-6 backdrop-blur">
            <SearchCheck :size="24" class="text-emerald-200" />
            <h2 class="mt-5 text-3xl font-semibold text-white">SEO-аудит и анализ конкурентов</h2>
            <p class="mt-4 text-base leading-8 text-slate-300">
              Проверяйте title, description, H1, технические ошибки, сравнивайте сайт с конкурентами и выгружайте PDF-отчёты с рекомендациями.
            </p>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#071015] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="max-w-[22rem] sm:max-w-3xl">
            <p class="text-sm font-semibold text-cyan-200">Как работает</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">От подключения до понятных улучшений</h2>
          </div>
          <div class="mt-10 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <article v-for="(step, index) in steps" :key="step[0]" class="rounded-lg border border-white/10 bg-[#0d151b] p-5">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-cyan-300 text-sm font-semibold text-slate-950">{{ index + 1 }}</span>
              <h3 class="mt-5 text-lg font-semibold text-white">{{ step[0] }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-300">{{ step[1] }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-emerald-200">Для кого</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Подходит тем, кто отвечает за результат сайта</h2>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <article v-for="item in audienceCards" :key="item" class="rounded-lg border border-white/10 bg-white/6 p-5 text-sm font-semibold text-slate-100">
              <Globe2 :size="18" class="mb-4 text-cyan-200" />
              {{ item }}
            </article>
          </div>
        </div>
      </section>

      <section class="border-b border-white/10 bg-[#070b10] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-cyan-200">Безопасность</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Безопасная аналитика без лишнего сбора данных</h2>
            <p class="mt-5 text-base leading-8 text-slate-300">
              TrackNode собирает технические и поведенческие сигналы, но не хранит содержимое полей форм, пароли и персональные сообщения пользователей.
            </p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <article v-for="item in securityItems" :key="item" class="flex gap-3 rounded-lg border border-white/10 bg-white/6 p-4 text-sm leading-6 text-slate-200">
              <CheckCircle2 :size="18" class="mt-0.5 shrink-0 text-emerald-200" />
              <span>{{ item }}</span>
            </article>
          </div>
        </div>
      </section>

      <section id="pricing" class="border-b border-white/10 bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="max-w-[22rem] sm:max-w-3xl">
            <p class="text-sm font-semibold text-cyan-200">Тарифы</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Выберите уровень аналитики под задачу</h2>
          </div>
          <div class="mt-10 grid gap-4 lg:grid-cols-3">
            <article
              v-for="plan in pricingPlans"
              :key="plan.name"
              class="relative rounded-lg border p-6 backdrop-blur"
              :class="plan.popular ? 'border-cyan-300/45 bg-cyan-300/10 shadow-[0_24px_80px_rgba(8,145,178,0.18)]' : 'border-white/10 bg-white/6'"
            >
              <span v-if="plan.popular" class="mb-4 inline-flex rounded-lg bg-cyan-300 px-3 py-1 text-xs font-semibold text-slate-950">Популярный</span>
              <h3 class="text-2xl font-semibold text-white">{{ plan.name }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-300">{{ plan.description }}</p>
              <p class="mt-6 text-4xl font-semibold text-white">{{ plan.price }}<span class="text-base font-medium text-slate-400">/мес</span></p>
              <ul class="mt-6 space-y-3">
                <li v-for="feature in plan.features" :key="feature" class="flex gap-3 text-sm leading-6 text-slate-200">
                  <CheckCircle2 :size="17" class="mt-0.5 shrink-0 text-emerald-200" />
                  <span>{{ feature }}</span>
                </li>
              </ul>
              <RouterLink to="/login" class="mt-7 inline-flex min-h-11 w-full items-center justify-center rounded-lg bg-white px-4 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100">
                Начать
              </RouterLink>
            </article>
          </div>
        </div>
      </section>

      <section id="faq" class="border-b border-white/10 bg-[#071015] py-16 sm:py-20">
        <div class="mx-auto grid w-full max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
          <div>
            <p class="text-sm font-semibold text-cyan-200">FAQ</p>
            <h2 class="mt-3 text-3xl font-semibold text-white sm:text-4xl">Ответы на частые вопросы</h2>
          </div>
          <div class="grid gap-3">
            <details v-for="[question, answer] in faqItems" :key="question" class="group rounded-lg border border-white/10 bg-white/6 p-5">
              <summary class="flex cursor-pointer list-none items-center justify-between gap-4 text-base font-semibold text-white">
                {{ question }}
                <ArrowRight :size="18" class="shrink-0 transition group-open:rotate-90" />
              </summary>
              <p class="mt-3 text-sm leading-6 text-slate-300">{{ answer }}</p>
            </details>
          </div>
        </div>
      </section>

      <section class="bg-[#05070a] py-16 sm:py-20">
        <div class="mx-auto w-full max-w-7xl px-4 text-center sm:px-6 lg:px-8">
            <div class="mx-auto max-w-[22rem] sm:max-w-3xl">
            <MonitorSmartphone :size="30" class="mx-auto text-cyan-200" />
            <h2 class="mt-5 text-3xl font-semibold text-white sm:text-4xl">Начните понимать свой сайт уже сегодня</h2>
            <p class="mt-5 text-base leading-8 text-slate-300">
              Откройте личный кабинет TrackNode и смотрите аналитику, заявки, SEO и рекомендации в одном месте.
            </p>
            <RouterLink to="/login" class="mt-8 inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-cyan-300 px-6 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">
              Войти в кабинет
              <ArrowRight :size="17" />
            </RouterLink>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
