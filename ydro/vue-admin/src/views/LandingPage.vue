<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ArrowRight,
  BarChart3,
  Blocks,
  CheckCircle2,
  FileSearch,
  FileText,
  Flame,
  Funnel,
  Inbox,
  ListVideo,
  Menu,
  MousePointerClick,
  Route,
  SearchCheck,
  Sparkles,
  X,
  Zap,
} from '@lucide/vue'

const mobileMenuOpen = ref(false)
const cookieVisible = ref(false)
const supportSent = ref(false)
const scrollProgress = ref(0)
const currentYear = new Date().getFullYear()

const supportForm = reactive({
  title: '',
  problem: '',
  description: '',
})

const navItems = [
  { label: 'Возможности', href: '#features' },
  { label: 'Аналитика', href: '#analytics' },
  { label: 'SEO-анализ', href: '#seo-audit' },
  { label: 'Кейсы', href: '#cases' },
  { label: 'Тарифы', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
  { label: 'Поддержка', href: '#support' },
]

const trustBadges = ['A Meditation', 'Новое Конаково', 'Volga', 'Local Business', 'Studio Pro', 'Service Hub', 'Marketing Lab']
const marqueeItems = [...trustBadges, ...trustBadges]

const dashboardMenuItems = [
  ['Главная', BarChart3],
  ['Аналитика', BarChart3],
  ['Поведение', MousePointerClick],
  ['Тепловые карты', Flame],
  ['Записи сессий', ListVideo],
  ['Заявки', Inbox],
  ['SEO-аудит', SearchCheck],
  ['Конкуренты', FileSearch],
  ['Отчёты', FileText],
  ['Настройки', Blocks],
]

const dashboardMetrics = [
  { key: 'visitors', label: 'Посетители', value: 24780, change: 12.3, color: 'text-indigo-600', spark: 'M4 30 L22 38 L40 22 L58 31 L76 18 L94 34 L112 25 L130 30 L148 20' },
  { key: 'views', label: 'Просмотры', value: 71842, change: 8.1, color: 'text-violet-600', spark: 'M4 34 L24 20 L44 34 L64 18 L84 29 L104 22 L124 33 L148 19' },
  { key: 'leads', label: 'Заявки', value: 342, change: 15.7, color: 'text-emerald-600', spark: 'M4 28 L22 34 L40 17 L58 29 L76 22 L94 33 L112 27 L130 31 L148 20' },
  { key: 'conversion', label: 'Конверсия', value: 2.47, change: 0.3, suffix: '%', color: 'text-amber-600', spark: 'M4 29 L22 22 L40 31 L58 21 L76 32 L94 25 L112 34 L130 28 L148 20' },
]

const animatedValues = reactive(Object.fromEntries(dashboardMetrics.map((item) => [item.key, 0])))
const animatedChanges = reactive(Object.fromEntries(dashboardMetrics.map((item) => [item.key, 0])))

const trafficSources = [
  ['Прямые', '40%', 'bg-indigo-600', '78%'],
  ['Поиск', '30%', 'bg-cyan-500', '62%'],
  ['Соцсети', '20%', 'bg-teal-400', '44%'],
  ['Рефералы', '10%', 'bg-violet-500', '28%'],
]

const topPages = [
  ['/services', '12 480'],
  ['/about', '8 320'],
  ['/blog', '6 160'],
  ['/contacts', '2 080'],
]

const heroFeatureCards = [
  { title: 'Веб-аналитика', text: 'Трафик, источники, конверсии', icon: BarChart3 },
  { title: 'Тепловые карты', text: 'Клики, скролл, движение мыши', icon: Flame },
  { title: 'Записи сессий', text: 'Как пользователи работают с сайтом', icon: ListVideo },
  { title: 'SEO-анализ', text: 'Проверка и рекомендации', icon: SearchCheck },
  { title: 'Сравнение конкурентов', text: 'Узнайте, кто вас опережает', icon: FileSearch },
  { title: 'Отчёты', text: 'PDF и email для команды', icon: FileText },
]

const featureCards = [
  { title: 'Веб-аналитика', text: 'Посещения, просмотры, источники трафика и конверсии в одном понятном отчёте.', icon: BarChart3 },
  { title: 'Тепловые карты', text: 'Клики, скролл и зоны внимания помогают увидеть, что реально замечают посетители.', icon: Flame },
  { title: 'Записи сессий', text: 'Смотрите путь пользователя как аккуратную timeline-ленту без лишнего шума.', icon: ListVideo },
  { title: 'Заявки с сайта', text: 'Все обращения попадают в кабинет с источником, страницей и статусом обработки.', icon: Inbox },
  { title: 'SEO-аудит', text: 'Title, description, H1, скорость, индексация и технические ошибки собраны в чек-лист.', icon: SearchCheck },
  { title: 'Анализ конкурентов', text: 'Сравнивайте страницы, офферы и точки роста в вашей нише.', icon: FileSearch },
  { title: 'PDF-отчёты', text: 'Готовьте понятные отчёты для собственника, маркетолога или подрядчика.', icon: FileText },
  { title: 'Telegram-уведомления', text: 'Получайте новые заявки в реальном времени и не теряйте горячие обращения.', icon: Sparkles },
  { title: 'Мультисайтовость', text: 'Управляйте несколькими проектами из одного кабинета без переключения инструментов.', icon: Blocks },
]

const analyticsCards = [
  { title: 'Путь до заявки', text: 'TrackNode показывает шаги, где пользователь заинтересовался, отвлёкся или ушёл.', icon: Route },
  { title: 'Воронка конверсии', text: 'Понимайте, какие страницы дают заявки, а какие только потребляют рекламный бюджет.', icon: Funnel },
  { title: 'Поведение на блоках', text: 'Клики, скролл и активность по секциям помогают перестроить посадочные страницы.', icon: MousePointerClick },
]

const seoRecommendations = [
  ['Высокий приоритет', 'Добавить уникальные title для 8 страниц услуг'],
  ['Средний приоритет', 'Усилить H1 и первые экраны коммерческих страниц'],
  ['Средний приоритет', 'Сжать изображения на мобильной версии'],
  ['Низкий приоритет', 'Добавить FAQ-разметку для поисковых сниппетов'],
]

const competitorRows = [
  ['Вы', 88, 'bg-indigo-600'],
  ['site1.ru', 72, 'bg-violet-500'],
  ['site2.ru', 61, 'bg-cyan-500'],
  ['site3.ru', 54, 'bg-slate-300'],
]

const caseCards = [
  {
    title: 'Рост органического трафика',
    problem: 'Страницы услуг не индексировались и теряли показы.',
    action: 'TrackNode нашёл технические ошибки, дубли title и слабые коммерческие сигналы.',
    result: '+46%',
    bars: [38, 46, 52, 68, 84],
  },
  {
    title: 'Больше заявок с посадочной',
    problem: 'Пользователи читали страницу, но редко отправляли форму.',
    action: 'Тепловая карта показала слабую CTA-зону, рекомендации помогли перестроить блоки.',
    result: '+31%',
    bars: [30, 35, 44, 59, 72],
  },
  {
    title: 'Меньше потерь обращений',
    problem: 'Часть заявок терялась между формой, менеджером и каналами связи.',
    action: 'TrackNode связал заявки, источники и Telegram-уведомления в единый поток.',
    result: '-28%',
    bars: [82, 69, 62, 51, 42],
  },
  {
    title: 'Точки роста против конкурентов',
    problem: 'Было непонятно, почему конкуренты получают больше поискового трафика.',
    action: 'Сравнение страниц показало недостающие разделы, FAQ и слабые сниппеты.',
    result: '+19%',
    bars: [44, 51, 58, 63, 71],
  },
]

const pricingPlans = [
  {
    name: 'Старт',
    price: '2 990 ₽',
    period: '/ месяц',
    description: 'Для одного сайта и базового контроля заявок.',
    features: [
      'CMS для управления сайтом',
      'Хостинг',
      'Telegram-уведомления о заявках в реальном времени',
      'Базовая поддержка',
      'Подключение 1 сайта',
    ],
  },
  {
    name: 'Pro',
    price: '6 990 ₽',
    period: '/ месяц',
    description: 'Для роста заявок, SEO и анализа поведения.',
    popular: true,
    features: [
      'Всё из тарифа Старт',
      'SEO-аудит',
      'Анализ конкурента',
      'Аналитика сайта',
      'Подключение до 3 сайтов',
      'Расширенные рекомендации',
    ],
  },
  {
    name: 'Business',
    price: 'Индивидуально',
    period: 'по запросу',
    description: 'Для компаний, агентств и нескольких проектов.',
    features: [
      'Всё из тарифа Pro',
      'Расширенная мультисайтовость',
      'Вся аналитика',
      'Командная работа',
      'Расширенные отчёты',
      'Приоритетная техподдержка',
    ],
  },
]

const faqItems = [
  ['Что такое TrackNode?', 'Это SaaS-платформа для аналитики сайта, заявок, SEO-аудита, анализа конкурентов и понятных рекомендаций в одном кабинете.'],
  ['Нужно ли устанавливать код на сайт?', 'Да, для тепловых карт, записей сессий и событий нужен короткий код трекера. Подключение занимает несколько минут.'],
  ['Можно ли подключить несколько сайтов?', 'Да, TrackNode поддерживает мультисайтовость. Количество сайтов зависит от тарифа.'],
  ['Где смотреть заявки?', 'Заявки отображаются в кабинете вместе с источником, страницей, датой, статусом и связанной аналитикой.'],
  ['Есть ли SEO-аудит и конкуренты?', 'Да. В кабинете доступны SEO-аудит, сравнение с конкурентами и отчёты с рекомендациями.'],
  ['Безопасно ли собирать поведение пользователей?', 'TrackNode не сохраняет пароли и чувствительные значения полей форм. Аналитика нужна для улучшения сайта и сервиса.'],
]

let revealObserver
let metricFrame

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function formatMetric(item) {
  const value = animatedValues[item.key] || 0
  if (item.suffix === '%') return `${value.toFixed(2)}%`
  return new Intl.NumberFormat('ru-RU').format(Math.round(value))
}

function formatChange(item) {
  return `+${(animatedChanges[item.key] || 0).toFixed(1)}%`
}

function updateScrollProgress() {
  const element = document.documentElement
  const scrollable = element.scrollHeight - element.clientHeight
  scrollProgress.value = scrollable > 0 ? Math.min(100, Math.max(0, (window.scrollY / scrollable) * 100)) : 0
}

function animateMetrics() {
  const startedAt = performance.now()
  const duration = 1400

  const tick = (now) => {
    const progress = Math.min(1, (now - startedAt) / duration)
    const eased = 1 - (1 - progress) ** 3

    dashboardMetrics.forEach((item) => {
      animatedValues[item.key] = item.value * eased
      animatedChanges[item.key] = item.change * eased
    })

    if (progress < 1) {
      metricFrame = requestAnimationFrame(tick)
    }
  }

  metricFrame = requestAnimationFrame(tick)
}

function submitSupport() {
  // TODO: подключить публичный API поддержки, когда в backend появится отдельный endpoint.
  supportSent.value = true
  supportForm.title = ''
  supportForm.problem = ''
  supportForm.description = ''
}

function acceptCookies() {
  localStorage.setItem('tracknode_cookie_consent', 'accepted')
  cookieVisible.value = false
}

onMounted(() => {
  cookieVisible.value = localStorage.getItem('tracknode_cookie_consent') !== 'accepted'
  updateScrollProgress()
  animateMetrics()

  window.addEventListener('scroll', updateScrollProgress, { passive: true })
  window.addEventListener('resize', updateScrollProgress)

  document.querySelectorAll('.hero-section .tn-reveal').forEach((element) => {
    element.classList.add('is-visible')
  })

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          revealObserver.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.16, rootMargin: '0px 0px -8% 0px' },
  )

  document.querySelectorAll('.tn-reveal:not(.is-visible)').forEach((element) => revealObserver.observe(element))
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateScrollProgress)
  window.removeEventListener('resize', updateScrollProgress)
  if (revealObserver) revealObserver.disconnect()
  if (metricFrame) cancelAnimationFrame(metricFrame)
})
</script>

