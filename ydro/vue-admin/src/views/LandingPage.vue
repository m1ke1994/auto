<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ArrowRight,
  BarChart3,
  BellRing,
  Blocks,
  CheckCircle2,
  FileSearch,
  FileText,
  Flame,
  Funnel,
  Inbox,
  Menu,
  MousePointerClick,
  Route,
  SearchCheck,
  Smartphone,
  Sparkles,
  X,
  Zap,
} from '@lucide/vue'

const mobileMenuOpen = ref(false)
const activeSection = ref('features')
const activePricingDuration = ref('monthly')
const openFaq = ref(0)
const ecosystemStyle = ref({ '--cube-x': '0deg', '--cube-y': '0deg' })
let sectionObserver

const navItems = [
  { label: 'Возможности', href: '#features', id: 'features' },
  { label: 'Аналитика', href: '#ecosystem', id: 'ecosystem' },
  { label: 'SEO-анализ', href: '#seo-audit', id: 'seo-audit' },
]

const rightNavItems = [
  { label: 'Тарифы', href: '#pricing', id: 'pricing' },
  { label: 'FAQ', href: '#faq', id: 'faq' },
]

const heroBenefits = [
  ['Установка за 5 минут', Zap],
  ['Данные в реальном времени', Route],
  ['Без карты и ограничений', CheckCircle2],
  ['Российский сервер', Blocks],
]

const features = [
  { number: '01', title: 'Веб-аналитика', text: 'Посетители, источники трафика и ключевые события в одном отчёте.', icon: BarChart3, type: 'chart' },
  { number: '02', title: 'Карта кликов и скролла', text: 'Находите зоны внимания и точки, где аудитория теряет интерес.', icon: MousePointerClick, type: 'heatmap' },
  { number: '03', title: 'Конверсии и цели', text: 'Собирайте воронки и отслеживайте путь от просмотра до заявки.', icon: Funnel, type: 'funnel' },
  { number: '04', title: 'SEO-аудит', text: 'Проверяйте техническое SEO и получайте понятные рекомендации.', icon: SearchCheck, type: 'score' },
  { number: '05', title: 'Анализ конкурентов', text: 'Сравнивайте трафик, страницы и видимость с конкурентами.', icon: FileSearch, type: 'compare' },
  { number: '06', title: 'Уведомления', text: 'Получайте важные события и новые заявки без задержек.', icon: BellRing, type: 'alerts' },
  { number: '07', title: 'Отчёты и экспорт', text: 'Экспортируйте данные в PDF и CSV по расписанию.', icon: FileText, type: 'reports' },
  { number: '08', title: 'Устройства и технологии', text: 'Узнавайте, с каких устройств и браузеров приходит аудитория.', icon: Smartphone, type: 'devices' },
  { number: '09', title: 'AI-инсайты и рекомендации', text: 'Находите скрытые точки роста и получайте план действий.', icon: Sparkles, type: 'ai' },
]

const ecosystemItems = [
  { title: 'Аналитика', text: 'Вся динамика сайта в реальном времени', icon: BarChart3, position: 'p1' },
  { title: 'SEO-анализ', text: 'Ошибки и поисковые возможности', icon: SearchCheck, position: 'p2' },
  { title: 'Карта кликов', text: 'Визуальная карта внимания', icon: MousePointerClick, position: 'p3' },
  { title: 'Поведение', text: 'Путь каждого пользователя', icon: Route, position: 'p4' },
  { title: 'AI-инсайты', text: 'Рекомендации по росту', icon: Sparkles, position: 'p5' },
  { title: 'Воронки', text: 'Контроль этапов конверсии', icon: Funnel, position: 'p6' },
  { title: 'Уведомления', text: 'Важное — без задержек', icon: BellRing, position: 'p7' },
  { title: 'Производительность', text: 'Скорость и стабильность сайта', icon: Zap, position: 'p8' },
  { title: 'Конкуренты', text: 'Сравнение позиций и страниц', icon: FileSearch, position: 'p9' },
  { title: 'Конверсии', text: 'Цели, заявки и результат', icon: CheckCircle2, position: 'p10' },
]

const seoChecks = [
  ['Title и Description', 'ok'],
  ['Скорость загрузки', 'warn'],
  ['Мобильная адаптация', 'ok'],
  ['Индексация', 'ok'],
  ['Технические ошибки', 'error'],
  ['Дубли страниц', 'warn'],
  ['Изображения', 'ok'],
  ['Структура заголовков', 'ok'],
]

const pricingTabs = [
  { id: 'monthly', label: '1 месяц' },
  { id: 'halfYear', label: '6 месяцев', saving: '−5%' },
  { id: 'year', label: '12 месяцев', saving: '−10%' },
]

const pricingPlans = [
  { duration: 'monthly', title: 'Контент и хостинг', price: '1 299', period: '/ месяц', featured: false },
  { duration: 'monthly', title: 'Бизнес-аналитика', price: '1 999', period: '/ месяц', featured: true },
  { duration: 'halfYear', title: 'Контент и хостинг', price: '7 404', period: 'за 6 месяцев', featured: false },
  { duration: 'halfYear', title: 'Бизнес-аналитика', price: '11 394', period: 'за 6 месяцев', featured: true },
  { duration: 'year', title: 'Контент и хостинг', price: '14 029', period: 'за 12 месяцев', featured: false },
  { duration: 'year', title: 'Бизнес-аналитика', price: '21 589', period: 'за 12 месяцев', featured: true },
]

const visiblePlans = computed(() => pricingPlans.filter((plan) => plan.duration === activePricingDuration.value))

const planFeatures = {
  'Контент и хостинг': ['Хостинг сайта', 'Управление контентом', 'Резервное копирование', 'Техническая поддержка'],
  'Бизнес-аналитика': ['Веб-аналитика и цели', 'SEO-аудит и конкуренты', 'AI-рекомендации', 'Отчёты и уведомления'],
}

const faqItems = [
  ['Сколько занимает подключение TrackNode?', 'Обычно не больше пяти минут: добавьте сайт, установите короткий код и дождитесь первых событий.'],
  ['Нужна ли банковская карта для пробного периода?', 'Нет. Пробный период запускается без карты и автоматически не продлевается.'],
  ['Данные хранятся в России?', 'Да, инфраструктура TrackNode и основные данные размещены на российских серверах.'],
  ['Можно ли подключить несколько сайтов?', 'Да. В кабинете можно управлять несколькими проектами и переключаться между ними.'],
  ['TrackNode заменяет Яндекс Метрику?', 'TrackNode дополняет привычную аналитику SEO-аудитом, конкурентным анализом и единым планом действий.'],
]

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function handleEcosystemMove(event) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = event.currentTarget.getBoundingClientRect()
  const x = ((event.clientY - rect.top) / rect.height - 0.5) * -10
  const y = ((event.clientX - rect.left) / rect.width - 0.5) * 12
  ecosystemStyle.value = { '--cube-x': `${x}deg`, '--cube-y': `${y}deg` }
}

function resetEcosystem() {
  ecosystemStyle.value = { '--cube-x': '0deg', '--cube-y': '0deg' }
}

onMounted(() => {
  const sections = [...navItems, ...rightNavItems]
    .map((item) => document.getElementById(item.id))
    .filter(Boolean)

  sectionObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
      if (visible) activeSection.value = visible.target.id
    },
    { rootMargin: '-24% 0px -62% 0px', threshold: [0, 0.1, 0.3] },
  )

  sections.forEach((section) => sectionObserver.observe(section))
})

