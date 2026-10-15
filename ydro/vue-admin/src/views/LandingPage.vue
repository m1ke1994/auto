<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  ArrowRight,
  BarChart3,
  ChevronRight,
  Code2,
  ExternalLink,
  Menu,
  SearchCheck,
  Sparkles,
  UsersRound,
  X,
} from '@lucide/vue'

import TrackNodeIcon from '../components/TrackNodeIcon.vue'
import {
  applyPublicSiteSeo,
  ensurePublicSiteTracker,
  loadTrackNodePublicSite,
  submitPublicSiteLead,
} from '../api/publicSite'

const PORTFOLIO_URL = 'https://tishechkinalexandr.ru/'
const site = ref(null)
const loading = ref(true)
const loadError = ref('')
const menuOpen = ref(false)
const openFaq = ref(0)
const cookieChoice = ref(null)
const cookiePreferencesOpen = ref(false)
const COOKIE_KEY = 'tracknode:analytics-consent:v1'
let revealObserver

const form = reactive({
  name: '',
  phone: '',
  email: '',
  taskType: 'Создание сайта с нуля',
  hasExistingSite: 'no',
  existingSiteUrl: '',
  message: '',
  preferredContact: 'email',
  consent: false,
  website: '',
})
const formState = reactive({ submitting: false, success: '', error: '', started: false })

const customBuildSteps = [
  ['Индивидуальный дизайн', 'Не шаблон, а визуальная система под бренд.'],
  ['Структура под бизнес', 'Страницы строятся вокруг пути клиента.'],
  ['Адаптивная разработка', 'Сайт аккуратно работает на разных экранах.'],
  ['SEO-база', 'Фундамент для дальнейшего роста заложен сразу.'],
]

const capabilityCards = [
  ['Сайты', Code2],
  ['Аналитика', BarChart3],
  ['CRM', UsersRound],
  ['SEO-аудит', SearchCheck],
  ['Отчёты', BarChart3],
  ['Разработка', Sparkles],
]

const pwaSteps = [
  ['iPhone', ['Откройте TrackNode в Safari', 'Нажмите «Поделиться»', 'Выберите «На экран Домой»']],
  ['Android', ['Откройте TrackNode в Chrome', 'Откройте меню браузера', 'Добавьте на главный экран']],
]

const taskTypes = [
  'Создание сайта с нуля',
  'Индивидуальный дизайн',
  'Структура и прототип',
  'Кабинет аналитики TrackNode',
  'SEO и развитие сайта',
  'Другое',
]

const faq = [
  ['Сайт делается по шаблону?', 'Нет. Структура, дизайн и интерфейс проектируются под конкретный бизнес.'],
  ['Что получает клиент после запуска?', 'Сайт и кабинет TrackNode с данными по посетителям, заявкам, источникам и SEO.'],
  ['Где смотреть заявки?', 'Все новые обращения отображаются в личном кабинете вместе с аналитикой сайта.'],
  ['Что показывает SEO-блок?', 'Техническое состояние, базовые ошибки и точки для дальнейшего развития сайта.'],
  ['Как рассчитывается стоимость сайта?', 'Стоимость рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности.'],
]

function track(type, payload = {}) {
  window.tracknode?.track?.(type, { source_site: 'tracknode', page_path: window.location.pathname, ...payload })
}

function trackPortfolioLink(placement) {
  track('portfolio_link_click', { destination: PORTFOLIO_URL, placement })
}

function formStarted() {
  if (formState.started) return
  formState.started = true
  track('lead_form_started', { placement: 'landing_contact' })
}

function setAnalyticsConsent(choice) {
  cookieChoice.value = choice
  cookiePreferencesOpen.value = false
  try { localStorage.setItem(COOKIE_KEY, choice) } catch { /* Browsers may restrict storage */ }
  if (choice === 'all' && site.value) ensurePublicSiteTracker(site.value)
  if (choice === 'essential') {
    window.__trackNodeTracker?.destroy?.('consent_revoked')
    document.querySelectorAll('script[data-tracknode-managed="true"]').forEach((el) => el.remove())
  }
}

function sanitize(value) {
  return String(value || '').replace(/[<>]/g, '').trim()
}

async function submitLead() {
  if (formState.submitting) return
  formState.error = ''
  formState.success = ''
  const hasContact = [form.phone, form.email].some((value) => sanitize(value))
  if (!sanitize(form.name) || !hasContact || !form.consent) {
    formState.error = 'Укажите имя, хотя бы один способ связи и подтвердите согласие на обработку данных.'
    return
  }
  formState.submitting = true
  const query = new URLSearchParams(window.location.search)
  try {
    await submitPublicSiteLead(site.value?.slug || 'tracknode', {
      name: sanitize(form.name),
      phone: sanitize(form.phone),
      email: sanitize(form.email),
      message: sanitize(form.message),
      source_url: window.location.href,
      section_key: 'landing-contact',
      form_name: 'Обсудить создание сайта',
      service_type: 'tracknode_landing_contact',
      service_title: sanitize(form.taskType),
      existing_site_url: sanitize(form.existingSiteUrl),
      preferred_contact: sanitize(form.preferredContact),
      consent: form.consent,
      website: sanitize(form.website),
      payload: {
        source: 'tracknode_landing_contact',
        consent_at: new Date().toISOString(),
        task_type: sanitize(form.taskType),
        has_existing_site: form.hasExistingSite,
        existing_site_url: sanitize(form.existingSiteUrl),
        preferred_contact: sanitize(form.preferredContact),
        referrer: document.referrer || '',
        utm_source: query.get('utm_source') || '',
        utm_medium: query.get('utm_medium') || '',
        utm_campaign: query.get('utm_campaign') || '',
        utm_term: query.get('utm_term') || '',
        utm_content: query.get('utm_content') || '',
      },
    })
    Object.assign(form, {
      name: '',
      phone: '',
      email: '',
      taskType: 'Создание сайта с нуля',
      hasExistingSite: 'no',
      existingSiteUrl: '',
      message: '',
      preferredContact: 'email',
      consent: false,
      website: '',
    })
    formState.success = 'Заявка отправлена. Я свяжусь с вами выбранным способом.'
    track('lead_form_success', { source: 'tracknode_landing_contact' })
  } catch (error) {
    formState.error = error?.message || 'Не удалось отправить заявку. Проверьте поля и попробуйте еще раз.'
    track('lead_form_error', { source: 'tracknode_landing_contact' })
  } finally {
    formState.submitting = false
  }
}

function closeMenu() { menuOpen.value = false }

function setupReveal() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => entry.isIntersecting && entry.target.classList.add('is-visible'))
  }, { threshold: 0.14 })
  document.querySelectorAll('[data-reveal]').forEach((element) => revealObserver.observe(element))
}