<template>
  <div class="landing-page min-h-screen overflow-x-hidden bg-[#f7f8ff] text-slate-950">
    <header class="sticky top-0 z-50 border-b border-indigo-100/80 bg-white/82 shadow-[0_10px_36px_rgba(47,42,120,0.05)] backdrop-blur-xl">
      <div class="mx-auto flex min-h-[76px] w-full max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <a href="#top" class="flex min-w-0 items-center gap-3" aria-label="TrackNode">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-[#5B35F5] to-[#1D5CFF] text-white shadow-[0_16px_34px_rgba(75,54,240,0.28)]">
            <Zap :size="23" fill="currentColor" />
          </span>
          <span class="truncate text-xl font-semibold text-slate-950">TrackNode</span>
        </a>

        <nav class="hidden items-center gap-7 xl:flex" aria-label="Основная навигация">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="text-sm font-semibold text-slate-700 transition hover:text-[#4C33E6]"
          >
            {{ item.label }}
          </a>
        </nav>

        <RouterLink
          to="/login"
          class="hidden min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#5B35F5] to-[#1D4FFF] px-5 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(59,55,238,0.28)] transition hover:-translate-y-0.5 hover:shadow-[0_18px_42px_rgba(59,55,238,0.36)] xl:inline-flex"
        >
          Войти в кабинет
          <ArrowRight :size="17" />
        </RouterLink>

        <button
          type="button"
          class="mobile-menu-button grid h-11 w-11 place-items-center rounded-lg border border-indigo-100 bg-white text-[#4C33E6] shadow-sm xl:hidden"
          :aria-expanded="mobileMenuOpen"
          aria-label="Открыть меню"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <X v-if="mobileMenuOpen" :size="21" />
          <Menu v-else :size="21" />
        </button>
      </div>
      <div class="h-px bg-indigo-100/70">
        <span class="progress-line block h-full bg-gradient-to-r from-[#5B35F5] via-[#1D5CFF] to-[#35C9B8]" :style="{ transform: `scaleX(${scrollProgress / 100})` }" />
      </div>

      <div v-if="mobileMenuOpen" class="border-t border-indigo-100 bg-white px-4 py-4 xl:hidden">
        <nav class="mx-auto grid max-w-[1440px] gap-2" aria-label="Мобильная навигация">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="rounded-lg px-3 py-3 text-sm font-semibold text-slate-700 hover:bg-indigo-50"
            @click="closeMobileMenu"
          >
            {{ item.label }}
          </a>
          <RouterLink
            to="/login"
            class="mt-2 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#4C33E6] px-4 text-sm font-semibold text-white"
            @click="closeMobileMenu"
          >
            Войти в кабинет
          </RouterLink>
        </nav>
      </div>
    </header>

    <main id="top">
      <section class="hero-section relative overflow-hidden">
        <div class="mx-auto grid min-h-[720px] w-full max-w-[1440px] items-center gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[0.74fr_1.26fr] lg:px-8 lg:py-14">
          <div class="tn-reveal relative z-10">
            <p class="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/78 px-4 py-2 text-xs font-semibold text-[#4338CA] shadow-sm backdrop-blur">
              <Sparkles :size="16" />
              Аналитика нового поколения
            </p>

            <h1 class="mt-7 max-w-[660px] text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl lg:text-[3.3rem]">
              Понимайте, что происходит
              <span class="block bg-gradient-to-r from-[#1D4FFF] via-[#4C33E6] to-[#7C3AED] bg-clip-text text-transparent">с вашим сайтом</span>
            </h1>

            <p class="mt-6 max-w-[610px] text-base leading-8 text-slate-600 sm:text-lg">
              TrackNode объединяет аналитику, заявки, SEO-аудит, конкурентов и отчёты в одном кабинете. Всё, что нужно для роста сайта и бизнеса.
            </p>

            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <RouterLink
                to="/login"
                class="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#5B35F5] to-[#1D4FFF] px-6 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(59,55,238,0.32)] transition hover:-translate-y-0.5 hover:shadow-[0_22px_48px_rgba(59,55,238,0.4)]"
              >
                Попробовать бесплатно
                <Zap :size="17" fill="currentColor" />
              </RouterLink>
              <a href="#features" class="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg border border-indigo-100 bg-white/75 px-6 text-sm font-semibold text-[#3524B6] shadow-sm transition hover:-translate-y-0.5 hover:bg-white">
                <span class="grid h-9 w-9 place-items-center rounded-full bg-indigo-50">
                  <ArrowRight :size="16" />
                </span>
                Смотреть возможности
              </a>
            </div>

            <div class="mt-8 flex flex-wrap items-center gap-5 text-sm text-slate-600">
              <div class="flex items-center">
                <span v-for="index in 5" :key="index" class="-ml-2 first:ml-0 grid h-10 w-10 place-items-center rounded-full border-2 border-white bg-gradient-to-br from-indigo-100 to-white text-xs font-semibold text-[#4C33E6] shadow-sm">
                  {{ index === 5 ? '+120' : index }}
                </span>
              </div>
              <div>
                <p class="font-semibold text-slate-900">5.0 из 5</p>
                <p class="text-xs">Нам доверяют более 120 компаний</p>
              </div>
            </div>
          </div>

          <div class="tn-reveal dashboard-shell relative z-10">
            <div class="dashboard-window">
              <aside class="dashboard-sidebar">
                <div class="flex items-center gap-3 px-3">
                  <span class="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-[#5B35F5] to-[#1D5CFF] text-white">
                    <Zap :size="18" fill="currentColor" />
                  </span>
                  <strong class="text-base text-white">TrackNode</strong>
                </div>

                <nav class="mt-7 grid gap-1">
                  <div
                    v-for="([item, icon], index) in dashboardMenuItems"
                    :key="item"
                    class="flex min-h-10 items-center gap-3 rounded-lg px-3 text-xs font-semibold"
                    :class="index === 0 ? 'bg-white/10 text-white' : 'text-indigo-100/80'"
                  >
                    <component :is="icon" :size="16" />
                    <span class="truncate">{{ item }}</span>
                  </div>
                </nav>

                <div class="mt-auto rounded-xl border border-white/10 bg-white/8 p-4 text-white shadow-[0_16px_40px_rgba(0,0,0,0.18)]">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-semibold">Тариф Pro</p>
                      <p class="mt-2 text-xs leading-5 text-indigo-100/78">До 3 сайтов, SEO и расширенные отчёты</p>
                    </div>
                    <span class="text-indigo-100/60">×</span>
                  </div>
                  <RouterLink to="/login" class="mt-4 inline-flex min-h-10 w-full items-center justify-center rounded-lg bg-gradient-to-r from-[#5B35F5] to-[#1D4FFF] text-xs font-semibold text-white">
                    Управлять
                  </RouterLink>
                </div>
              </aside>

              <div class="min-w-0 flex-1 p-4 sm:p-5">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div class="flex items-center gap-4">
                    <h2 class="text-2xl font-semibold text-slate-950">Обзор</h2>
                    <span class="hidden rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 sm:inline-flex">Все сайты</span>
                  </div>
                  <span class="inline-flex w-fit rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600">25 мая — 24 июн 2026</span>
                </div>

                <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <article v-for="item in dashboardMetrics" :key="item.key" class="metric-card">
                    <p class="text-xs font-semibold text-slate-500">{{ item.label }}</p>
                    <div class="mt-3 flex items-end justify-between gap-3">
                      <strong class="text-2xl font-semibold text-slate-950">{{ formatMetric(item) }}</strong>
                      <span class="text-xs font-semibold text-emerald-600">{{ formatChange(item) }}</span>
                    </div>
                    <svg viewBox="0 0 152 44" class="mt-2 h-9 w-full" role="img" :aria-label="`Мини-график: ${item.label}`">
                      <path :d="item.spark" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="mini-chart" :class="item.color" />
                    </svg>
                  </article>
                </div>

                <div class="mt-4 grid gap-4 xl:grid-cols-[1.18fr_0.82fr]">
                  <article class="dashboard-panel min-h-[236px]">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                      <h3 class="text-sm font-semibold text-slate-950">График посетителей</h3>
                      <div class="flex gap-4 text-xs text-slate-500">
                        <span class="inline-flex items-center gap-2"><i class="h-1.5 w-4 rounded-full bg-[#4C33E6]" />Посетители</span>
                        <span class="inline-flex items-center gap-2"><i class="h-1.5 w-4 rounded-full bg-slate-300" />Предыдущий период</span>
                      </div>
                    </div>
                    <svg viewBox="0 0 560 210" class="mt-4 h-[190px] w-full" role="img" aria-label="Анимированный график посетителей">
                      <path d="M28 174H532M28 132H532M28 90H532M28 48H532" stroke="#E7EAF5" stroke-width="1" />
                      <path d="M42 150 C72 130 83 110 104 89 C131 62 145 142 178 116 C205 95 220 101 246 86 C273 68 292 151 320 120 C348 89 372 106 402 77 C430 49 450 139 478 108 C502 83 516 88 532 72" fill="none" stroke="#CBD5E1" stroke-width="3" stroke-dasharray="7 9" />
                      <path class="hero-chart-line" d="M42 146 C72 112 88 74 111 42 C136 78 151 118 178 93 C203 70 221 88 248 71 C276 49 292 127 322 91 C351 58 374 82 404 48 C431 20 450 112 480 78 C503 52 520 66 532 58" fill="none" stroke="#4C33E6" stroke-width="5" stroke-linecap="round" />
                      <circle class="chart-dot" cx="111" cy="42" r="6" fill="#4C33E6" />
                      <circle class="chart-dot delay-1" cx="248" cy="71" r="6" fill="#4C33E6" />
                      <circle class="chart-dot delay-2" cx="404" cy="48" r="6" fill="#4C33E6" />
                    </svg>
                  </article>

                  <article class="dashboard-panel min-h-[236px]">
                    <h3 class="text-sm font-semibold text-slate-950">Тепловая карта кликов</h3>
                    <div class="heatmap mt-4" role="img" aria-label="Тепловая карта кликов">
                      <span class="heat-line top-[18%] left-[10%] w-[70%]" />
                      <span class="heat-line top-[32%] left-[12%] w-[58%]" />
                      <span class="heat-line top-[48%] left-[9%] w-[78%]" />
                      <span class="heat-line top-[68%] left-[14%] w-[46%]" />
                      <span class="heat-blob heat-a" />
                      <span class="heat-blob heat-b" />
                      <span class="heat-blob heat-c" />
                      <span class="heat-blob heat-d" />
                      <strong class="absolute bottom-4 right-4 rounded-lg bg-white/92 px-3 py-2 text-xs shadow-sm">Кликов: 1842</strong>
                    </div>
                  </article>
                </div>

                <div class="mt-4 grid gap-4 xl:grid-cols-3">
                  <article class="dashboard-panel">
                    <h3 class="text-sm font-semibold text-slate-950">Источники трафика</h3>
                    <div class="mt-4 grid grid-cols-[96px_1fr] items-center gap-4">
                      <div class="donut-chart"><span>24 780</span></div>
                      <div class="space-y-3">
                        <div v-for="[source, value, color, width] in trafficSources" :key="source" class="grid grid-cols-[74px_1fr_36px] items-center gap-2 text-xs">
                          <span class="text-slate-500">{{ source }}</span>
                          <span class="h-1.5 overflow-hidden rounded-full bg-slate-100">
                            <span class="block h-full rounded-full" :class="color" :style="{ width }" />
                          </span>
                          <strong class="text-right text-slate-700">{{ value }}</strong>
                        </div>
                      </div>
                    </div>
                  </article>

                  <article class="dashboard-panel">
                    <h3 class="text-sm font-semibold text-slate-950">Топ страниц</h3>
                    <div class="mt-4 space-y-3">
                      <div v-for="[page, count] in topPages" :key="page" class="grid grid-cols-[1fr_auto] items-center gap-4 text-xs">
                        <span class="font-semibold text-slate-700">{{ page }}</span>
                        <span class="text-slate-500">{{ count }}</span>
                        <span class="col-span-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                          <span class="block h-full rounded-full bg-[#4C33E6]" :style="{ width: page === '/services' ? '86%' : page === '/about' ? '68%' : page === '/blog' ? '54%' : '32%' }" />
                        </span>
                      </div>
                    </div>
                  </article>

                  <article class="dashboard-panel">
                    <h3 class="text-sm font-semibold text-slate-950">AI-рекомендации</h3>
                    <div class="mt-4 space-y-3 text-xs leading-5 text-slate-600">
                      <p class="flex gap-2"><Sparkles :size="14" class="mt-0.5 shrink-0 text-[#4C33E6]" />Увеличьте контраст кнопок на главном экране</p>
                      <p class="flex gap-2"><Sparkles :size="14" class="mt-0.5 shrink-0 text-[#4C33E6]" />Добавьте отзывы клиентов на страницу услуг</p>
                      <p class="flex gap-2"><Sparkles :size="14" class="mt-0.5 shrink-0 text-[#4C33E6]" />Оптимизируйте изображения для мобильных устройств</p>
                    </div>
                  </article>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mx-auto grid w-full max-w-[1440px] gap-4 px-4 pb-12 sm:px-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 xl:px-8">
          <article v-for="item in heroFeatureCards" :key="item.title" class="tn-reveal hero-mini-card">
            <component :is="item.icon" :size="22" class="text-[#4C33E6]" />
            <h3 class="mt-4 text-base font-semibold text-slate-950">{{ item.title }}</h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.text }}</p>
          </article>
        </div>
      </section>

      <section id="features" class="section-band bg-white">
        <div class="landing-container">
          <div class="section-title tn-reveal">
            <p>Возможности платформы</p>
            <h2>Один кабинет для аналитики, заявок и роста</h2>
          </div>
          <div class="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <article v-for="item in featureCards" :key="item.title" class="tn-reveal feature-card">
              <span class="feature-icon"><component :is="item.icon" :size="22" /></span>
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.text }}</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section id="analytics" class="section-band bg-[#f7f8ff]">
        <div class="landing-container grid gap-8 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
          <div class="tn-reveal">
            <div class="section-title text-left">
              <p>Интерактивная аналитика</p>
              <h2>Цифры превращаются в понятные решения</h2>
            </div>
            <div class="mt-7 grid gap-4">
              <article v-for="item in analyticsCards" :key="item.title" class="feature-card">
                <span class="feature-icon"><component :is="item.icon" :size="22" /></span>
                <div>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.text }}</p>
                </div>
              </article>
            </div>
          </div>

          <div class="tn-reveal analytics-board">
            <div class="grid gap-4 md:grid-cols-[1.05fr_0.95fr]">
              <article class="dashboard-panel">
                <h3 class="text-base font-semibold text-slate-950">Воронка заявок</h3>
                <div class="mt-5 space-y-4">
                  <div v-for="([label, value], index) in [['Посещения', '24 780'], ['Клики по CTA', '3 218'], ['Формы открыты', '914'], ['Заявки', '342']]" :key="label" class="rounded-lg border border-indigo-100 bg-white p-4">
                    <div class="flex items-center justify-between gap-3 text-sm">
                      <span class="font-semibold text-slate-700">{{ label }}</span>
                      <strong class="text-slate-950">{{ value }}</strong>
                    </div>
                    <span class="mt-3 block h-2 overflow-hidden rounded-full bg-slate-100">
                      <span class="block h-full rounded-full bg-gradient-to-r from-[#5B35F5] to-[#35C9B8]" :style="{ width: `${92 - index * 18}%` }" />
                    </span>
                  </div>
                </div>
              </article>
              <article class="dashboard-panel">
                <h3 class="text-base font-semibold text-slate-950">Записи сессий</h3>
                <div class="mt-5 space-y-3">
                  <div v-for="([session, time, status], index) in [['Сессия #1254', '02:36', 'Заявка'], ['Сессия #1253', '04:18', 'SEO'], ['Сессия #1252', '01:54', 'Отказ'], ['Сессия #1251', '03:22', 'CTA']]" :key="session" class="flex items-center gap-3 rounded-lg border border-indigo-100 bg-white p-3">
                    <span class="grid h-9 w-9 place-items-center rounded-lg bg-indigo-50 text-[#4C33E6]"><ListVideo :size="17" /></span>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-semibold text-slate-900">{{ session }}</p>
                      <p class="text-xs text-slate-500">{{ status }}</p>
                    </div>
                    <strong class="text-xs text-slate-600">{{ time }}</strong>
                    <ArrowRight :size="15" class="text-[#4C33E6]" />
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section id="seo-audit" class="section-band bg-white">
        <div class="landing-container grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div class="tn-reveal seo-score-card">
            <div class="grid gap-6 md:grid-cols-[180px_1fr] md:items-center">
              <div class="score-ring">
                <strong>85</strong>
                <span>/100</span>
              </div>
              <div>
                <p class="text-sm font-semibold text-[#4C33E6]">SEO-аудит и рекомендации</p>
                <h2 class="mt-3 text-3xl font-semibold leading-tight text-slate-950">Проверка, которую можно сразу отдать в работу</h2>
                <p class="mt-4 text-base leading-8 text-slate-600">
                  TrackNode показывает технические ошибки, слабые мета-теги, проблемы индексации и конкретные шаги для роста органического трафика.
                </p>
              </div>
            </div>
          </div>
          <div class="tn-reveal grid gap-3">
            <article v-for="[priority, text] in seoRecommendations" :key="text" class="recommendation-row">
              <span><SearchCheck :size="18" /></span>
              <div>
                <p class="text-xs font-semibold text-[#4C33E6]">{{ priority }}</p>
                <h3 class="mt-1 text-sm font-semibold text-slate-950">{{ text }}</h3>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section id="competitors" class="section-band bg-[#f7f8ff]">
        <div class="landing-container grid gap-8 lg:grid-cols-[0.86fr_1.14fr] lg:items-center">
          <div class="tn-reveal">
            <div class="section-title text-left">
              <p>Анализ конкурентов</p>
              <h2>Видно, где вы сильнее и где можно расти</h2>
            </div>
            <p class="mt-5 max-w-xl text-base leading-8 text-slate-600">
              Сравнивайте SEO-сигналы, структуру страниц, коммерческие блоки и видимость конкурентов. Кабинет помогает быстро понять, какие изменения дадут эффект.
            </p>
          </div>

          <div class="tn-reveal competitor-card">
            <div class="grid h-[280px] grid-cols-4 items-end gap-5">
              <div v-for="[label, value, color] in competitorRows" :key="label" class="flex h-full flex-col justify-end">
                <div class="rounded-t-lg shadow-[0_14px_34px_rgba(76,51,230,0.14)]" :class="color" :style="{ height: `${value}%` }" />
                <p class="mt-3 truncate text-center text-sm font-semibold text-slate-700">{{ label }}</p>
              </div>
            </div>
            <div class="mt-6 grid gap-3 md:grid-cols-3">
              <div class="rounded-lg bg-indigo-50 p-4">
                <p class="text-xs text-slate-500">SEO-счёт</p>
                <strong class="mt-1 block text-2xl text-slate-950">88</strong>
              </div>
              <div class="rounded-lg bg-white p-4">
                <p class="text-xs text-slate-500">Точки роста</p>
                <strong class="mt-1 block text-2xl text-slate-950">14</strong>
              </div>
              <div class="rounded-lg bg-white p-4">
                <p class="text-xs text-slate-500">Риск потерь</p>
                <strong class="mt-1 block text-2xl text-emerald-600">низкий</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="cases" class="section-band bg-white">
        <div class="landing-container">
          <div class="section-title tn-reveal">
            <p>Кейсы SEO-оптимизации</p>
            <h2>Понятные сценарии, где TrackNode показывает эффект</h2>
          </div>
          <div class="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <article v-for="item in caseCards" :key="item.title" class="tn-reveal case-card">
              <div class="flex items-start justify-between gap-4">
                <h3>{{ item.title }}</h3>
                <strong>{{ item.result }}</strong>
              </div>
              <p><span>Проблема:</span> {{ item.problem }}</p>
              <p><span>Что сделал TrackNode:</span> {{ item.action }}</p>
              <div class="mt-auto flex h-24 items-end gap-2 pt-5">
                <i v-for="(bar, index) in item.bars" :key="`${item.title}-${index}`" class="case-bar" :style="{ height: `${bar}%` }" />
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class="section-band bg-[#f7f8ff]">
        <div class="landing-container">
          <div class="section-title tn-reveal">
            <p>Нам доверяют компании</p>
            <h2>Проекты, которые уже подключены к TrackNode</h2>
          </div>
          <div class="tn-reveal marquee-shell mt-8" aria-label="Бегущая строка компаний">
            <div class="marquee-track">
              <span v-for="(item, index) in marqueeItems" :key="`${item}-${index}`" class="marquee-pill">{{ item }}</span>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" class="section-band bg-white">
        <div class="landing-container">
          <div class="section-title tn-reveal">
            <p>Тарифы</p>
            <h2>Выберите формат подключения</h2>
          </div>
          <div class="mt-10 grid items-stretch gap-5 lg:grid-cols-3">
            <article
              v-for="plan in pricingPlans"
              :key="plan.name"
              class="tn-reveal pricing-card"
              :class="{ 'is-popular': plan.popular }"
            >
              <div v-if="plan.popular" class="popular-badge">Популярный</div>
              <h3>{{ plan.name }}</h3>
              <p class="mt-2 min-h-[48px] text-sm leading-6 text-slate-600">{{ plan.description }}</p>
              <div class="mt-6">
                <strong class="text-3xl font-semibold text-slate-950">{{ plan.price }}</strong>
                <span class="ml-2 text-sm font-semibold text-slate-500">{{ plan.period }}</span>
              </div>
              <ul class="mt-7 grid gap-3">
                <li v-for="feature in plan.features" :key="feature">
                  <CheckCircle2 :size="17" />
                  <span>{{ feature }}</span>
                </li>
              </ul>
              <RouterLink
                to="/login"
                class="mt-auto inline-flex min-h-12 w-full items-center justify-center rounded-lg text-sm font-semibold transition"
                :class="plan.popular ? 'bg-gradient-to-r from-[#5B35F5] to-[#1D4FFF] text-white shadow-[0_16px_34px_rgba(59,55,238,0.28)] hover:-translate-y-0.5' : 'border border-indigo-200 bg-white text-[#4C33E6] hover:bg-indigo-50'"
              >
                Попробовать тариф
              </RouterLink>
            </article>
          </div>
        </div>
      </section>

      <section id="faq" class="section-band bg-[#f7f8ff]">
        <div class="landing-container grid gap-8 lg:grid-cols-[0.75fr_1.25fr]">
          <div class="tn-reveal">
            <div class="section-title text-left">
              <p>FAQ</p>
              <h2>Частые вопросы о TrackNode</h2>
            </div>
            <p class="mt-5 text-base leading-8 text-slate-600">Коротко о подключении, аналитике, заявках, SEO и безопасности данных.</p>
          </div>
          <div class="tn-reveal grid gap-3">
            <details v-for="[question, answer] in faqItems" :key="question" class="faq-item">
              <summary>
                <span>{{ question }}</span>
                <ArrowRight :size="18" />
              </summary>
              <p>{{ answer }}</p>
            </details>
          </div>
        </div>
      </section>

      <section id="support" class="section-band bg-white">
        <div class="landing-container grid gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
          <div class="tn-reveal">
            <div class="section-title text-left">
              <p>Техническая поддержка</p>
              <h2>Опишите вопрос, и команда поможет разобраться</h2>
            </div>
            <p class="mt-5 max-w-xl text-base leading-8 text-slate-600">
              Форма подготовлена на фронте. Когда появится публичный endpoint поддержки, её можно подключить без изменения интерфейса.
            </p>
            <a href="https://t.me/M1ke994" target="_blank" rel="noopener noreferrer" class="mt-7 inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-indigo-200 bg-white px-5 text-sm font-semibold text-[#4C33E6] shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-50">
              Связаться через Telegram
              <ArrowRight :size="17" />
            </a>
          </div>

          <form class="tn-reveal support-form" @submit.prevent="submitSupport">
            <label>
              <span>Заголовок</span>
              <input v-model="supportForm.title" required type="text" placeholder="Например: не вижу заявки в кабинете" />
            </label>
            <label>
              <span>Проблема</span>
              <input v-model="supportForm.problem" required type="text" placeholder="Кратко опишите, что произошло" />
            </label>
            <label>
              <span>Описание</span>
              <textarea v-model="supportForm.description" required rows="5" placeholder="Добавьте детали: сайт, раздел, время, что уже проверили" />
            </label>
            <button type="submit">Отправить</button>
            <p v-if="supportSent" class="rounded-lg bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">
              Обращение сохранено на стороне интерфейса. Для срочного вопроса используйте Telegram.
            </p>
          </form>
        </div>
      </section>
    </main>

    <footer class="border-t border-indigo-100 bg-[#080B23] py-12 text-white" id="footer">
      <div class="landing-container grid gap-8 md:grid-cols-[1.15fr_0.85fr_0.85fr]">
        <div>
          <a href="#top" class="inline-flex items-center gap-3" aria-label="TrackNode">
            <span class="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-[#5B35F5] to-[#1D5CFF] text-white">
              <Zap :size="21" fill="currentColor" />
            </span>
            <strong class="text-xl">TrackNode</strong>
          </a>
          <p class="mt-5 max-w-md text-sm leading-7 text-indigo-100/75">
            SaaS-платформа для аналитики сайтов, заявок, SEO-аудита, анализа конкурентов и отчётов в одном кабинете.
          </p>
          <p class="mt-6 text-sm text-indigo-100/60">© {{ currentYear }} TrackNode</p>
        </div>
        <div>
          <h2 class="text-sm font-semibold text-white">Документы</h2>
          <div class="mt-4 grid gap-3 text-sm text-indigo-100/75">
            <a href="#footer" class="hover:text-white">Пользовательское соглашение</a>
            <a href="#footer" class="hover:text-white">Политика конфиденциальности</a>
            <a href="#pricing" class="hover:text-white">Тарифы</a>
            <a href="#support" class="hover:text-white">Поддержка</a>
          </div>
        </div>
        <div>
          <h2 class="text-sm font-semibold text-white">Контакты</h2>
          <div class="mt-4 grid gap-3 text-sm text-indigo-100/75">
            <a href="https://t.me/M1ke994" target="_blank" rel="noopener noreferrer" class="hover:text-white">Telegram: @M1ke994</a>
            <RouterLink to="/login" class="hover:text-white">Войти в кабинет</RouterLink>
          </div>
        </div>
      </div>
    </footer>

    <div v-if="cookieVisible" class="cookie-popup" role="dialog" aria-live="polite" aria-label="Уведомление о cookies">
      <div>
        <p class="font-semibold text-slate-950">Cookies и аналитика</p>
        <p class="mt-1 text-sm leading-6 text-slate-600">Сайт использует cookies для аналитики и улучшения сервиса.</p>
      </div>
      <button type="button" @click="acceptCookies">Принять</button>
    </div>
  </div>