onUnmounted(() => sectionObserver?.disconnect())
</script>

<template>
  <div class="landing-page">
    <header class="landing-header">
      <nav class="nav-shell" aria-label="Основная навигация">
        <div class="nav-side nav-left">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="nav-link"
            :class="{ active: activeSection === item.id }"
          >{{ item.label }}</a>
        </div>

        <a class="brand" href="#top" aria-label="TrackNode — на главную">
          <span class="brand-kicker">Система</span>
          <span class="brand-line">
            <span class="brand-cube"><Zap :size="18" fill="currentColor" /></span>
            <span>Track<span>Node</span></span>
          </span>
        </a>

        <div class="nav-side nav-right">
          <a
            v-for="item in rightNavItems"
            :key="item.href"
            :href="item.href"
            class="nav-link"
            :class="{ active: activeSection === item.id }"
          >{{ item.label }}</a>
          <RouterLink class="login-button" to="/login">Войти в кабинет <ArrowRight :size="17" /></RouterLink>
        </div>

        <button
          class="menu-button"
          type="button"
          :aria-expanded="mobileMenuOpen"
          aria-controls="mobile-navigation"
          aria-label="Открыть меню"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <X v-if="mobileMenuOpen" :size="22" />
          <Menu v-else :size="22" />
        </button>
      </nav>

      <div v-if="mobileMenuOpen" id="mobile-navigation" class="mobile-menu">
        <a v-for="item in [...navItems, ...rightNavItems]" :key="item.href" :href="item.href" @click="closeMobileMenu">
          {{ item.label }}
        </a>
        <RouterLink to="/login" class="login-button" @click="closeMobileMenu">Войти в кабинет <ArrowRight :size="17" /></RouterLink>
      </div>
    </header>

    <main id="top">
      <section class="hero-section" aria-labelledby="hero-title">
        <div class="ambient ambient-one"></div>
        <div class="ambient ambient-two"></div>
        <div class="landing-container hero-grid">
          <div class="hero-copy">
            <p class="eyebrow"><BarChart3 :size="15" /> Аналитика для роста бизнеса</p>
            <h1 id="hero-title">Понимайте аудиторию.<br />Принимайте решения.<br /><span>Растите быстрее.</span></h1>
            <p class="hero-lead">
              TrackNode собирает данные о посетителях, источниках трафика и действиях на сайте.
              Превращает цифры в понятные инсайты, которые помогают увеличивать конверсию и прибыль.
            </p>
            <div class="hero-actions">
              <RouterLink class="primary-button" to="/register">Попробовать бесплатно 3 дня <Zap :size="18" /></RouterLink>
              <a class="secondary-button" href="#ecosystem"><span class="play">▶</span> Посмотреть демо</a>
            </div>
            <div class="hero-benefits">
              <div v-for="([label, icon]) in heroBenefits" :key="label" class="hero-benefit">
                <span><component :is="icon" :size="16" /></span>
                {{ label }}
              </div>
            </div>
          </div>

          <div class="hero-visual" aria-label="Визуализация аналитики TrackNode">
            <div class="hero-orbit orbit-a"></div>
            <div class="hero-orbit orbit-b"></div>
            <div class="cube-stage"></div>
            <div class="hero-cube" role="img" aria-label="Светящийся куб TrackNode"></div>
            <article class="float-card visitors-card">
              <small>Посетители</small><strong>24 780 <em>+12.3%</em></strong>
              <svg viewBox="0 0 190 45" aria-hidden="true"><path d="M2 36 24 26 45 34 66 18 88 29 110 17 134 30 160 20 188 6" /></svg>
            </article>
            <article class="float-card conversion-card">
              <small>Конверсия</small><strong>2.47% <em>+8.3%</em></strong>
              <div class="donut"></div>
            </article>
            <article class="float-card heat-card">
              <small>Тепловая карта</small>
              <div class="mini-heat"><i></i><i></i><i></i><i></i></div>
            </article>
            <article class="float-card traffic-card">
              <small>Источники трафика</small>
              <span><i style="width: 84%"></i></span><span><i style="width: 61%"></i></span><span><i style="width: 42%"></i></span>
            </article>
          </div>
        </div>
        <div class="landing-container metrics-strip">
          <div><BarChart3 :size="20" /><span><strong>24 780</strong><small>Посетителей <em>+12.3%</em></small></span></div>
          <div><Route :size="20" /><span><strong>71 842</strong><small>Просмотра <em>+8.1%</em></small></span></div>
          <div><Inbox :size="20" /><span><strong>342</strong><small>Заявки <em>+15.7%</em></small></span></div>
          <div><Funnel :size="20" /><span><strong>2.47%</strong><small>Конверсия <em>+8.3%</em></small></span></div>
        </div>
      </section>

      <section id="features" class="section features-section" aria-labelledby="features-title">
        <div class="landing-container">
          <div class="features-heading">
            <div>
              <p class="eyebrow"><Zap :size="15" /> Всё для роста вашего бизнеса</p>
              <h2 id="features-title">Возможности,<br />которые <span>дают результат</span></h2>
              <p>TrackNode объединяет ключевые инструменты для анализа, оптимизации и роста сайта в одном сервисе.</p>
            </div>
            <div class="feature-promises">
              <div><CheckCircle2 :size="22" /><span><strong>Точные данные</strong><small>Без искажений</small></span></div>
              <div><Zap :size="22" /><span><strong>Реальное время</strong><small>Метрики онлайн</small></span></div>
              <div><Sparkles :size="22" /><span><strong>Практические инсайты</strong><small>Понятный план роста</small></span></div>
            </div>
          </div>

          <div class="features-grid">
            <article v-for="feature in features" :key="feature.number" class="feature-card" :class="`visual-${feature.type}`">
              <div class="feature-copy">
                <div class="feature-number">{{ feature.number }}</div>
                <component :is="feature.icon" :size="23" class="feature-icon" />
                <h3>{{ feature.title }}</h3>
                <p>{{ feature.text }}</p>
              </div>
              <div class="feature-mini" aria-hidden="true">
                <template v-if="feature.type === 'chart'">
                  <strong>24 780 <em>+12.3%</em></strong><svg viewBox="0 0 160 60"><path d="M2 48 24 35 46 44 70 25 92 39 115 18 138 31 158 10" /></svg>
                </template>
                <template v-else-if="feature.type === 'heatmap'">
                  <div class="feature-heat"><i></i><i></i><i></i><i></i><i></i></div>
                </template>
                <template v-else-if="feature.type === 'funnel'">
                  <i class="funnel-layer"></i><i class="funnel-layer"></i><i class="funnel-layer"></i><i class="funnel-layer"></i>
                </template>
                <template v-else-if="feature.type === 'score'">
                  <div class="score-ring"><strong>87</strong><small>/100</small></div>
                </template>
                <template v-else-if="feature.type === 'compare'">
                  <span v-for="width in [92, 74, 58, 41]" :key="width"><i :style="{ width: `${width}%` }"></i></span>
                </template>
                <template v-else-if="feature.type === 'alerts'">
                  <p v-for="(label, index) in ['Новая заявка', 'Цель достигнута', 'Ошибка на сайте']" :key="label"><i :class="`alert-${index}`"></i>{{ label }}</p>
                </template>
                <template v-else-if="feature.type === 'reports'">
                  <span class="report-file">PDF</span><span class="report-file green">CSV</span>
                </template>
                <template v-else-if="feature.type === 'devices'">
                  <div class="device-donut"></div><p>Desktop 55%<br />Mobile 35%<br />Tablet 10%</p>
                </template>
                <template v-else>
                  <strong class="ai-growth">+23%</strong><svg viewBox="0 0 160 60"><path d="M2 52 28 42 51 48 78 20 101 36 128 8 158 17" /></svg>
                </template>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section id="ecosystem" class="section ecosystem-section" aria-labelledby="ecosystem-title">
        <div class="landing-container">
          <div class="section-heading centered">
            <p class="eyebrow"><Blocks :size="15" /> Экосистема TrackNode</p>
            <h2 id="ecosystem-title">Вся сила аналитики в <span>единой экосистеме</span></h2>
            <p>Все инструменты TrackNode работают вместе, чтобы данные превращались в понятные решения для роста.</p>
          </div>

          <div
            class="ecosystem-canvas"
            :style="ecosystemStyle"
            @pointermove="handleEcosystemMove"
            @pointerleave="resetEcosystem"
          >
            <div class="orbit-line orbit-line-1"></div>
            <div class="orbit-line orbit-line-2"></div>
            <div class="orbit-line orbit-line-3"></div>
            <div class="orbit-glow"></div>
            <div class="ecosystem-cube-wrap" role="img" aria-label="Куб — центр экосистемы TrackNode"></div>
            <article v-for="item in ecosystemItems" :key="item.title" class="ecosystem-node" :class="item.position" tabindex="0">
              <component :is="item.icon" :size="24" />
              <strong>{{ item.title }}</strong>
              <span>{{ item.text }}</span>
            </article>
          </div>

          <div class="ecosystem-mobile-grid">
            <article v-for="item in ecosystemItems" :key="`mobile-${item.title}`">
              <component :is="item.icon" :size="22" /><span><strong>{{ item.title }}</strong><small>{{ item.text }}</small></span>
            </article>
          </div>
        </div>
      </section>

      <section id="seo-audit" class="section seo-section" aria-labelledby="seo-title">
        <div class="landing-container seo-grid">
          <div class="seo-copy">
            <p class="eyebrow"><SearchCheck :size="15" /> SEO-анализ</p>
            <h2 id="seo-title">SEO-анализ, который показывает, <span>что мешает сайту расти</span></h2>
            <p>TrackNode сканирует сайт, расставляет приоритеты и объясняет, что исправить в первую очередь — без сложных таблиц и технического шума.</p>
            <div class="seo-summary">
              <div><strong>12</strong><small>ошибок</small></div>
              <div><strong>8</strong><small>предупреждений</small></div>
              <div><strong>34</strong><small>проверки пройдено</small></div>
            </div>
            <RouterLink class="primary-button" to="/register">Проверить свой сайт <ArrowRight :size="18" /></RouterLink>
          </div>

          <div class="seo-dashboard">
            <div class="browser-bar"><i></i><i></i><i></i><span>your-site.ru</span><SearchCheck :size="17" /></div>
            <div class="seo-dashboard-body">
              <div class="health-card">
                <div class="health-ring"><span><strong>87</strong><small>/100</small></span></div>
                <div><small>SEO Health</small><strong>Хороший результат</strong><p>Сайт готов к росту. Осталось исправить несколько важных пунктов.</p></div>
              </div>
              <div class="seo-checks">
                <div v-for="([label, status]) in seoChecks" :key="label" :class="`status-${status}`">
                  <span><CheckCircle2 v-if="status === 'ok'" :size="17" /><Zap v-else-if="status === 'warn'" :size="17" /><X v-else :size="17" /></span>
                  <strong>{{ label }}</strong><small>{{ status === 'ok' ? 'Пройдено' : status === 'warn' ? 'Проверить' : 'Исправить' }}</small>
                </div>
              </div>
              <div class="ai-recommendation">
                <span><Sparkles :size="22" /></span>
                <div><small>AI-рекомендация</small><strong>Сожмите изображения на 4 страницах</strong><p>Это ускорит загрузку на мобильных устройствах примерно на 1,2 секунды.</p></div>
                <ArrowRight :size="20" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" class="section pricing-section" aria-labelledby="pricing-title">
        <div class="landing-container">
          <div class="section-heading centered">
            <p class="eyebrow"><Zap :size="15" /> Простые тарифы</p>
            <h2 id="pricing-title">Выберите формат <span>для вашего роста</span></h2>
            <p>Начните с трёх бесплатных дней. Карта не нужна.</p>
          </div>
          <div class="pricing-tabs" role="tablist" aria-label="Период оплаты">
            <button v-for="tab in pricingTabs" :key="tab.id" type="button" :class="{ active: activePricingDuration === tab.id }" @click="activePricingDuration = tab.id">
              {{ tab.label }} <small v-if="tab.saving">{{ tab.saving }}</small>
            </button>
          </div>
          <div class="pricing-grid">
            <article v-for="plan in visiblePlans" :key="`${plan.duration}-${plan.title}`" class="pricing-card" :class="{ featured: plan.featured }">
              <span v-if="plan.featured" class="popular">Популярный</span>
              <p class="pricing-label">{{ plan.title }}</p>
              <div class="price"><strong>{{ plan.price }} ₽</strong><small>{{ plan.period }}</small></div>
              <p>{{ plan.featured ? 'Полный набор инструментов для роста сайта и бизнеса.' : 'Надёжная техническая основа для вашего сайта.' }}</p>
              <ul><li v-for="item in planFeatures[plan.title]" :key="item"><CheckCircle2 :size="18" />{{ item }}</li></ul>
              <RouterLink :class="plan.featured ? 'primary-button' : 'secondary-button'" to="/register">Попробовать бесплатно <ArrowRight :size="17" /></RouterLink>
            </article>
          </div>
        </div>
      </section>

      <section id="faq" class="section faq-section" aria-labelledby="faq-title">
        <div class="landing-container faq-layout">
          <div class="faq-heading"><p class="eyebrow">FAQ</p><h2 id="faq-title">Ответы на частые вопросы</h2><p>Не нашли ответ? Напишите нам — поможем разобраться.</p></div>
          <div class="faq-list">
            <article v-for="([question, answer], index) in faqItems" :key="question" :class="{ open: openFaq === index }">
              <button type="button" :aria-expanded="openFaq === index" @click="openFaq = openFaq === index ? -1 : index"><span>{{ question }}</span><span>+</span></button>
              <div v-show="openFaq === index"><p>{{ answer }}</p></div>
            </article>
          </div>
        </div>
      </section>

      <section class="final-cta">
        <div class="landing-container final-cta-inner">
          <div><p>Один сервис — вся аналитика</p><h2>Начните принимать решения на основе данных</h2></div>
          <RouterLink class="cta-white" to="/register">Попробовать бесплатно 3 дня <ArrowRight :size="18" /></RouterLink>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <div class="landing-container footer-grid">
        <a class="footer-brand" href="#top"><span><Zap :size="18" fill="currentColor" /></span>TrackNode</a>
        <p>Аналитика, SEO и инсайты для роста сайта в одном сервисе.</p>
        <div><a href="#features">Возможности</a><a href="#pricing">Тарифы</a><a href="#faq">FAQ</a><RouterLink to="/login">Войти</RouterLink></div>
        <small>© {{ new Date().getFullYear() }} TrackNode</small>
      </div>
    </footer>
  </div>