onMounted(async () => {
  try {
    const saved = localStorage.getItem(COOKIE_KEY)
    cookieChoice.value = ['all', 'essential'].includes(saved) ? saved : null
  } catch { cookieChoice.value = null }
  try {
    const payload = await loadTrackNodePublicSite()
    site.value = payload.site
    applyPublicSiteSeo({
      ...payload.site,
      seo: {
        ...(payload.site?.seo || {}),
        title: 'TrackNode — сайты, аналитика и заявки в единой системе',
        description: 'TrackNode объединяет разработку сайтов, аналитику посетителей, обработку заявок и SEO-аудит. Единое пространство для развития вашего бизнеса.',
        canonical: 'https://tracknode.ru/',
        og_title: 'TrackNode - цифровая платформа для сайта, заявок, аналитики и SEO',
        og_description: 'Создание сайта под бизнес, данные после запуска, заявки, SEO и уведомления в одном кабинете.',
        og_image: 'https://tracknode.ru/og-image.svg',
        structured_data: {
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'Organization',
              name: 'TrackNode',
              url: 'https://tracknode.ru/',
            },
            {
              '@type': 'WebSite',
              name: 'TrackNode',
              url: 'https://tracknode.ru/',
              inLanguage: 'ru-RU',
            },
            {
              '@type': 'Service',
              name: 'TrackNode - разработка сайтов и аналитическая платформа',
              provider: { '@type': 'Organization', name: 'TrackNode' },
              areaServed: 'RU',
              serviceType: ['создание сайтов', 'аналитика сайта', 'управление заявками', 'SEO-аудит', 'анализ конкурентов'],
            },
            {
              '@type': 'FAQPage',
              mainEntity: faq.map(([question, answer]) => ({
                '@type': 'Question',
                name: question,
                acceptedAnswer: { '@type': 'Answer', text: answer },
              })),
            },
          ],
        },
      },
    })
    if (cookieChoice.value === 'all') ensurePublicSiteTracker(payload.site)
    requestAnimationFrame(setupReveal)
  } catch (error) {
    loadError.value = error?.message || 'Не удалось загрузить TrackNode.'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => revealObserver?.disconnect())
</script>