</template>

<style scoped>
:global(html) {
  scroll-behavior: smooth;
}

.landing-page {
  --tn-primary: #4c33e6;
  --tn-blue: #1d5cff;
  --tn-teal: #35c9b8;
}

.progress-line {
  transform-origin: left center;
  transition: transform 120ms linear;
}

.hero-section {
  background:
    linear-gradient(115deg, rgba(255, 255, 255, 0.95) 0%, rgba(247, 248, 255, 0.96) 45%, rgba(238, 242, 255, 0.92) 100%),
    repeating-linear-gradient(90deg, rgba(76, 51, 230, 0.05) 0 1px, transparent 1px 112px);
}

.hero-section::before {
  content: '';
  position: absolute;
  inset: auto -12% -16% -12%;
  height: 300px;
  background: linear-gradient(180deg, transparent 0%, rgba(124, 58, 237, 0.08) 52%, rgba(29, 92, 255, 0.12) 100%);
  clip-path: polygon(0 36%, 15% 22%, 34% 48%, 52% 28%, 70% 44%, 86% 18%, 100% 36%, 100% 100%, 0 100%);
  pointer-events: none;
}

.landing-container {
  width: min(100% - 2rem, 1440px);
  margin-inline: auto;
}

.section-band {
  padding-block: clamp(4rem, 7vw, 6.5rem);
}