</template>

<style scoped>
:global(html) { scroll-behavior: smooth; scroll-padding-top: 118px; }
:global(body) { background: #fdfdff; }

.landing-page {
  --ink: #11152d;
  --muted: #626985;
  --purple: #4b2cff;
  --violet: #7856ff;
  --line: rgba(92, 67, 255, 0.12);
  min-height: 100vh;
  overflow: clip;
  color: var(--ink);
  background: #fdfdff;
}

.landing-container { width: min(100% - 40px, 1440px); margin-inline: auto; }
.section { position: relative; padding: 112px 0; scroll-margin-top: 112px; }
.section h2 { margin: 14px 0 18px; font-size: clamp(2.2rem, 4vw, 4rem); line-height: 1.04; letter-spacing: -0.05em; }
.section h2 span { color: var(--purple); }
.section-heading { max-width: 900px; margin-bottom: 56px; }
.section-heading.centered { margin-inline: auto; text-align: center; }
.section-heading.centered .eyebrow { margin-inline: auto; }
.section-heading > p:last-child { max-width: 720px; margin: 0 auto; color: var(--muted); font-size: 1.08rem; line-height: 1.75; }
.eyebrow { display: inline-flex; align-items: center; gap: 7px; width: max-content; margin: 0; padding: 8px 13px; border: 1px solid rgba(89, 56, 255, 0.11); border-radius: 999px; color: var(--purple); background: rgba(255, 255, 255, 0.72); box-shadow: 0 8px 28px rgba(70, 38, 220, 0.08); font-size: .74rem; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; }

.landing-header { position: fixed; z-index: 100; top: max(14px, env(safe-area-inset-top)); left: 50%; width: min(calc(100% - 32px), 1480px); transform: translateX(-50%); }
.nav-shell { position: relative; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; min-height: 88px; padding: 10px 16px 10px 24px; border: 1px solid rgba(255,255,255,.84); border-radius: 25px; background: rgba(255,255,255,.74); box-shadow: 0 18px 60px rgba(70,51,165,.13), inset 0 0 0 1px rgba(84,57,255,.05); backdrop-filter: blur(24px) saturate(150%); }
.nav-side { display: flex; align-items: center; gap: clamp(14px, 2vw, 34px); }
.nav-right { justify-content: flex-end; }
.nav-link { position: relative; padding: 13px 2px; color: #282a3c; font-size: .88rem; font-weight: 700; text-decoration: none; white-space: nowrap; }
.nav-link::after { position: absolute; right: 0; bottom: 6px; left: 0; height: 2px; border-radius: 99px; background: var(--purple); content: ''; opacity: 0; transform: scaleX(.3); transition: .25s ease; }
.nav-link:hover, .nav-link.active { color: var(--purple); }
.nav-link.active::after { opacity: 1; transform: scaleX(1); }
.brand { display: grid; min-width: 210px; padding: 0 24px; color: var(--ink); text-align: left; text-decoration: none; }
.brand-kicker { margin-left: 49px; color: #777c91; font-size: .68rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
.brand-line { display: flex; align-items: center; gap: 10px; font-size: 1.78rem; font-weight: 900; letter-spacing: -.055em; }
.brand-line > span:last-child > span { color: var(--purple); }
.brand-cube, .footer-brand span { display: grid; width: 39px; height: 39px; place-items: center; border-radius: 11px; color: white; background: linear-gradient(145deg, #7b5cff, #3115ed); box-shadow: 0 9px 22px rgba(69,37,241,.35), inset 0 1px 2px rgba(255,255,255,.6); transform: rotate(-3deg); }
.login-button, .primary-button, .secondary-button, .cta-white { display: inline-flex; min-height: 50px; align-items: center; justify-content: center; gap: 9px; border-radius: 14px; padding: 0 21px; font-weight: 800; text-decoration: none; transition: .25s ease; }
.login-button, .primary-button { color: white; background: linear-gradient(135deg, #5c38ff, #3518ee); box-shadow: 0 12px 26px rgba(66,37,238,.28), inset 0 1px 1px rgba(255,255,255,.25); }
.login-button { min-height: 48px; padding-inline: 19px; font-size: .85rem; }
.login-button:hover, .primary-button:hover { transform: translateY(-2px); box-shadow: 0 17px 34px rgba(66,37,238,.36); }
.menu-button { display: none; width: 46px; height: 46px; place-items: center; border: 1px solid var(--line); border-radius: 14px; color: var(--purple); background: white; }
.mobile-menu { display: none; }

.hero-section { position: relative; min-height: 900px; padding: 188px 0 56px; background: radial-gradient(circle at 70% 42%, rgba(114,73,255,.17), transparent 28%), radial-gradient(circle at 10% 12%, rgba(114,73,255,.09), transparent 26%), linear-gradient(180deg, #fff 0%, #faf9ff 72%, #fff 100%); }
.ambient { position: absolute; border-radius: 50%; filter: blur(3px); pointer-events: none; }
.ambient-one { top: 100px; right: -180px; width: 620px; height: 620px; background: radial-gradient(circle, rgba(85,47,255,.12), transparent 66%); }
.ambient-two { bottom: 80px; left: -240px; width: 520px; height: 520px; background: radial-gradient(circle, rgba(153,116,255,.1), transparent 65%); }
.hero-grid { position: relative; z-index: 1; display: grid; grid-template-columns: .88fr 1.12fr; align-items: center; gap: 30px; min-height: 590px; }
.hero-copy { position: relative; z-index: 5; padding-left: 12px; }
.hero-copy h1 { margin: 28px 0 22px; font-size: clamp(3.1rem, 5.25vw, 5.3rem); line-height: 1.01; letter-spacing: -.064em; }
.hero-copy h1 span { color: var(--purple); }
.hero-lead { max-width: 690px; color: var(--muted); font-size: 1.08rem; line-height: 1.8; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 32px; }
.primary-button { min-height: 56px; padding-inline: 26px; }
.secondary-button { min-height: 56px; border: 1px solid var(--line); color: var(--purple); background: rgba(255,255,255,.8); box-shadow: 0 10px 30px rgba(58,34,150,.08); }
.secondary-button:hover { transform: translateY(-2px); border-color: rgba(75,44,255,.3); }
.play { display: grid; width: 29px; height: 29px; place-items: center; border-radius: 50%; color: white; background: var(--purple); font-size: .65rem; }
.hero-benefits { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px 18px; max-width: 620px; margin-top: 34px; }
.hero-benefit { display: flex; align-items: center; gap: 9px; color: #545b77; font-size: .8rem; font-weight: 650; }
.hero-benefit > span { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; border: 1px solid var(--line); border-radius: 50%; color: var(--purple); background: white; box-shadow: 0 7px 19px rgba(70,42,180,.08); }
.hero-visual { position: relative; min-height: 600px; perspective: 1000px; }
.hero-cube { position: absolute; z-index: 2; top: 50%; left: 50%; width: min(520px, 68%); aspect-ratio: 1; border-radius: 50%; background-image: url('/images/landing/ecosystem-reference.png'); background-repeat: no-repeat; background-position: 50% 69%; background-size: 1850px auto; filter: saturate(1.06) drop-shadow(0 30px 28px rgba(71,38,230,.16)); transform: translate(-48%,-49%); animation: heroCubeFloat 6s ease-in-out infinite; }
.cube-stage { position: absolute; z-index: 1; left: 50%; bottom: 70px; width: 370px; height: 120px; border: 2px solid rgba(90,56,255,.28); border-radius: 50%; background: radial-gradient(ellipse, rgba(87,51,255,.38), rgba(255,255,255,.3) 46%, transparent 72%); box-shadow: 0 20px 55px rgba(67,36,227,.22), inset 0 0 25px white; transform: translateX(-50%); }
.hero-orbit { position: absolute; top: 50%; left: 50%; border: 1px solid rgba(93,62,255,.17); border-radius: 50%; transform: translate(-50%,-50%) rotate(-10deg); }
.orbit-a { width: 96%; height: 49%; }
.orbit-b { width: 78%; height: 38%; transform: translate(-50%,-50%) rotate(18deg); }
.float-card { position: absolute; z-index: 4; min-width: 180px; padding: 16px 18px; border: 1px solid rgba(255,255,255,.9); border-radius: 18px; background: rgba(255,255,255,.72); box-shadow: 0 18px 50px rgba(63,43,145,.13), inset 0 0 0 1px rgba(84,58,255,.06); backdrop-filter: blur(15px); animation: cardFloat 5s ease-in-out infinite; }
.float-card small { display: block; margin-bottom: 9px; color: #666c84; font-weight: 700; }
.float-card strong { font-size: 1.25rem; }
.float-card em, .metrics-strip em, .feature-mini em { color: #0cab79; font-size: .66rem; font-style: normal; }
.visitors-card { top: 40px; left: 6%; }
.visitors-card svg, .feature-mini svg { display: block; width: 100%; margin-top: 8px; fill: none; stroke: #5535ff; stroke-width: 3; }
.conversion-card { bottom: 120px; left: 2%; animation-delay: -2s; }
.donut { width: 54px; height: 54px; margin-top: 9px; border-radius: 50%; background: conic-gradient(var(--purple) 0 72%, #e7e4ff 72%); -webkit-mask: radial-gradient(circle, transparent 45%, #000 47%); mask: radial-gradient(circle, transparent 45%, #000 47%); }
.heat-card { top: 70px; right: 0; width: 218px; animation-delay: -1.2s; }
.mini-heat, .feature-heat { position: relative; height: 82px; overflow: hidden; border-radius: 11px; background: linear-gradient(135deg, #e6e4ff, #eff8ff); }
.mini-heat i, .feature-heat i { position: absolute; width: 32px; height: 32px; border-radius: 50%; background: #ffdf36; filter: blur(8px); }
.mini-heat i:nth-child(1), .feature-heat i:nth-child(1) { top: 32%; left: 44%; background: #ff432f; }
.mini-heat i:nth-child(2), .feature-heat i:nth-child(2) { top: 10%; left: 20%; background: #5ce070; }
.mini-heat i:nth-child(3), .feature-heat i:nth-child(3) { right: 13%; bottom: 5%; }
.mini-heat i:nth-child(4), .feature-heat i:nth-child(4) { bottom: 4%; left: 32%; background: #72de77; }
.traffic-card { right: 4%; bottom: 72px; width: 210px; animation-delay: -3.1s; }
.traffic-card > span, .visual-compare .feature-mini > span { display: block; height: 7px; margin: 9px 0; overflow: hidden; border-radius: 99px; background: #e9e7fa; }
.traffic-card i, .visual-compare .feature-mini i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #826aff, #4b2cff); }
.metrics-strip { position: relative; z-index: 6; display: grid; grid-template-columns: repeat(4,1fr); margin-top: 16px; padding: 24px 8px; border-top: 1px solid var(--line); }
.metrics-strip > div { display: flex; align-items: center; gap: 15px; padding: 4px 26px; border-right: 1px solid var(--line); color: var(--purple); }
.metrics-strip > div:last-child { border: 0; }
.metrics-strip span, .metrics-strip strong, .metrics-strip small { display: block; }
.metrics-strip strong { color: var(--ink); font-size: 1.5rem; }
.metrics-strip small { margin-top: 3px; color: #5e657d; }

.features-section { background: linear-gradient(180deg,#fff,#fbfaff); }
.features-heading { display: grid; grid-template-columns: .9fr 1.1fr; align-items: end; gap: 60px; margin-bottom: 46px; }
.features-heading h2 { font-size: clamp(2.45rem, 4vw, 4.1rem); }
.features-heading > div:first-child > p:last-child { max-width: 570px; color: var(--muted); line-height: 1.75; }
.feature-promises { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; padding-bottom: 12px; }
.feature-promises > div { display: flex; gap: 12px; min-height: 76px; padding: 14px; border-left: 1px solid var(--line); color: var(--purple); }
.feature-promises strong, .feature-promises small { display: block; }
.feature-promises strong { color: var(--ink); font-size: .83rem; }
.feature-promises small { margin-top: 7px; color: var(--muted); font-size: .72rem; }
.features-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 15px; }
.feature-card { display: grid; grid-template-columns: minmax(0,1fr) minmax(130px,.78fr); min-height: 230px; padding: 24px; overflow: hidden; border: 1px solid rgba(89,58,225,.11); border-radius: 20px; background: rgba(255,255,255,.76); box-shadow: 0 12px 34px rgba(66,43,145,.065); transition: .3s ease; }
.feature-card:hover { z-index: 2; border-color: rgba(75,44,255,.25); box-shadow: 0 24px 55px rgba(66,43,145,.14); transform: translateY(-6px); }
.feature-copy { position: relative; z-index: 2; }
.feature-number { display: inline-grid; width: 38px; height: 38px; margin-right: 8px; place-items: center; border-radius: 11px; color: #765cff; background: #f0edff; font-weight: 850; }
.feature-icon { display: inline; color: var(--purple); vertical-align: middle; }
.feature-card h3 { margin: 28px 0 9px; font-size: 1.08rem; }
.feature-card p { margin: 0; color: var(--muted); font-size: .78rem; line-height: 1.65; }
.feature-mini { align-self: center; min-width: 0; margin-left: 13px; }
.feature-mini > strong { display: block; font-size: 1.15rem; }
.feature-heat { height: 112px; }
.feature-heat i:nth-child(5) { top: 18%; right: 9%; background: #55d886; }
.visual-funnel .feature-mini { display: grid; justify-items: center; gap: 5px; }
.funnel-layer { display: block; height: 22px; clip-path: polygon(10% 0,90% 0,72% 100%,28% 100%); background: linear-gradient(90deg,#bfb4ff,#5436fa); }
.funnel-layer:nth-child(1) { width: 125px; }.funnel-layer:nth-child(2){width:100px}.funnel-layer:nth-child(3){width:75px}.funnel-layer:nth-child(4){width:48px}
.score-ring, .device-donut { display: grid; width: 92px; height: 92px; margin: auto; place-items: center; border-radius: 50%; background: conic-gradient(#23c48a 0 87%,#eceafb 87%); -webkit-mask: radial-gradient(circle,transparent 54%,#000 56%); mask: radial-gradient(circle,transparent 54%,#000 56%); }
.score-ring strong { font-size: 1.35rem; }
.score-ring small { font-size: .62rem; }
.visual-compare .feature-mini > span { height: 10px; }
.visual-alerts .feature-mini p { display: flex; align-items: center; gap: 7px; margin: 7px 0; padding: 8px; border-radius: 9px; background: #f8f7ff; color: #4a5068; font-size: .65rem; }
.visual-alerts .feature-mini p i { width: 8px; height: 8px; border-radius: 50%; background: #18bf8a; }.visual-alerts .feature-mini p i.alert-1{background:#f3ad26}.visual-alerts .feature-mini p i.alert-2{background:#ef5b65}
.visual-reports .feature-mini { display: flex; gap: 8px; }.report-file { display: grid; width: 58px; height: 70px; place-items: center; border-radius: 10px; color: #e94d5c; background: #fff0f1; font-size: .72rem; font-weight: 900; }.report-file.green{color:#12ad7f;background:#e9fbf5}
.visual-devices .feature-mini { display: flex; align-items: center; gap: 10px; }.device-donut{width:75px;height:75px;flex:0 0 auto;background:conic-gradient(#4b2cff 0 55%,#3295ff 55% 90%,#20c7ad 90%)}.visual-devices .feature-mini p{font-size:.62rem;line-height:1.9}
.visual-ai .feature-mini { padding: 14px; border-radius: 14px; color: white; background: linear-gradient(145deg,#22116b,#5229d9); }.visual-ai .feature-mini .ai-growth{color:#30deb2;font-size:1.6rem}.visual-ai .feature-mini svg{stroke:#9f8cff}

.ecosystem-section { min-height: 980px; background: radial-gradient(circle at 50% 55%,rgba(101,61,255,.17),transparent 30%), linear-gradient(180deg,#fbfaff,#f7f5ff 62%,#fff); }
.ecosystem-canvas { position: relative; height: 660px; max-width: 1340px; margin: 0 auto; perspective: 1200px; }
.orbit-line { position: absolute; top: 50%; left: 50%; border: 1px solid rgba(93,62,255,.19); border-radius: 50%; box-shadow: 0 0 14px rgba(87,50,255,.07); transform: translate(-50%,-50%) rotate(-7deg); }
.orbit-line::after { position: absolute; top: 50%; left: -5px; width: 10px; height: 10px; border-radius: 50%; background: white; box-shadow: 0 0 14px 5px #9a85ff; content: ''; }
.orbit-line-1 { width: 52%; height: 37%; animation: orbitSpin 18s linear infinite; }.orbit-line-2{width:76%;height:57%;transform:translate(-50%,-50%) rotate(7deg);animation:orbitSpinReverse 27s linear infinite}.orbit-line-3{width:96%;height:78%;transform:translate(-50%,-50%) rotate(-4deg);animation:orbitSpin 36s linear infinite}
.orbit-glow { position: absolute; top: 50%; left: 50%; width: 470px; height: 170px; border: 2px solid rgba(95,61,255,.25); border-radius: 50%; background: radial-gradient(ellipse,rgba(99,58,255,.25),transparent 68%); box-shadow: 0 20px 55px rgba(75,39,239,.2),inset 0 0 30px white; transform: translate(-50%,55%); }
.ecosystem-cube-wrap { position: absolute; z-index: 3; top: 50%; left: 50%; width: 330px; height: 330px; border-radius: 50%; background-image: url('/images/landing/ecosystem-reference.png'); background-repeat: no-repeat; background-position: 50% 69%; background-size: 1536px auto; filter: saturate(1.08) drop-shadow(0 23px 28px rgba(71,38,230,.18)); transform: translate(-50%,-55%) rotateX(var(--cube-x)) rotateY(var(--cube-y)); transition: transform .18s ease-out; animation: cubeFloat 6s ease-in-out infinite; }
.ecosystem-node { position: absolute; z-index: 5; display: grid; width: 136px; min-height: 116px; place-items: center; padding: 13px; border: 1px solid rgba(255,255,255,.92); border-radius: 18px; color: var(--purple); text-align: center; background: rgba(255,255,255,.73); box-shadow: 0 15px 43px rgba(61,43,132,.12),inset 0 0 0 1px rgba(83,56,230,.06); backdrop-filter: blur(14px); transition: .3s ease; animation: nodeFloat 5s ease-in-out infinite; }
.ecosystem-node strong { color: var(--ink); font-size: .78rem; }
.ecosystem-node span { position: absolute; top: calc(100% - 10px); left: 50%; width: 175px; padding: 9px 11px; border-radius: 9px; color: white; background: #21175b; font-size: .66rem; opacity: 0; pointer-events: none; transform: translate(-50%,8px); transition: .25s ease; }
.ecosystem-node:hover, .ecosystem-node:focus { z-index: 8; border-color: rgba(91,56,255,.3); box-shadow: 0 20px 52px rgba(61,43,132,.2),0 0 30px rgba(99,64,255,.15); transform: translateY(-6px) scale(1.03); outline: none; }
.ecosystem-node:hover span, .ecosystem-node:focus span { opacity: 1; transform: translate(-50%,0); }
.p1{top:2%;left:45%}.p2{top:10%;right:17%}.p3{top:34%;right:4%}.p4{right:15%;bottom:8%}.p5{right:36%;bottom:0}.p6{bottom:2%;left:31%}.p7{bottom:10%;left:9%}.p8{top:36%;left:0}.p9{top:10%;left:14%}.p10{top:29%;left:25%}
.p2,.p7{animation-delay:-1s}.p3,.p8{animation-delay:-2s}.p4,.p9{animation-delay:-3s}.p5,.p10{animation-delay:-4s}
.ecosystem-mobile-grid { display: none; }

.seo-section { background: #fff; }
.seo-grid { display: grid; grid-template-columns: .74fr 1.26fr; align-items: center; gap: 70px; }
.seo-copy > p:not(.eyebrow) { max-width: 580px; color: var(--muted); line-height: 1.78; }
.seo-summary { display: grid; grid-template-columns: repeat(3,1fr); max-width: 530px; margin: 32px 0; border: 1px solid var(--line); border-radius: 16px; background: #fbfaff; }
.seo-summary > div { padding: 16px 18px; border-right: 1px solid var(--line); }.seo-summary > div:last-child{border:0}
.seo-summary strong,.seo-summary small { display:block }.seo-summary strong{font-size:1.45rem}.seo-summary small{margin-top:4px;color:var(--muted);font-size:.68rem}
.seo-dashboard { overflow: hidden; border: 1px solid rgba(83,52,222,.13); border-radius: 25px; background: rgba(255,255,255,.9); box-shadow: 0 35px 80px rgba(61,43,132,.14); }
.browser-bar { display: flex; align-items: center; gap: 7px; height: 53px; padding: 0 17px; border-bottom: 1px solid var(--line); background: #f7f6fd; color: var(--purple); }.browser-bar i{width:8px;height:8px;border-radius:50%;background:#ff777f}.browser-bar i:nth-child(2){background:#f7bd43}.browser-bar i:nth-child(3){background:#3bd28f}.browser-bar span{flex:1;margin-left:10px;padding:7px 12px;border-radius:8px;color:#73788e;background:#fff;font-size:.68rem}
.seo-dashboard-body { padding: 22px; background: linear-gradient(145deg,#fff,#faf9ff); }
.health-card { display: grid; grid-template-columns: 135px 1fr; align-items:center;gap:18px;padding:18px;border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:0 10px 25px rgba(61,43,132,.06)}
.health-ring { display:grid;width:120px;height:120px;place-items:center;border-radius:50%;background:conic-gradient(#4b2cff 0 87%,#e9e7fa 87%);position:relative}.health-ring::after{position:absolute;inset:12px;border-radius:50%;background:#fff;content:''}.health-ring span{position:relative;z-index:2;text-align:center}.health-ring strong,.health-ring small{display:block}.health-ring strong{font-size:2rem}.health-card > div:last-child > small{color:var(--purple);font-weight:800;text-transform:uppercase}.health-card > div:last-child > strong{display:block;margin-top:5px;font-size:1.1rem}.health-card p{margin:7px 0 0;color:var(--muted);font-size:.73rem;line-height:1.55}
.seo-checks { display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:12px 0}.seo-checks > div{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:9px;padding:10px;border:1px solid var(--line);border-radius:11px;background:#fff}.seo-checks > div > span{display:grid;width:29px;height:29px;place-items:center;border-radius:8px}.seo-checks strong{font-size:.7rem}.seo-checks small{font-size:.6rem}.status-ok > span,.status-ok small{color:#0da777;background:#e8fbf4}.status-warn > span,.status-warn small{color:#c78109;background:#fff6dd}.status-error > span,.status-error small{color:#dc4755;background:#fff0f1}.seo-checks small{padding:4px 6px;border-radius:6px;background:transparent}
.ai-recommendation { display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:13px;padding:15px;border-radius:15px;color:white;background:linear-gradient(130deg,#271174,#5a31e8);box-shadow:0 14px 28px rgba(63,31,199,.22)}.ai-recommendation > span{display:grid;width:42px;height:42px;place-items:center;border-radius:12px;background:rgba(255,255,255,.14)}.ai-recommendation small,.ai-recommendation strong{display:block}.ai-recommendation small{color:#c9bdff;font-size:.6rem;text-transform:uppercase}.ai-recommendation strong{margin-top:3px;font-size:.8rem}.ai-recommendation p{margin:4px 0 0;color:#ded8ff;font-size:.63rem}

.pricing-section { background: linear-gradient(180deg,#faf9ff,#fff); }
.pricing-tabs { display:flex;width:max-content;max-width:100%;margin:-20px auto 38px;padding:5px;border:1px solid var(--line);border-radius:15px;background:white;box-shadow:0 10px 30px rgba(61,43,132,.08)}
.pricing-tabs button { min-height:44px;padding:0 20px;border:0;border-radius:11px;color:var(--muted);background:transparent;font-weight:750}.pricing-tabs button.active{color:white;background:var(--purple);box-shadow:0 8px 18px rgba(75,44,255,.25)}.pricing-tabs small{margin-left:4px;padding:3px 5px;border-radius:5px;color:#0a9b71;background:#e8fbf4}.pricing-tabs button.active small{color:white;background:rgba(255,255,255,.18)}
.pricing-grid { display:grid;grid-template-columns:repeat(2,minmax(0,480px));justify-content:center;gap:20px}.pricing-card{position:relative;padding:32px;border:1px solid var(--line);border-radius:23px;background:rgba(255,255,255,.84);box-shadow:0 18px 50px rgba(61,43,132,.09)}.pricing-card.featured{color:white;border-color:transparent;background:linear-gradient(145deg,#271174,#5430df);box-shadow:0 25px 60px rgba(63,31,199,.25)}.popular{position:absolute;top:20px;right:20px;padding:6px 9px;border-radius:99px;color:#4b2cff;background:#fff;font-size:.62rem;font-weight:850;text-transform:uppercase}.pricing-label{margin:0;font-weight:850}.price{margin:20px 0}.price strong,.price small{display:block}.price strong{font-size:2.5rem;letter-spacing:-.04em}.price small{margin-top:4px;color:var(--muted)}.featured .price small,.featured > p{color:#d8d1ff}.pricing-card ul{display:grid;gap:12px;margin:25px 0;padding:0;list-style:none}.pricing-card li{display:flex;gap:9px;font-size:.84rem}.pricing-card li svg{flex:0 0 auto;color:#6f54ff}.featured li svg{color:#bcb0ff}.pricing-card .primary-button,.pricing-card .secondary-button{width:100%;margin-top:5px}.pricing-card.featured .primary-button{color:var(--purple);background:white;box-shadow:none}

.faq-section { background:#fff }.faq-layout{display:grid;grid-template-columns:.65fr 1.35fr;gap:80px}.faq-heading h2{margin:17px 0;font-size:clamp(2.2rem,3.5vw,3.4rem);letter-spacing:-.05em}.faq-heading > p:last-child{color:var(--muted);line-height:1.65}.faq-list{display:grid;gap:10px}.faq-list article{border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:0 8px 26px rgba(61,43,132,.05)}.faq-list article.open{border-color:rgba(75,44,255,.25)}.faq-list button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:20px;padding:20px 22px;border:0;color:var(--ink);text-align:left;background:transparent;font-weight:800}.faq-list button span:last-child{display:grid;width:31px;height:31px;flex:0 0 auto;place-items:center;border-radius:50%;color:var(--purple);background:#f0edff;font-size:1.25rem;transition:.25s ease}.faq-list article.open button span:last-child{color:white;background:var(--purple);transform:rotate(45deg)}.faq-list article > div p{margin:0;padding:0 22px 20px;color:var(--muted);line-height:1.7}
.final-cta{padding:35px 0 70px;background:#fff}.final-cta-inner{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:40px 45px;border-radius:24px;color:white;background:radial-gradient(circle at 18% 0,rgba(145,121,255,.55),transparent 35%),linear-gradient(110deg,#241072,#4c28d5);box-shadow:0 25px 60px rgba(63,31,199,.23)}.final-cta p{margin:0;color:#cfc7ff;font-weight:750}.final-cta h2{max-width:800px;margin:8px 0 0;font-size:clamp(1.8rem,3vw,2.8rem);line-height:1.1;letter-spacing:-.04em}.cta-white{flex:0 0 auto;color:var(--purple);background:white;box-shadow:0 12px 26px rgba(20,10,70,.18)}.cta-white:hover{transform:translateY(-2px)}
.landing-footer{padding:48px 0 30px;color:#c6c9d7;background:#0d1022}.footer-grid{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:30px}.footer-brand{display:flex;align-items:center;gap:10px;color:white;font-size:1.35rem;font-weight:900;text-decoration:none}.footer-brand span{width:34px;height:34px;border-radius:9px}.footer-grid p{font-size:.82rem}.footer-grid > div{display:flex;gap:20px}.footer-grid a{color:#dfe1eb;text-decoration:none;font-size:.78rem}.footer-grid a:hover{color:white}.footer-grid > small{grid-column:1/-1;padding-top:25px;border-top:1px solid rgba(255,255,255,.1);color:#777d94}

@keyframes heroCubeFloat { 0%,100%{transform:translate(-48%,-49%) rotate(-1deg)}50%{transform:translate(-48%,calc(-49% - 13px)) rotate(1deg)} }
@keyframes cubeFloat { 0%,100%{margin-top:0}50%{margin-top:-13px} }
@keyframes cardFloat { 0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)} }
@keyframes nodeFloat { 0%,100%{margin-top:0}50%{margin-top:-7px} }
@keyframes orbitSpin { to{transform:translate(-50%,-50%) rotate(353deg)} }
@keyframes orbitSpinReverse { to{transform:translate(-50%,-50%) rotate(-353deg)} }

@media (max-width: 1180px) {
  .nav-shell{grid-template-columns:1fr auto}.nav-side{display:none}.brand{justify-self:start;padding:0;min-width:0}.brand-kicker{display:none}.menu-button{display:grid;justify-self:end}.mobile-menu{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px;padding:16px;border:1px solid rgba(255,255,255,.9);border-radius:20px;background:rgba(255,255,255,.92);box-shadow:0 18px 50px rgba(61,43,132,.15);backdrop-filter:blur(20px)}.mobile-menu > a:not(.login-button){padding:13px;border-radius:10px;color:var(--ink);font-weight:750;text-align:center;text-decoration:none}.mobile-menu .login-button{grid-column:1/-1}.hero-grid{grid-template-columns:1fr 1fr}.float-card{transform:scale(.88)}.heat-card{right:-3%}.traffic-card{right:-5%}.features-heading{grid-template-columns:1fr}.feature-card{grid-template-columns:1fr}.feature-mini{min-height:90px;margin:20px 0 0}.features-grid{grid-template-columns:repeat(3,1fr)}.ecosystem-node{width:122px}.seo-grid{gap:35px}.footer-grid{grid-template-columns:auto 1fr}.footer-grid > div{grid-column:1/-1;grid-row:2}.footer-grid > small{grid-row:3}
}

@media (max-width: 900px) {
  .section{padding:82px 0}.hero-section{min-height:0;padding-top:155px}.hero-grid{grid-template-columns:1fr}.hero-copy{text-align:center}.hero-copy .eyebrow{margin-inline:auto}.hero-lead{margin-inline:auto}.hero-actions,.hero-benefits{justify-content:center;margin-inline:auto}.hero-visual{min-height:570px}.metrics-strip{grid-template-columns:repeat(2,1fr)}.metrics-strip > div:nth-child(2){border-right:0}.features-grid{grid-template-columns:repeat(2,1fr)}.feature-promises{grid-template-columns:repeat(3,1fr)}.ecosystem-canvas{display:none}.ecosystem-section{min-height:0}.ecosystem-mobile-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.ecosystem-mobile-grid article{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--line);border-radius:15px;color:var(--purple);background:rgba(255,255,255,.8);box-shadow:0 10px 30px rgba(61,43,132,.07)}.ecosystem-mobile-grid strong,.ecosystem-mobile-grid small{display:block}.ecosystem-mobile-grid strong{color:var(--ink);font-size:.82rem}.ecosystem-mobile-grid small{margin-top:4px;color:var(--muted);font-size:.68rem}.seo-grid{grid-template-columns:1fr}.seo-copy{text-align:center}.seo-copy .eyebrow,.seo-copy > p:not(.eyebrow),.seo-summary{margin-inline:auto}.faq-layout{grid-template-columns:1fr;gap:35px}.final-cta-inner{display:grid;text-align:center;justify-items:center}.footer-grid{display:flex;flex-direction:column;align-items:flex-start}.footer-grid > small{width:100%}
}

@media (max-width: 640px) {
  :global(html){scroll-padding-top:96px}.landing-container{width:min(100% - 24px,1440px)}.section{padding:68px 0}.landing-header{top:max(8px,env(safe-area-inset-top));width:calc(100% - 16px)}.nav-shell{min-height:66px;padding:8px 10px 8px 14px;border-radius:19px}.brand-line{font-size:1.26rem}.brand-cube{width:34px;height:34px}.mobile-menu{grid-template-columns:1fr 1fr;padding:10px}.mobile-menu > a:not(.login-button){padding:11px 5px;font-size:.82rem}.hero-section{padding:125px 0 36px}.hero-copy{padding:0}.hero-copy h1{margin-top:23px;font-size:clamp(2.55rem,12vw,3.65rem)}.hero-lead{font-size:.94rem;line-height:1.7}.hero-actions{display:grid}.hero-actions > a{width:100%}.hero-benefits{grid-template-columns:1fr 1fr;gap:10px}.hero-benefit{align-items:flex-start;text-align:left;font-size:.7rem}.hero-visual{min-height:430px;margin-top:5px}.hero-cube{width:80%}.cube-stage{bottom:35px;width:250px;height:85px}.float-card{min-width:130px;padding:10px 11px;border-radius:13px;animation:none}.float-card small{margin-bottom:5px;font-size:.6rem}.float-card strong{font-size:.85rem}.visitors-card{top:23px;left:-7%;width:148px}.heat-card{top:50px;right:-9%;width:145px}.mini-heat{height:60px}.conversion-card{bottom:58px;left:-5%}.donut{width:38px;height:38px}.traffic-card{right:-6%;bottom:35px;width:143px}.metrics-strip{gap:0;padding-top:16px}.metrics-strip > div{padding:12px 8px;gap:8px}.metrics-strip strong{font-size:1.08rem}.metrics-strip small{font-size:.65rem}.features-heading{gap:28px}.section h2,.features-heading h2{font-size:2.35rem}.feature-promises{grid-template-columns:1fr}.feature-promises > div{min-height:0}.features-grid{grid-template-columns:1fr}.feature-card{grid-template-columns:minmax(0,1fr) minmax(115px,.72fr);min-height:210px;padding:20px}.feature-mini{min-height:0;margin:0 0 0 10px}.feature-card h3{margin-top:22px}.ecosystem-mobile-grid{grid-template-columns:1fr}.seo-summary{grid-template-columns:repeat(3,1fr)}.seo-summary > div{padding:13px 8px}.seo-summary strong{font-size:1.15rem}.seo-dashboard-body{padding:12px}.health-card{grid-template-columns:95px 1fr;padding:12px}.health-ring{width:84px;height:84px}.health-ring::after{inset:9px}.health-ring strong{font-size:1.4rem}.seo-checks{grid-template-columns:1fr}.ai-recommendation{grid-template-columns:auto 1fr}.ai-recommendation > svg{display:none}.pricing-tabs{width:100%}.pricing-tabs button{flex:1;padding:0 7px;font-size:.72rem}.pricing-grid{grid-template-columns:1fr}.pricing-card{padding:25px 20px}.faq-list button{padding:17px}.faq-list article > div p{padding:0 17px 17px}.final-cta{padding-bottom:45px}.final-cta-inner{padding:32px 20px}.cta-white{width:100%}.footer-grid > div{flex-wrap:wrap}
}

@media (max-width: 390px) {
  .hero-benefits{grid-template-columns:1fr}.feature-card{grid-template-columns:1fr}.feature-mini{margin:18px 0 0}.metrics-strip{grid-template-columns:1fr}.metrics-strip > div{border-right:0;border-bottom:1px solid var(--line)}.metrics-strip > div:last-child{border-bottom:0}.seo-summary small{font-size:.58rem}.health-card{grid-template-columns:1fr;text-align:center}.health-ring{margin:auto}.brand-line{gap:7px}.brand-cube{width:31px;height:31px}
}

@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}
</style>