<template>
  <div class="landing">
    <div v-if="loading" class="state" role="status">Загружаем TrackNode...</div>
    <div v-else-if="loadError" class="state" role="alert"><strong>Сайт временно недоступен</strong><span>{{ loadError }}</span></div>
    <template v-else>
      <header class="header">
        <nav class="wrap nav" aria-label="Основная навигация">
          <a class="brand" href="#top" @click="closeMenu">
            <TrackNodeIcon class="brand-icon" />
            <strong>tracknode<span class="brand-dot">.</span></strong>
          </a>
          <div class="desktop-nav">
            <a href="#website">Разработка</a>
            <a href="#analytics">Платформа</a>
            <a href="#features">Возможности</a>
            <a href="#pricing">Стоимость</a>
          </div>
          <div class="nav-actions">
            <RouterLink class="login" to="/login">Личный кабинет <ArrowRight :size="15" /></RouterLink>
            <a class="button small" href="#contact" @click="track('website_order_cta_click', { placement: 'header' })">Обсудить проект <ArrowRight :size="16" /></a>
          </div>
          <button class="menu-button" type="button" :aria-expanded="menuOpen" aria-controls="tracknode-mobile-menu" :aria-label="menuOpen ? 'Закрыть меню' : 'Открыть меню'" @click="menuOpen = !menuOpen">
            <X v-if="menuOpen" :size="23" /><Menu v-else :size="23" />
          </button>
        </nav>
        <div v-if="menuOpen" id="tracknode-mobile-menu" class="mobile-nav">
          <a href="#website" @click="closeMenu">Разработка</a>
          <a href="#analytics" @click="closeMenu">Платформа</a>
          <a href="#features" @click="closeMenu">Возможности</a>
          <a href="#pricing" @click="closeMenu">Стоимость</a>
          <a href="#contact" @click="closeMenu">Контакты</a>
          <RouterLink to="/login" @click="closeMenu">Личный кабинет</RouterLink>
          <RouterLink to="/register" @click="closeMenu">Регистрация</RouterLink>
        </div>
      </header>

      <main id="top">
        <section class="hero-stage">
          <div class="hero-glow" aria-hidden="true"></div>
          <div class="wrap hero">
            <div class="hero-copy" data-reveal>
              <p class="hero-eyebrow"><span class="status-light"></span> Цифровая платформа для бизнеса</p>
              <h1>Сайт — <span>начало.</span><br />Рост — <em>система.</em></h1>
              <p class="lead">Разрабатываем сайты и объединяем в одном кабинете всё, что происходит после запуска: посетителей, заявки, аналитику и SEO.</p>
              <div class="hero-actions">
                <a class="button" href="#contact" @click="track('website_order_cta_click', { placement: 'hero' })">Обсудить сайт <ArrowRight :size="19" /></a>
                <a class="text-link" href="#analytics" @click="track('analytics_section_cta_click', { placement: 'hero' })">Посмотреть платформу <ChevronRight :size="18" /></a>
              </div>
              <div class="hero-benefits" aria-label="Основные возможности">
                <span><span class="mini-dot"></span> Разработка под бизнес</span>
                <span><span class="mini-dot"></span> Прозрачная аналитика</span>
                <span><span class="mini-dot"></span> Управление заявками</span>
              </div>
            </div>

            <div class="hero-visual" data-reveal aria-label="Демонстрационный макет кабинета TrackNode">
              <div class="visual-outer-ring" aria-hidden="true"></div>
              <div class="mock-window">
                <div class="mock-topline">
                  <div class="mock-identity"><TrackNodeIcon class="mock-logo" /><span>tracknode <small>workspace</small></span></div>
                  <span class="mock-demo">Демонстрация интерфейса</span>
                </div>
                <div class="mock-greeting">
                  <span>Обзор бизнеса</span>
                  <b>Всё под контролем<span>.</span></b>
                </div>
                <div class="mock-stats">
                  <article><small>Посетители</small><strong>1 284</strong><span>↗ +18%</span></article>
                  <article><small>Обращения</small><strong>37</strong><span>↗ +12%</span></article>
                  <article><small>SEO-оценка</small><strong>82<span>/100</span></strong><span>Технический аудит</span></article>
                </div>
                <div class="mock-chart">
                  <div class="chart-header"><span>Активность сайта</span><small>Пример данных</small></div>
                  <svg viewBox="0 0 560 170" role="img" aria-label="Иллюстративный график посещений">
                    <defs><linearGradient id="landingChartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#5b84ff" stop-opacity=".30" /><stop offset="100%" stop-color="#5b84ff" stop-opacity="0" /></linearGradient></defs>
                    <path class="chart-grid" d="M0 43H560 M0 86H560 M0 129H560" />
                    <path class="chart-area" d="M0 145 C45 118 64 127 99 112 S165 137 196 89 S246 111 298 65 S360 104 412 49 S489 77 560 17 L560 170 L0 170 Z" />
                    <path class="chart-stroke" d="M0 145 C45 118 64 127 99 112 S165 137 196 89 S246 111 298 65 S360 104 412 49 S489 77 560 17" />
                  </svg>
                  <div class="chart-days"><span>ПН</span><span>ВТ</span><span>СР</span><span>ЧТ</span><span>ПТ</span><span>СБ</span><span>ВС</span></div>
                </div>
                <div class="mock-bottom"><span class="mock-pulse"></span> Сайт · Аналитика · CRM · SEO <span class="mock-bottom-arrow">↗</span></div>
              </div>
              <div class="mock-float"><span class="float-symbol">↗</span><div><b>Новая заявка</b><small>Поступила с сайта</small></div></div>
            </div>
          </div>
          <div class="hero-index wrap"><span>01 / Сайт</span><span>02 / Данные</span><span>03 / Развитие</span><span class="hero-index-end">От идеи — к измеримым действиям <ArrowRight :size="16" /></span></div>
        </section>

        <section class="intro-strip" aria-label="Что объединяет TrackNode">
          <div class="wrap intro-strip-inner">
            <span class="intro-label">Вместо разрозненных сервисов</span>
            <strong>Один сайт.<span> Один кабинет.</span> Одна понятная картина.</strong>
          </div>
        </section>

        <section id="website" class="landing-section website-section wrap" data-reveal>
          <div class="section-intro">
            <span class="section-number">01 / Разработка</span>
            <div><p class="kicker">От первого экрана до последней детали</p><h2>Сайт, который <span>решает задачу бизнеса.</span></h2></div>
            <p class="section-description">Создаём понятный путь клиента: от первого впечатления до заявки. Без случайных блоков и шаблонных решений.</p>
          </div>
          <div class="website-layout">
            <div class="browser-showcase" aria-label="Демонстрационный дизайн создаваемого сайта">
              <div class="browser-top"><span class="browser-dots"><i></i><i></i><i></i></span><span>yourbrand.ru</span><span>↗</span></div>
              <div class="browser-design">
                <div class="browser-heading"><span>ВАШ БРЕНД <b>✳</b></span><span>МЕНЮ &nbsp; КОНТАКТЫ</span></div>
                <div class="browser-display"><small>Новая точка роста</small><strong>Простые идеи.<br/><em>Сильный результат.</em></strong><span>Ваша уникальная история начинается здесь.</span><b>Оставить заявку ↗</b></div>
                <div class="browser-tiles"><span>Стратегия / 01</span><span>Дизайн / 02</span><span>Результат / 03</span></div>
              </div>
              <span class="showcase-caption">Концептуальный пример · не реальный проект</span>
            </div>
            <div class="website-details">
              <div class="detail-intro"><Sparkles :size="20" /><p>Сначала разбираемся в задаче. Потом проектируем решение — дизайн и разработка работают на общую цель.</p></div>
              <article v-for="([title, description], index) in customBuildSteps" :key="title">
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <div><h3>{{ title }}</h3><p>{{ description }}</p></div>
                <ArrowRight :size="19" />
              </article>
              <a class="inline-link" href="#contact" @click="track('website_order_cta_click', { placement: 'website' })">Рассказать о своей задаче <ArrowRight :size="18" /></a>
            </div>
          </div>
        </section>

        <section id="analytics" class="analytics-section" data-reveal>
          <div class="wrap">
            <div class="analytics-heading">
              <div><span class="section-number light">02 / Платформа</span><p class="kicker">Работа не заканчивается публикацией</p><h2>После запуска <em>начинается самое интересное.</em></h2></div>
              <p>TrackNode помогает видеть, откуда приходят люди, какие страницы работают и что мешает сайту развиваться.</p>
            </div>
            <div class="analytics-panel">
              <div class="analytics-panel-head"><div class="panel-mark"><TrackNodeIcon /> <span>TRACKNODE <small>ПАНЕЛЬ УПРАВЛЕНИЯ</small></span></div><span class="panel-example">Иллюстративные данные</span></div>
              <div class="analytics-panel-grid">
                <div class="analytics-large"><span class="overline">Пульс сайта / 7 дней</span><strong>Каждое действие <em>оставляет след.</em></strong>
                  <div class="activity-bars" aria-hidden="true"><i style="--h:42%"></i><i style="--h:64%"></i><i style="--h:51%"></i><i style="--h:78%"></i><i style="--h:59%"></i><i style="--h:90%"></i><i style="--h:72%"></i><i style="--h:86%"></i><i style="--h:65%"></i><i style="--h:100%"></i><i style="--h:80%"></i><i style="--h:93%"></i></div>
                  <small>Аналитика · Источники · Поведение</small>
                </div>
                <div class="analytics-side">
                  <article><span class="side-icon"><UsersRound :size="22" /></span><small>CRM И ЗАЯВКИ</small><h3>Обращения больше не теряются в переписках.</h3><span class="side-arrow">↗</span></article>
                  <article><span class="side-icon"><SearchCheck :size="22" /></span><small>SEO-КОНТРОЛЬ</small><h3>Технические ошибки — на виду.</h3><span class="side-arrow">↗</span></article>
                </div>
              </div>
            </div>
            <div class="analytics-foot"><span><span class="status-light"></span> Данные в одном рабочем пространстве</span><a href="#features">Все возможности <ArrowRight :size="18" /></a></div>
          </div>
        </section>

        <section id="features" class="landing-section capabilities wrap" data-reveal>
          <span id="seo" class="section-anchor" aria-hidden="true"></span>
          <div class="features-top"><div><span class="section-number">03 / Возможности</span><p class="kicker">Инструменты, которые дополняют друг друга</p><h2>Меньше переключений.<br/><span>Больше ясности.</span></h2></div><p>Не отдельные цифры ради отчёта, а связанная история: сайт, посетители, заявки и задачи на улучшение.</p></div>
          <div class="capability-grid">
            <article v-for="([title, icon], index) in capabilityCards" :key="title" :class="['capability-card', 'capability-' + index]">
              <div class="capability-top"><span class="capability-icon"><component :is="icon" :size="26" /></span><span class="capability-count">{{ String(index + 1).padStart(2, '0') }}</span></div>
              <div><h3>{{ title }}</h3><p>{{ ['Разработка и развитие онлайн-присутствия.', 'События, посетители и источники трафика.', 'Заявки и этапы работы с клиентами.', 'Технические проверки и точки роста.', 'Наглядная картина происходящего.', 'Новые решения под бизнес-задачи.'][index] }}</p></div>
              <span class="capability-arrow" aria-hidden="true">↗</span>
            </article>
          </div>
        </section>

        <section id="pwa" class="pwa-section" data-reveal>
          <div class="wrap pwa-layout">
            <div class="pwa-copy"><span class="section-number">04 / Мобильный доступ</span><p class="kicker">Ваш бизнес остаётся с вами</p><h2>В кабинете.<br/><span>В кармане.</span></h2><p>TrackNode можно добавить на главный экран смартфона и быстро возвращаться к рабочим данным.</p><div class="pwa-steps"><article v-for="[platform, steps] in pwaSteps" :key="platform"><h3>{{ platform }}</h3><ol><li v-for="(step, index) in steps" :key="step"><span>{{ String(index + 1).padStart(2, '0') }}</span>{{ step }}</li></ol></article></div></div>
            <div class="phone-stage" aria-label="Пример мобильного доступа TrackNode">
              <div class="phone-orbit" aria-hidden="true"></div>
              <div class="phone-device"><div class="phone-island"></div><div class="phone-time">09:41</div><TrackNodeIcon class="phone-app-icon"/><strong>TrackNode</strong><small>Ваш бизнес в одном месте</small><div class="phone-mini-card"><span>Панель управления</span><i></i><i></i><i></i></div><div class="phone-home"></div></div>
              <span class="phone-note">Без дополнительного приложения</span>
            </div>
          </div>
        </section>

        <section id="pricing" class="pricing-section wrap" data-reveal>
          <div><span class="section-number">05 / Сотрудничество</span><p class="kicker">Подход без лишних обещаний</p><h2>Под вашу задачу.<br/><span>С понятным объёмом работ.</span></h2><p>Стоимость разработки рассчитывается индивидуально после обсуждения задач, структуры и функциональности.</p><a class="button" href="#contact" @click="track('website_order_cta_click', { placement: 'pricing' })">Рассчитать проект <ArrowRight :size="18" /></a></div>
          <div class="pricing-note"><span>НЕ ШАБЛОННЫЙ ПАКЕТ</span><strong>Сначала задача.<br/>Потом решение.</strong><p>Разработка, аналитика и дальнейшее развитие — по согласованному объёму.</p><div id="developer" class="developer-note">Проект развивает Александр Тишечкин <a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" @click="trackPortfolioLink('developer')">Сайт разработчика <ExternalLink :size="15"/></a></div></div>
        </section>

        <section id="faq" class="faq wrap" data-reveal>
          <div class="faq-heading"><span class="section-number">06 / Ответы</span><h2>Вопросы, которые <span>стоит задать.</span></h2></div>
          <div class="faq-list">
            <article v-for="(item,index) in faq" :key="item[0]">
              <button type="button" :aria-expanded="openFaq===index" @click="openFaq=openFaq===index?-1:index"><span>{{ item[0] }}</span><b>{{ openFaq===index ? '−' : '+' }}</b></button>
              <p v-show="openFaq===index">{{ item[1] }}</p>
            </article>
          </div>
        </section>

        <section id="contact" class="contact">
          <div class="wrap contact-layout">
            <div class="contact-copy" data-reveal>
              <span class="section-number light">07 / Контакт</span><p class="kicker">Начнём с разговора</p>
              <h2>Есть идея?<br/><em>Давайте обсудим.</em></h2>
              <p>Расскажите, какой сайт нужен вашему бизнесу. Вернёмся с вопросами по задаче и обсудим возможный формат работы.</p>
              <div class="contact-side-note"><span class="status-light"></span> Каждая заявка попадает в рабочий кабинет TrackNode</div>
            </div>
            <form data-reveal novalidate @submit.prevent="submitLead" @focusin="formStarted">
              <div class="form-header"><span>Заявка на проект</span><span>01 / 01</span></div>
              <div class="form-grid">
                <label>Как к вам обращаться? <span aria-hidden="true">*</span><input v-model="form.name" maxlength="255" autocomplete="name" placeholder="Ваше имя" required /></label>
                <label>Телефон<input v-model="form.phone" maxlength="100" type="tel" autocomplete="tel" placeholder="+7 (999) 000-00-00" /></label>
                <label>Email<input v-model="form.email" maxlength="255" type="email" autocomplete="email" placeholder="name@company.ru" /></label>
                <label>Что нужно сделать?<select v-model="form.taskType"><option v-for="item in taskTypes" :key="item" :value="item">{{ item }}</option></select></label>
                <label class="wide-field">Как удобнее связаться?<select v-model="form.preferredContact"><option value="phone">По телефону</option><option value="email">По email</option></select></label>
                <label class="wide-field">Расскажите о задаче<textarea v-model="form.message" maxlength="2000" rows="4" placeholder="Пару слов о проекте, целях и пожеланиях..."></textarea></label>
              </div>
              <p class="required-note">* Имя и хотя бы один контакт обязательны.</p>
              <label class="honeypot" aria-hidden="true">Сайт<input v-model="form.website" tabindex="-1" autocomplete="off" /></label>
              <label class="consent"><input v-model="form.consent" type="checkbox" required /><span>Даю отдельное согласие на обработку указанных персональных данных для ответа на моё обращение. Подробнее — в <RouterLink to="/privacy">политике обработки персональных данных</RouterLink>.</span></label>
              <p class="form-legal-note">Отправка заявки не означает согласия на рекламу. Условия использования сервиса — в <RouterLink to="/terms">пользовательском соглашении</RouterLink>.</p>
              <p v-if="formState.success" class="success" role="status">{{ formState.success }}</p>
              <p v-if="formState.error" class="error" role="alert">{{ formState.error }}</p>
              <button class="button submit-button" type="submit" :disabled="formState.submitting">{{ formState.submitting ? 'Отправляем...' : 'Обсудить создание сайта' }} <ArrowRight :size="19" /></button>
            </form>
          </div>
        </section>
      </main>

      <footer>
        <div class="wrap footer-inner">
          <div class="footer-brand"><a class="brand" href="#top"><TrackNodeIcon class="brand-icon" /><strong>tracknode<span class="brand-dot">.</span></strong></a><p>Сайт, аналитика и развитие бизнеса в единой системе.</p><small>© {{ new Date().getFullYear() }} TrackNode</small></div>
          <nav aria-label="Ссылки в подвале">
            <a href="#website">Создание сайтов</a><a href="#analytics">Платформа</a><a href="#features">Возможности</a><a href="#seo">SEO</a><a href="#pwa">На смартфоне</a><a href="#pricing">Стоимость</a><a href="#contact">Контакты</a>
            <RouterLink to="/login">Вход</RouterLink><RouterLink to="/register">Регистрация</RouterLink>
            <RouterLink to="/privacy">Политика обработки персональных данных</RouterLink><RouterLink to="/terms">Пользовательское соглашение</RouterLink>
            <a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" @click="trackPortfolioLink('footer')">Сайт разработчика</a>
          </nav>
          <div class="footer-bottom"><span>Делаем сложное понятным.</span><button type="button" class="cookie-manage" @click="cookiePreferencesOpen = true">Настройки cookies</button></div>
        </div>
      </footer>

      <aside v-if="cookieChoice === null || cookiePreferencesOpen" class="cookie-notice" aria-label="Настройки файлов cookie">
        <div><strong>Вы управляете данными</strong><p>Необходимые файлы и локальные настройки помогают работе сайта. Необязательную аналитику посещений включаем только с вашего разрешения.</p><RouterLink to="/privacy">Подробнее об обработке данных</RouterLink></div>
        <div class="cookie-actions">
          <button type="button" class="cookie-accept" @click="setAnalyticsConsent('all')">Разрешить аналитику</button>
          <button type="button" class="cookie-essential" @click="setAnalyticsConsent('essential')">Только необходимые</button>
        </div>
      </aside>
    </template>
  </div>