.section-title {
  max-width: 760px;
  margin-inline: auto;
  text-align: center;
}

.section-title p {
  display: inline-flex;
  border-radius: 999px;
  background: #eef2ff;
  padding: 0.5rem 1rem;
  color: var(--tn-primary);
  font-size: 0.78rem;
  font-weight: 700;
}

.section-title h2 {
  margin-top: 1rem;
  color: #0f172a;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 650;
  line-height: 1.1;
}

.dashboard-shell {
  filter: drop-shadow(0 34px 70px rgba(59, 55, 238, 0.2));
}

.dashboard-window {
  display: flex;
  min-height: 610px;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 0 0 8px rgba(92, 72, 255, 0.05);
  backdrop-filter: blur(22px);
}

.dashboard-sidebar {
  display: flex;
  width: 178px;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 1rem;
  background: #070a24;
  padding: 1.25rem 1rem;
}

.metric-card,
.dashboard-panel,
.hero-mini-card,
.feature-card,
.analytics-board,
.seo-score-card,
.competitor-card,
.case-card,
.pricing-card,
.support-form {
  border: 1px solid rgba(99, 102, 241, 0.14);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18px 50px rgba(47, 42, 120, 0.08);
  backdrop-filter: blur(18px);
}

.metric-card {
  padding: 1rem;
}