</template>

<style scoped>
:global(*){box-sizing:border-box}
:global(html){scroll-behavior:smooth;scroll-padding-top:86px}
:global(body){margin:0;background:#f6f7f9}
.landing{--navy:#0a1630;--ink:#152340;--muted:#69768a;--blue:#456eff;--mint:#bcf0d9;--line:#e0e5ed;min-height:100vh;overflow-x:hidden;color:var(--ink);background:#f7f8fa;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{width:min(calc(100% - 80px),1240px);margin-inline:auto}
.state{display:grid;place-content:center;gap:12px;min-height:100vh;text-align:center}
.header{position:fixed;z-index:50;inset:0 0 auto;height:78px;color:white;background:rgba(9,20,43,.96);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(18px)}
.nav{display:flex;align-items:center;justify-content:space-between;gap:28px;height:100%}
.brand{display:inline-flex;align-items:center;gap:11px;color:inherit;text-decoration:none;font-size:1.35rem;letter-spacing:-.055em;font-weight:900;white-space:nowrap}
.brand-icon{width:33px;height:33px;flex:none}
.brand-dot{color:#78a2ff}
.desktop-nav{display:flex;align-items:center;gap:29px;margin-left:auto}
.desktop-nav a,.nav-actions .login{color:#d4dcea;text-decoration:none;font-size:.87rem;font-weight:650}
.desktop-nav a:hover,.nav-actions .login:hover{color:#fff}
.nav-actions{display:flex;align-items:center;gap:23px}
.nav-actions .login{display:inline-flex;align-items:center;gap:7px}
.button{display:inline-flex;align-items:center;justify-content:center;gap:13px;min-height:54px;padding:0 25px;border:0;border-radius:9px;background:#456eff;color:#fff;font:inherit;font-size:.94rem;font-weight:750;text-decoration:none;cursor:pointer;box-shadow:0 14px 38px rgba(35,65,184,.17);transition:transform .2s ease,background .2s ease,box-shadow .2s ease}
.button:hover{background:#315bed;transform:translateY(-2px);box-shadow:0 17px 44px rgba(35,65,184,.28)}
.button.small{min-height:41px;padding:0 17px;font-size:.81rem}
.button:disabled{opacity:.6;cursor:wait;transform:none}
.menu-button,.mobile-nav{display:none}
.hero-stage{position:relative;overflow:hidden;padding-top:78px;background:radial-gradient(ellipse at 80% 38%,#192f60 0%,transparent 42%),linear-gradient(130deg,#081326 10%,#111f3d 66%,#0c1630 100%);color:#f7faff}
.hero-glow{position:absolute;right:-170px;top:-280px;width:700px;height:700px;border:1px solid rgba(133,172,255,.16);border-radius:50%;box-shadow:0 0 0 90px rgba(114,155,248,.018),0 0 0 190px rgba(114,155,248,.018);pointer-events:none}
.hero{position:relative;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.05fr);gap:45px;align-items:center;min-height:730px;padding-block:95px 65px}
.hero-copy{position:relative;z-index:3}
.hero-eyebrow{display:inline-flex;align-items:center;gap:10px;margin:0 0 29px;color:#bbcaf0;font-size:.76rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.status-light{display:inline-block;width:8px;height:8px;flex:none;border-radius:50%;background:#a8edcb;box-shadow:0 0 0 5px rgba(168,237,203,.12)}
.hero h1{margin:0;font-size:clamp(3.25rem,5.1vw,5.7rem);line-height:1.01;letter-spacing:-.075em;font-weight:850}
.hero h1>span{color:#e3ecff}
.hero h1 em{color:#a8d6ff;font-style:normal}
.hero .lead{max-width:535px;margin:30px 0 0;color:#c0cbe0;font-size:1.08rem;line-height:1.75}
.hero-actions{display:flex;flex-wrap:wrap;align-items:center;gap:24px;margin-top:37px}
.text-link{display:inline-flex;align-items:center;gap:5px;color:#e8efff;text-decoration:none;font-size:.92rem;font-weight:700}
.text-link:hover{color:#a8d6ff}
.hero-benefits{display:flex;flex-wrap:wrap;gap:17px 21px;margin-top:72px;color:#aebcd4;font-size:.78rem}
.hero-benefits>span{display:inline-flex;align-items:center;gap:9px}
.mini-dot{width:5px;height:5px;border-radius:50%;background:#789eff}
.hero-visual{position:relative;min-width:0;padding:35px 0 42px 20px}
.visual-outer-ring{position:absolute;inset:3% 0 0 10%;border:1px solid rgba(154,182,250,.14);border-radius:50%;transform:rotate(-23deg)}
.mock-window{position:relative;z-index:1;overflow:hidden;border:1px solid rgba(172,193,237,.25);border-radius:19px;background:#f9fbff;color:#122343;box-shadow:0 55px 110px rgba(0,4,18,.42);transform:perspective(1200px) rotateY(-5deg) rotateX(3deg)}
.mock-topline{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:19px 22px;border-bottom:1px solid #e6eaf2}
.mock-identity{display:flex;align-items:center;gap:8px;font-weight:900;letter-spacing:-.04em}
.mock-identity .mock-logo{width:25px;height:25px}
.mock-identity small{color:#8b99b0;font-size:.7rem;font-weight:500;letter-spacing:0}
.mock-demo{color:#748299;font-size:.64rem}
.mock-greeting{display:grid;gap:7px;padding:23px 24px 18px}
.mock-greeting>span{color:#75839d;font-size:.72rem}
.mock-greeting b{font-size:1.42rem;letter-spacing:-.05em}
.mock-greeting b span{color:#456eff}
.mock-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;padding:0 23px}
.mock-stats article{display:flex;flex-direction:column;gap:8px;min-width:0;padding:13px;border:1px solid #e8ecf3;border-radius:10px;background:#fff}
.mock-stats small{color:#8491a6;font-size:.66rem}
.mock-stats strong{font-size:1.58rem;letter-spacing:-.06em;line-height:1.1}
.mock-stats strong span{color:#9ba7ba;font-size:.65rem}
.mock-stats article>span{color:#27856c;font-size:.62rem}
.mock-chart{margin:13px 23px 22px;padding:17px 16px 12px;border:1px solid #e8ecf3;border-radius:11px;background:#fff}
.chart-header{display:flex;justify-content:space-between;gap:12px;font-size:.7rem;font-weight:800}
.chart-header small{font-size:.6rem;color:#95a1b3;font-weight:500}
.mock-chart svg{display:block;width:100%;height:auto;margin:16px 0 5px}
.chart-grid{fill:none;stroke:#edf0f6;stroke-width:1}
.chart-area{fill:url(#landingChartFill)}
.chart-stroke{fill:none;stroke:#456eff;stroke-width:4;stroke-linecap:round}
.chart-days{display:flex;justify-content:space-between;color:#a0a9b9;font-size:.6rem;font-weight:700}
.mock-bottom{display:flex;align-items:center;gap:9px;padding:15px 24px;border-top:1px solid #e6eaf2;font-size:.7rem;font-weight:700;color:#738199}
.mock-pulse{width:8px;height:8px;border-radius:50%;background:#58caa4}
.mock-bottom-arrow{margin-left:auto;color:#456eff;font-size:1.2rem}
.mock-float{position:absolute;z-index:2;right:-22px;bottom:8px;display:flex;align-items:center;gap:12px;padding:15px 23px 15px 15px;border:1px solid rgba(255,255,255,.44);border-radius:12px;background:#d9e8ff;box-shadow:0 20px 45px rgba(4,14,37,.35);color:#19345d;transform:rotate(3deg)}
.float-symbol{display:grid;place-items:center;width:35px;height:35px;border-radius:9px;color:#fff;background:#456eff;font-size:1.5rem}
.mock-float div{display:grid;gap:4px;font-size:.83rem}
.mock-float small{font-size:.67rem;color:#596d8a}
.hero-index{position:relative;display:flex;align-items:center;gap:40px;padding:19px 0 23px;border-top:1px solid rgba(255,255,255,.13);color:#8293b2;font-size:.72rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
.hero-index-end{display:flex;align-items:center;gap:8px;margin-left:auto;color:#e1e8f6;letter-spacing:0;text-transform:none}
.intro-strip{padding:38px 0;background:#eaf0f6}
.intro-strip-inner{display:flex;align-items:center;justify-content:space-between;gap:30px}
.intro-label{color:#73829c;font-size:.74rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.intro-strip strong{font-size:clamp(1.1rem,2vw,1.7rem);letter-spacing:-.045em}
.intro-strip strong span{color:#456eff}
.landing-section{padding-block:125px}
.section-number{display:inline-flex;color:#456eff;font-size:.76rem;font-weight:900;letter-spacing:.06em;text-transform:uppercase}
.section-number.light{color:#98b8ff}
.kicker{margin:0 0 14px;color:#6a7e9f;font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.section-intro{display:grid;grid-template-columns:160px 1fr .65fr;gap:28px;align-items:end;margin-bottom:56px}
h2{margin:0;font-size:clamp(2.55rem,4.5vw,4.7rem);line-height:1.07;letter-spacing:-.067em;font-weight:850}
.section-intro h2 span,.features-top h2 span,.pwa-copy h2 span,.pricing-section h2 span,.faq h2 span{color:#8190a7}
.section-description{max-width:330px;margin:0 0 5px;color:#6e7b8f;line-height:1.7;font-size:.95rem}
.website-layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:60px;align-items:center}
.browser-showcase{position:relative;padding:18px 18px 38px;border:1px solid #d9e0ea;border-radius:18px;background:#fff;box-shadow:0 32px 75px rgba(16,36,71,.08)}
.browser-top{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:2px 7px 16px;color:#7e8aa0;font-size:.75rem}
.browser-dots{display:flex;gap:5px}.browser-dots i{width:8px;height:8px;border-radius:50%;background:#dce3ed}
.browser-design{overflow:hidden;border-radius:6px;background:#dfe9e1;color:#173829}
.browser-heading{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:20px 27px;color:#21412c;font-size:.7rem;font-weight:900;letter-spacing:.09em}
.browser-heading b{font-size:1.3rem;color:#df7545}
.browser-display{position:relative;display:flex;flex-direction:column;align-items:flex-start;min-height:335px;padding:35px 32px 30px;background:radial-gradient(circle at 87% 60%,#b5ceb2 0%,transparent 39%),linear-gradient(130deg,#e5efe7,#cfdeca)}
.browser-display small{font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em}
.browser-display strong{margin:17px 0;font-size:clamp(2rem,3.1vw,3.7rem);line-height:1.03;letter-spacing:-.073em}
.browser-display em{color:#d7794a;font-style:normal}
.browser-display>span{color:#597064;font-size:.77rem}
.browser-display>b{margin-top:35px;padding:13px 17px;border-radius:5px;background:#173829;color:white;font-size:.72rem}
.browser-tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#b8cebd}
.browser-tiles span{padding:18px 10px;background:#dae7dc;font-size:.66rem;font-weight:800;text-align:center}
.showcase-caption{position:absolute;right:20px;bottom:12px;color:#8e9aab;font-size:.65rem}
.website-details{display:flex;flex-direction:column;gap:0}
.detail-intro{display:flex;align-items:flex-start;gap:15px;margin-bottom:13px;color:#456eff}
.detail-intro p{margin:0;color:#4e607a;font-size:1.02rem;line-height:1.6}
.website-details article{display:grid;grid-template-columns:33px 1fr 24px;gap:14px;align-items:start;padding:19px 0;border-bottom:1px solid #e0e5ed}
.website-details article>span{color:#8796ae;font-size:.77rem;font-weight:800}
.website-details h3{margin:0 0 5px;font-size:1.07rem;letter-spacing:-.025em}
.website-details article p{margin:0;color:#75829a;font-size:.82rem;line-height:1.5}
.website-details article svg{color:#a0acbd}
.inline-link{display:inline-flex;align-items:center;gap:10px;margin-top:25px;color:#375de3;font-size:.91rem;font-weight:800;text-decoration:none}
.analytics-section{padding:120px 0;background:#101e3b;color:#fff}
.analytics-heading{display:grid;grid-template-columns:1fr .42fr;gap:65px;align-items:end;margin-bottom:50px}
.analytics-heading .kicker{margin-top:22px;color:#a8b9d8}
.analytics-heading h2{max-width:850px}
.analytics-heading h2 em{font-style:normal;color:#9fbbff}
.analytics-heading>p{margin:0 0 5px;color:#b6c3d9;line-height:1.7}
.analytics-panel{overflow:hidden;border:1px solid rgba(255,255,255,.12);border-radius:17px;background:#f3f6fa;color:#152340;box-shadow:0 38px 85px rgba(0,0,0,.22)}
.analytics-panel-head{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:19px 25px;background:#fff;border-bottom:1px solid #e3e8f0}
.panel-mark{display:flex;align-items:center;gap:12px;font-weight:900;font-size:.85rem;letter-spacing:.03em}
.panel-mark svg{width:31px;height:31px}
.panel-mark small{display:block;margin-top:4px;color:#8e9aad;font-size:.55rem;letter-spacing:.12em}
.panel-example{color:#95a0b1;font-size:.65rem}
.analytics-panel-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:18px;padding:20px}
.analytics-large{display:flex;flex-direction:column;min-height:370px;padding:30px;border:1px solid #e4e9f1;border-radius:10px;background:#fff}
.overline{color:#6a7a94;font-size:.68rem;font-weight:850;letter-spacing:.09em;text-transform:uppercase}
.analytics-large>strong{max-width:490px;margin-top:20px;font-size:clamp(1.5rem,2.9vw,3.1rem);line-height:1.08;letter-spacing:-.07em}
.analytics-large>strong em{color:#456eff;font-style:normal}
.activity-bars{display:flex;align-items:end;gap:9px;height:150px;min-height:90px;margin-top:auto;padding-top:25px;border-bottom:1px solid #dbe2ef}
.activity-bars i{height:var(--h);flex:1;min-width:3px;background:linear-gradient(0deg,#9bbbff,#456eff);border-radius:5px 5px 0 0;opacity:.82}
.analytics-large>small{padding-top:14px;color:#8b98ac;font-size:.7rem}
.analytics-side{display:grid;grid-template-rows:1fr 1fr;gap:18px}
.analytics-side article{position:relative;display:flex;flex-direction:column;align-items:flex-start;justify-content:space-between;padding:24px;border:1px solid #e2e8f0;border-radius:10px;background:#e5ecfb}
.analytics-side article:nth-child(2){background:#ddf1e7}
.side-icon{display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:#fff;color:#456eff}
.analytics-side article:nth-child(2) .side-icon{color:#127959}
.analytics-side small{margin-top:14px;color:#6780ad;font-size:.64rem;font-weight:900;letter-spacing:.08em}
.analytics-side h3{max-width:370px;margin:7px 35px 0 0;font-size:clamp(1.1rem,1.65vw,1.6rem);line-height:1.25;letter-spacing:-.055em}
.side-arrow{position:absolute;right:23px;bottom:22px;font-size:1.4rem;color:#4c6ac7}
.analytics-foot{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-top:30px;color:#a9b9d4;font-size:.77rem}
.analytics-foot>span{display:flex;align-items:center;gap:12px}
.analytics-foot a{display:inline-flex;align-items:center;gap:8px;color:#fff;text-decoration:none;font-weight:800}
.features-top{display:flex;justify-content:space-between;gap:50px;align-items:end;margin-bottom:48px}
.features-top .kicker{margin-top:24px}
.features-top>p{max-width:340px;margin:0 0 7px;color:#6b7a91;line-height:1.7}
.section-anchor{display:block;position:relative;top:-100px;height:0;visibility:hidden}
.capability-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.capability-card{position:relative;display:flex;flex-direction:column;justify-content:space-between;gap:48px;min-height:260px;padding:28px;border:1px solid #dfe4ee;border-radius:11px;background:#fff;transition:border-color .2s ease,transform .2s ease}
.capability-card:hover{border-color:#b2c5fb;transform:translateY(-3px)}
.capability-0{background:#e7edff}.capability-3{background:#e5f2ed}
.capability-top{display:flex;align-items:flex-start;justify-content:space-between}
.capability-icon{display:grid;place-items:center;width:52px;height:52px;border-radius:12px;background:#f2f5ff;color:#456eff}
.capability-0 .capability-icon{background:#fff}
.capability-3 .capability-icon{background:#fff;color:#1b8360}
.capability-count{color:#9aa6b8;font-size:.7rem;font-weight:850}
.capability-card h3{margin:0 0 9px;font-size:1.55rem;letter-spacing:-.05em}
.capability-card p{max-width:300px;margin:0;color:#697990;font-size:.85rem;line-height:1.55}
.capability-arrow{position:absolute;right:25px;bottom:24px;color:#92a4be;font-size:1.3rem}
.pwa-section{padding:100px 0;background:#e9eef5}
.pwa-layout{display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:100px}
.pwa-copy .kicker{margin-top:22px}
.pwa-copy>p:not(.kicker){max-width:490px;color:#61728c;line-height:1.7}
.pwa-steps{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:38px}
.pwa-steps article{padding-top:15px;border-top:1px solid #c9d5e5}
.pwa-steps h3{margin:0 0 15px;font-size:1.06rem}
.pwa-steps ol{display:grid;gap:11px;margin:0;padding:0;list-style:none}
.pwa-steps li{display:flex;align-items:baseline;gap:10px;color:#61728c;font-size:.79rem;line-height:1.5}
.pwa-steps li span{color:#456eff;font-weight:850}
.phone-stage{position:relative;display:grid;min-height:590px;place-items:center;overflow:hidden;border-radius:17px;background:radial-gradient(circle at center,#354f84,#14284f 72%)}
.phone-orbit{position:absolute;width:410px;height:410px;border-radius:50%;border:1px solid rgba(255,255,255,.14);box-shadow:0 0 0 65px rgba(255,255,255,.03),0 0 0 130px rgba(255,255,255,.03)}
.phone-device{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;width:236px;height:455px;border:7px solid #0a1327;border-radius:37px;background:linear-gradient(145deg,#eff3ff,#cddcf6);color:#18315d;box-shadow:0 35px 65px rgba(0,0,0,.42)}
.phone-island{position:absolute;top:9px;width:76px;height:20px;border-radius:20px;background:#0a1327}
.phone-time{align-self:flex-start;margin:30px 0 54px 23px;font-size:.72rem;font-weight:900}
.phone-app-icon{width:66px;height:66px;margin-bottom:14px}
.phone-device>strong{font-size:1.3rem;letter-spacing:-.05em}
.phone-device>small{margin-top:4px;color:#6981a8;font-size:.67rem}
.phone-mini-card{display:grid;gap:9px;width:80%;margin-top:24px;padding:16px;border-radius:10px;background:white;box-shadow:0 7px 25px rgba(51,86,141,.1)}
.phone-mini-card span{font-size:.65rem;font-weight:800}
.phone-mini-card i{height:7px;border-radius:8px;background:#dde5f6}
.phone-mini-card i:nth-of-type(2){width:65%;background:#93b1fa}
.phone-mini-card i:nth-of-type(3){width:80%}
.phone-home{position:absolute;bottom:10px;width:73px;height:4px;border-radius:10px;background:#5b6e8b}
.phone-note{position:absolute;bottom:21px;color:#bfd0e9;font-size:.7rem}
.pricing-section{display:grid;grid-template-columns:1fr .72fr;gap:100px;align-items:center;padding-block:120px}
.pricing-section .kicker{margin-top:24px}
.pricing-section p:not(.kicker){max-width:530px;margin:25px 0 28px;color:#65748c;line-height:1.7}
.pricing-note{padding:42px;border:1px solid #dbe4f1;border-radius:14px;background:#e6edfc}
.pricing-note>span{color:#4e69ab;font-size:.66rem;font-weight:900;letter-spacing:.13em}
.pricing-note>strong{display:block;margin:35px 0 16px;font-size:clamp(1.8rem,2.8vw,2.8rem);line-height:1.2;letter-spacing:-.065em}
.pricing-note p{margin:0!important;font-size:.89rem}
.developer-note{display:grid;gap:13px;margin-top:34px;padding-top:23px;border-top:1px solid #c7d3eb;color:#5b6e8f;font-size:.78rem}
.developer-note a{display:inline-flex;align-items:center;gap:7px;color:#365ce0;text-decoration:none;font-weight:800}
.faq{display:grid;grid-template-columns:.8fr 1.2fr;gap:80px;padding-block:105px}
.faq h2{margin-top:22px;font-size:clamp(2.2rem,3.7vw,4rem)}
.faq article{border-bottom:1px solid #dce3ec}
.faq article:first-child{border-top:1px solid #dce3ec}
.faq button{display:flex;align-items:center;justify-content:space-between;gap:25px;width:100%;padding:22px 0;border:0;background:none;color:#182944;text-align:left;font:inherit;font-weight:800;cursor:pointer}
.faq button b{font-size:1.45rem;color:#456eff;font-weight:500}
.faq article p{margin:0 35px 22px 0;color:#62728d;line-height:1.7;font-size:.89rem}
.contact{padding:110px 0;background:#101e3b;color:#fff}
.contact-layout{display:grid;grid-template-columns:.85fr 1.15fr;gap:105px;align-items:start}
.contact-copy .kicker{margin:25px 0 18px;color:#9cafd0}
.contact-copy h2{font-size:clamp(3rem,5vw,5.6rem)}
.contact-copy h2 em{color:#a5c6ff;font-style:normal}
.contact-copy>p:not(.kicker){max-width:410px;margin-top:28px;color:#b3c1d8;line-height:1.75}
.contact-side-note{display:flex;align-items:center;gap:15px;margin-top:70px;color:#a9bddd;font-size:.77rem}
.contact form{padding:32px;border-radius:12px;background:#fff;color:#192942}
.form-header{display:flex;justify-content:space-between;gap:20px;padding-bottom:20px;border-bottom:1px solid #e1e6ed;font-size:.82rem;font-weight:850}
.form-header span:last-child{color:#a0abba}
.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:23px}
.form-grid label{display:grid;gap:8px;font-size:.8rem;font-weight:800}
.form-grid label>span{color:#e15e53}
.form-grid input,.form-grid select,.form-grid textarea{display:block;width:100%;min-height:46px;min-width:0;padding:12px 13px;border:1px solid #dce3ed;border-radius:7px;color:#172a48;background:#f9fbfe;font:inherit;font-size:.86rem;outline:none}
.form-grid input:focus,.form-grid select:focus,.form-grid textarea:focus{border-color:#456eff;box-shadow:0 0 0 3px rgba(69,110,255,.1)}
.form-grid textarea{min-height:105px;resize:vertical}
.wide-field{grid-column:1/-1}
.required-note{margin:14px 0;color:#8291a8;font-size:.7rem}
.honeypot{position:absolute!important;left:-10000px!important}
.consent{display:flex;gap:12px;align-items:flex-start;margin-top:18px;font-size:.76rem;line-height:1.55;color:#526078;cursor:pointer}
.consent input{width:17px;height:17px;flex:0 0 17px;margin:2px 0 0;accent-color:#456eff}
.consent a,.form-legal-note a{color:#365ce0;font-weight:750}
.form-legal-note{color:#7988a0;font-size:.69rem;line-height:1.55}
.success{color:#1a8d66;font-size:.83rem;font-weight:750}
.error{color:#bf403e;font-size:.83rem;font-weight:750}
.submit-button{width:100%;margin-top:12px}
footer{padding:67px 0 29px;background:#081326;color:#fff}
.footer-inner{display:grid;grid-template-columns:.8fr 1.2fr;gap:50px}
.footer-brand p{max-width:230px;margin:19px 0;color:#8e9db9;font-size:.84rem;line-height:1.7}
.footer-brand small{color:#6d7b99;font-size:.72rem}
footer nav{display:grid;grid-template-columns:1fr 1fr;gap:15px 20px;align-content:start}
footer nav a{color:#b2bfda;text-decoration:none;font-size:.79rem}
footer nav a:hover{color:#fff}
.footer-bottom{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:22px;margin-top:22px;padding-top:25px;border-top:1px solid #23324e;color:#7687a5;font-size:.75rem}
.cookie-manage{padding:0;border:0;background:none;color:#bfd0ff;font:inherit;font-weight:800;text-decoration:underline;cursor:pointer}
.cookie-notice{position:fixed;z-index:90;right:22px;bottom:22px;display:flex;align-items:center;justify-content:space-between;gap:32px;width:min(calc(100% - 44px),790px);padding:22px 25px;border:1px solid #cbd7eb;border-radius:13px;background:#fff;color:#20304a;box-shadow:0 22px 80px rgba(0,9,29,.25)}
.cookie-notice strong{font-size:.92rem}
.cookie-notice p{max-width:470px;margin:7px 0;color:#62738e;font-size:.75rem;line-height:1.6}
.cookie-notice a{color:#365ce0;font-size:.71rem;font-weight:750}
.cookie-actions{display:grid;gap:8px;flex:0 0 180px}
.cookie-actions button{min-height:39px;padding:0 12px;border:1px solid #dbe3f0;border-radius:7px;background:#f3f6fa;color:#283f62;font:inherit;font-size:.73rem;font-weight:800;cursor:pointer}
.cookie-actions .cookie-accept{border-color:#456eff;background:#456eff;color:#fff}
[data-reveal]{opacity:0;transform:translateY(18px);transition:opacity .7s ease,transform .7s ease}
[data-reveal].is-visible{opacity:1;transform:none}
@media(max-width:1120px){
  .wrap{width:min(calc(100% - 54px),1240px)}
  .desktop-nav{gap:15px}
  .nav-actions{gap:14px}
  .hero{gap:15px}
  .hero h1{font-size:clamp(3rem,5vw,4.8rem)}
  .section-intro{grid-template-columns:130px 1fr}
  .section-description{grid-column:2;max-width:520px}
  .website-layout{gap:35px}
  .pwa-layout{gap:45px}
  .contact-layout{gap:45px}
}
@media(max-width:900px){
  .desktop-nav,.nav-actions{display:none}
  .menu-button{display:grid;place-items:center;width:41px;height:41px;border:1px solid #33425e;border-radius:8px;background:#172846;color:#fff;cursor:pointer}
  .mobile-nav{display:grid;position:fixed;top:78px;left:0;right:0;padding:10px 27px 22px;background:#101e3b;border-top:1px solid rgba(255,255,255,.1);box-shadow:0 22px 38px rgba(0,0,0,.25)}
  .mobile-nav a{padding:12px 0;color:#e2eaf8;text-decoration:none;font-size:.95rem;font-weight:800;border-bottom:1px solid rgba(255,255,255,.08)}
  .hero{grid-template-columns:1fr;min-height:0;padding-block:80px 75px}
  .hero-copy{max-width:690px}
  .hero-visual{max-width:680px;width:100%;margin-inline:auto;padding:10px 0 50px}
  .hero-benefits{margin-top:46px}
  .hero-index{flex-wrap:wrap}
  .hero-index-end{margin-left:0}
  .website-layout,.analytics-heading,.pwa-layout,.pricing-section,.faq,.contact-layout{grid-template-columns:1fr}
  .website-layout{gap:45px}
  .analytics-heading{gap:20px}
  .analytics-heading>p{max-width:650px}
  .pwa-layout{gap:40px}
  .phone-stage{min-height:490px}
  .faq{gap:30px}
  .faq h2{max-width:680px}
  .contact-copy>p:not(.kicker){max-width:680px}
  .contact-side-note{margin-top:35px}
}
@media(max-width:680px){
  .wrap{width:min(calc(100% - 32px),1240px)}
  .header{height:66px}
  .mobile-nav{top:66px;padding-inline:17px}
  :global(html){scroll-padding-top:74px}
  .hero-stage{padding-top:66px}
  .hero{padding-block:65px 52px}
  .hero-eyebrow{font-size:.63rem;letter-spacing:.07em}
  .hero h1{font-size:clamp(2.85rem,10.4vw,4.3rem)}
  .hero .lead{font-size:.95rem;margin-top:23px}
  .hero-actions{gap:18px;margin-top:28px}
  .hero-actions .button{width:100%}
  .hero-benefits{gap:12px;margin-top:39px;font-size:.7rem}
  .mock-window{transform:none}
  .mock-identity small{display:none}
  .mock-demo{font-size:.57rem}
  .mock-topline{padding:13px}
  .mock-greeting{padding:18px 13px 13px}
  .mock-stats{padding:0 12px;gap:5px}
  .mock-stats article{padding:8px}
  .mock-stats strong{font-size:1.08rem}
  .mock-stats small,.mock-stats article>span{font-size:.51rem}
  .mock-chart{margin:9px 12px 13px;padding:12px}
  .mock-chart svg{margin-top:9px}
  .mock-bottom{padding:10px 12px}
  .mock-float{right:0;bottom:12px;padding:9px 12px}
  .hero-index{gap:12px 19px;font-size:.61rem}
  .intro-strip{padding:25px 0}
  .intro-strip-inner{align-items:flex-start;flex-direction:column;gap:11px}
  .landing-section{padding-block:77px}
  .section-intro{grid-template-columns:1fr;gap:18px;margin-bottom:35px}
  .section-description{grid-column:1}
  h2{font-size:clamp(2.45rem,9vw,3.6rem)}
  .browser-showcase{padding:8px 8px 32px}
  .browser-display{min-height:275px;padding:22px 18px}
  .browser-display strong{font-size:clamp(2rem,7vw,3.2rem)}
  .browser-heading{padding:15px;font-size:.58rem}
  .browser-tiles span{padding:13px 4px;font-size:.55rem}
  .website-details article{gap:6px}
  .analytics-section{padding:78px 0}
  .analytics-heading{margin-bottom:30px}
  .analytics-panel-head{padding:13px}
  .analytics-panel-grid{grid-template-columns:1fr;gap:9px;padding:9px}
  .analytics-large{min-height:280px;padding:20px}
  .analytics-side{grid-template-columns:1fr 1fr;grid-template-rows:auto;gap:9px}
  .analytics-side article{min-height:180px;padding:16px}
  .analytics-side h3{margin:7px 0 28px;font-size:1rem}
  .side-arrow{right:12px;bottom:10px}
  .analytics-foot{align-items:flex-start;flex-direction:column}
  .features-top{align-items:flex-start;flex-direction:column;gap:13px}
  .capability-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .capability-card{min-height:230px;padding:17px;gap:40px}
  .capability-card h3{font-size:1.27rem}
  .capability-card p{font-size:.76rem}
  .capability-icon{width:39px;height:39px}
  .capability-arrow{right:15px;bottom:13px}
  .pwa-section{padding:78px 0}
  .pwa-steps{grid-template-columns:1fr}
  .phone-stage{min-height:500px}
  .pricing-section{gap:30px;padding-block:78px}
  .pricing-note{padding:28px}
  .faq{padding-block:75px}
  .contact{padding:77px 0}
  .contact-layout{gap:35px}
  .contact form{padding:22px 17px}
  .form-grid{grid-template-columns:1fr;gap:15px}
  .wide-field{grid-column:auto}
  .footer-inner{grid-template-columns:1fr;gap:32px}
  footer nav{grid-template-columns:1fr 1fr}
  .footer-bottom{margin-top:3px}
  .cookie-notice{left:12px;right:12px;bottom:12px;width:auto;flex-direction:column;align-items:stretch;gap:14px;padding:17px}
  .cookie-actions{display:grid;grid-template-columns:1fr 1fr;flex:auto}
}
@media(max-width:410px){
  .hero h1{font-size:2.68rem}
  .capability-grid{grid-template-columns:1fr}
  .capability-card{min-height:190px}
  .analytics-side{grid-template-columns:1fr}
  .cookie-actions{grid-template-columns:1fr}
}
@media(prefers-reduced-motion:reduce){
  :global(html){scroll-behavior:auto}
  [data-reveal]{opacity:1;transform:none;transition:none}
  .button,.capability-card{transition:none}
}
</style>