.dashboard-panel {
  padding: 1rem;
}

.mini-chart {
  stroke-dasharray: 220;
  stroke-dashoffset: 220;
  animation: drawMini 1.2s ease forwards;
}

.hero-chart-line {
  stroke-dasharray: 880;
  stroke-dashoffset: 880;
  animation: drawLine 1.8s ease forwards, liveLine 5s ease-in-out infinite 1.8s;
}

.chart-dot {
  opacity: 0;
  animation: dotPulse 2.4s ease-in-out infinite 1.2s;
}

.delay-1 {
  animation-delay: 1.45s;
}

.delay-2 {
  animation-delay: 1.7s;
}

.heatmap {
  position: relative;
  height: 190px;
  overflow: hidden;
  border: 1px solid #e4e7fb;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff, #ffffff);
}

.heat-line {
  position: absolute;
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
}

.heat-blob {
  position: absolute;
  border-radius: 999px;
  filter: blur(9px);
  animation: heatPulse 4s ease-in-out infinite;
}

.heat-a {
  left: 39%;
  top: 22%;
  width: 76px;
  height: 76px;
  background: rgba(239, 68, 68, 0.82);
}

.heat-b {
  left: 23%;
  top: 45%;
  width: 62px;
  height: 62px;
  background: rgba(250, 204, 21, 0.72);
}

.heat-c {
  left: 56%;
  top: 57%;
  width: 58px;
  height: 58px;
  background: rgba(52, 211, 153, 0.68);
}

.heat-d {
  left: 66%;
  top: 31%;
  width: 42px;
  height: 42px;
  background: rgba(45, 212, 191, 0.66);
}

.donut-chart {
  display: grid;
  width: 96px;
  height: 96px;
  place-items: center;
  border-radius: 999px;
  background: conic-gradient(#4c33e6 0 40%, #22c7d5 40% 70%, #35c9b8 70% 90%, #8b5cf6 90% 100%);
  position: relative;
}

.donut-chart::after {
  content: '';
  position: absolute;
  inset: 18px;
  border-radius: 999px;
  background: white;
}

.donut-chart span {
  position: relative;
  z-index: 1;
  font-size: 0.95rem;
  font-weight: 700;
}

.hero-mini-card {
  min-height: 174px;
  padding: 1.25rem;
  transition: transform 260ms ease, box-shadow 260ms ease;
}

.feature-card {
  display: flex;
  min-height: 126px;
  gap: 1rem;
  padding: 1.25rem;
  transition: transform 260ms ease, box-shadow 260ms ease;
}

.feature-card h3 {
  color: #0f172a;
  font-size: 1rem;
  font-weight: 700;
}

.feature-card p {
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.65;
}

.feature-icon {
  display: grid;
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff, #f8fafc);
  color: var(--tn-primary);
}

.hero-mini-card:hover,
.feature-card:hover,
.case-card:hover,
.pricing-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 70px rgba(47, 42, 120, 0.12);
}

.analytics-board,
.seo-score-card,
.competitor-card {
  padding: clamp(1rem, 3vw, 1.5rem);
}

.score-ring {
  display: grid;
  width: 160px;
  height: 160px;
  place-items: center;
  justify-self: center;
  border-radius: 999px;
  background: conic-gradient(#35c9b8 0 85%, #e2e8f0 85% 100%);
  color: #0f172a;
  position: relative;
}

.score-ring::after {
  content: '';
  position: absolute;
  inset: 18px;
  border-radius: 999px;
  background: white;
}

.score-ring strong,
.score-ring span {
  position: relative;
  z-index: 1;
}

.score-ring strong {
  font-size: 2.8rem;
  line-height: 1;
}

.score-ring span {
  margin-top: 3.4rem;
  margin-left: -4.8rem;
  color: #64748b;
  font-size: 0.9rem;
}

.recommendation-row {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  border: 1px solid rgba(99, 102, 241, 0.14);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  padding: 1rem;
  box-shadow: 0 14px 34px rgba(47, 42, 120, 0.06);
}

.recommendation-row span {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 8px;
  background: #eef2ff;
  color: var(--tn-primary);
}

.case-card {
  display: flex;
  min-height: 420px;
  flex-direction: column;
  padding: 1.25rem;
}

.case-card h3 {
  font-size: 1.08rem;
  font-weight: 700;
  line-height: 1.35;
}

.case-card strong {
  flex: 0 0 auto;
  border-radius: 8px;
  background: #ecfdf5;
  padding: 0.45rem 0.65rem;
  color: #059669;
}

.case-card p {
  margin-top: 1rem;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.65;
}

.case-card p span {
  color: #0f172a;
  font-weight: 700;
}

.case-bar {
  width: 100%;
  border-radius: 7px 7px 2px 2px;
  background: linear-gradient(180deg, #5b35f5, #35c9b8);
  transform-origin: bottom;
  animation: growBar 1.2s ease both;
}

.marquee-shell {
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
  padding: 1rem 0;
  box-shadow: 0 16px 44px rgba(47, 42, 120, 0.07);
}

.marquee-track {
  display: flex;
  width: max-content;
  gap: 1rem;
  animation: marquee 24s linear infinite;
}

.marquee-pill {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  padding: 0 1.3rem;
  color: #334155;
  font-size: 0.95rem;
  font-weight: 700;
  box-shadow: 0 12px 30px rgba(47, 42, 120, 0.06);
}

.pricing-card {
  display: flex;
  min-height: 540px;
  flex-direction: column;
  padding: 1.5rem;
  position: relative;
}

.pricing-card.is-popular {
  border-color: rgba(76, 51, 230, 0.38);
  box-shadow: 0 28px 80px rgba(76, 51, 230, 0.16);
}

.popular-badge {
  margin: -1.5rem -1.5rem 1.25rem;
  background: linear-gradient(90deg, #5b35f5, #1d4fff);
  padding: 0.7rem 1rem;
  color: white;
  text-align: center;
  font-size: 0.78rem;
  font-weight: 800;
}

.pricing-card h3 {
  font-size: 1.45rem;
  font-weight: 750;
}

.pricing-card ul {
  margin-bottom: 2rem;
}

.pricing-card li {
  display: flex;
  gap: 0.65rem;
  color: #334155;
  font-size: 0.92rem;
  line-height: 1.5;
}

.pricing-card li svg {
  margin-top: 0.15rem;
  flex: 0 0 auto;
  color: var(--tn-primary);
}

.faq-item {
  border: 1px solid rgba(99, 102, 241, 0.14);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  padding: 1rem 1.1rem;
  box-shadow: 0 14px 36px rgba(47, 42, 120, 0.06);
}

.faq-item summary {
  display: flex;
  cursor: pointer;
  list-style: none;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 700;
}

.faq-item summary::-webkit-details-marker {
  display: none;
}

.faq-item summary svg {
  flex: 0 0 auto;
  color: var(--tn-primary);
  transition: transform 220ms ease;
}

.faq-item[open] summary svg {
  transform: rotate(90deg);
}

.faq-item p {
  margin-top: 0.8rem;
  color: #64748b;
  font-size: 0.94rem;
  line-height: 1.7;
}

.support-form {
  display: grid;
  gap: 1rem;
  padding: clamp(1rem, 3vw, 1.5rem);
}

.support-form label {
  display: grid;
  gap: 0.5rem;
}

.support-form label span {
  color: #334155;
  font-size: 0.86rem;
  font-weight: 700;
}

.support-form input,
.support-form textarea {
  width: 100%;
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  padding: 0.9rem 1rem;
  color: #0f172a;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.support-form input:focus,
.support-form textarea:focus {
  border-color: rgba(76, 51, 230, 0.72);
  box-shadow: 0 0 0 4px rgba(76, 51, 230, 0.1);
}

.support-form button,
.cookie-popup button {
  min-height: 48px;
  border-radius: 8px;
  background: linear-gradient(90deg, #5b35f5, #1d4fff);
  padding: 0 1.25rem;
  color: white;
  font-size: 0.94rem;
  font-weight: 800;
  box-shadow: 0 16px 34px rgba(59, 55, 238, 0.24);
}

.cookie-popup {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 60;
  display: flex;
  width: min(calc(100vw - 2rem), 520px);
  align-items: center;
  gap: 1rem;
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  padding: 1rem;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(18px);
}

.tn-reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 620ms ease, transform 620ms ease;
}

.tn-reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.hero-section .tn-reveal {
  opacity: 1;
  transform: none;
  transition: none;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes drawMini {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes liveLine {
  50% {
    transform: translateY(-4px);
  }
}

@keyframes dotPulse {
  0%,
  100% {
    opacity: 0.6;
    transform: scale(0.9);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

@keyframes heatPulse {
  0%,
  100% {
    transform: scale(0.92);
  }
  50% {
    transform: scale(1.08);
  }
}

@keyframes growBar {
  from {
    transform: scaleY(0);
  }
  to {
    transform: scaleY(1);
  }
}

@keyframes marquee {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

@media (max-width: 1023px) {
  .dashboard-window {
    min-height: auto;
  }

  .dashboard-sidebar {
    display: none;
  }
}

@media (max-width: 640px) {
  .landing-container {
    width: min(100% - 1rem, 1440px);
  }

  .section-band {
    padding-block: 3.5rem;
  }

  .dashboard-window {
    border-radius: 18px;
  }

  .metric-card,
  .dashboard-panel,
  .hero-mini-card,
  .feature-card,
  .case-card,
  .pricing-card,
  .support-form {
    padding: 1rem;
  }

  .feature-card {
    min-height: auto;
  }

  .pricing-card {
    min-height: 0;
  }

  .cookie-popup {
    left: 0.5rem;
    right: 0.5rem;
    bottom: 0.5rem;
    width: auto;
    flex-direction: column;
    align-items: stretch;
  }
}

@media (prefers-reduced-motion: reduce) {
  :global(html) {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }

  .tn-reveal {
    opacity: 1;
    transform: none;
  }
}
</style>
