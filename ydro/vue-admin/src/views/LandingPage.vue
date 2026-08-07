<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  ArrowRight,
  BarChart3,
  Bell,
  Bot,
  Check,
  ChevronRight,
  CircleDollarSign,
  Code2,
  ExternalLink,
  FileSearch,
  LayoutDashboard,
  Menu,
  MessageSquare,
  SearchCheck,
  Send,
  Sparkles,
  UsersRound,
  X,
} from '@lucide/vue'

import {
  applyPublicSiteSeo,
  ensurePublicSiteTracker,
  loadTrackNodePublicSite,
  submitPublicSiteLead,
} from '../api/publicSite'

const PORTFOLIO_URL = 'https://tishechkinalexandr.ru/'
const site = ref(null)
const sections = ref([])
const loading = ref(true)
const loadError = ref('')
const menuOpen = ref(false)
const openFaq = ref(0)
let revealObserver

const form = reactive({
  name: '',
  phone: '',
  telegram: '',
  email: '',
  taskType: 'Создание сайта',
  hasExistingSite: 'no',
  existingSiteUrl: '',
  message: '',
  preferredContact: 'telegram',
  consent: false,
  website: '',
})
const formState = reactive({ submitting: false, success: '', error: '', started: false })

const sectionsByKey = computed(() => Object.fromEntries(sections.value.map((item) => [item.key, item.content || {}])))
const plans = computed(() => (sectionsByKey.value.tariffs?.plans || []).filter((plan, index, items) => {
  const key = plan.title || plan.name
  return key && items.findIndex((item) => (item.title || item.name) === key) === index
}).slice(0, 2))

const platformFlow = ['Сайт', 'Заявка', 'CRM', 'Telegram', 'Аналитика', 'SEO', 'Развитие']
const valueSteps = [
  ['01', 'Создаем или подключаем сайт', 'Проект можно запустить с нуля или подключить TrackNode к текущему сайту через аналитический скрипт.'],
  ['02', 'Собираем заявки и действия', 'Посещения, формы, источники, клики и обращения попадают в единую систему без ручных таблиц.'],
  ['03', 'Помогаем развивать проект', 'SEO-аудит, конкуренты и AI-рекомендации показывают, что стоит улучшить дальше.'],
]

const taskTypes = [
  'Создание сайта',
  'Подключение аналитики',
  'Управление заявками',
  'CRM-интеграция',
  'Telegram-уведомления',
  'SEO-аудит',
  'Анализ конкурентов',
  'Другое',
]

const features = [
  {
    title: 'Создание сайтов',
    text: 'Индивидуальная структура, уникальный дизайн, адаптивная верстка, формы, домен, базовая SEO-подготовка и управление контентом.',
    icon: Code2,
    class: 'wide',
  },
  {
    title: 'Управление заявками',
    text: 'Единый центр обращений: контакт, источник, статус, дата и история обработки. Подготовка к CRM-интеграциям по задаче клиента.',
    icon: UsersRound,
    class: 'tall',
  },
  {
    title: 'Аналитика',
    text: 'Посещения, просмотры, источники переходов, действия пользователей, формы и ключевые события в личном кабинете.',
    icon: BarChart3,
  },
  {
    title: 'Telegram-уведомления',
    text: 'Новые заявки приходят в Telegram, чтобы не проверять кабинет каждую минуту.',
    icon: Bell,
  },
  {
    title: 'SEO-аудит',
    text: 'Техническое состояние, метаданные, структура, ошибки и рекомендации по улучшению сайта.',
    icon: FileSearch,
    class: 'wide',
  },
  {
    title: 'Анализ конкурентов',
    text: 'Сравнение структуры, контента, преимуществ и точек для улучшения предложения.',
    icon: SearchCheck,
  },
  {
    title: 'AI-рекомендации',
    text: 'Идеи по контенту, структуре, продвижению и развитию проекта на основе собранных данных.',
    icon: Sparkles,
  },
]

const faq = [
  ['Можно ли заказать только сайт?', 'Да. Можно обсудить только разработку сайта, а аналитику TrackNode подключить сразу при запуске или позже.'],
  ['Можно ли подключить TrackNode к существующему сайту?', 'Да. Для этого используется аналитический скрипт и настройка сайта в личном кабинете.'],
  ['Это полноценная CRM?', 'Сейчас TrackNode закрывает управление заявками и обращениями. CRM-интеграции можно подключать по задаче клиента.'],
  ['Будут ли Telegram-уведомления?', 'Да, TrackNode поддерживает уведомления о новых заявках в Telegram.'],
  ['Что показывает SEO-аудит?', 'Технические проблемы, метаданные, структуру, ошибки и рекомендации для дальнейших улучшений.'],
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

function sanitize(value) {
  return String(value || '').replace(/[<>]/g, '').trim()
}

async function submitLead() {
  if (formState.submitting) return
  formState.error = ''
  formState.success = ''
  const hasContact = [form.phone, form.telegram, form.email].some((value) => sanitize(value))
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
      telegram: sanitize(form.telegram),
      email: sanitize(form.email),
      message: sanitize(form.message),
      source_url: window.location.href,
      section_key: 'landing-contact',
      form_name: 'Обсудим ваш проект',
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
        telegram: sanitize(form.telegram),
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
      telegram: '',
      email: '',
      taskType: 'Создание сайта',
      hasExistingSite: 'no',
      existingSiteUrl: '',
      message: '',
      preferredContact: 'telegram',
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
    const payload = await loadTrackNodePublicSite()
    site.value = payload.site
    sections.value = payload.sections
    applyPublicSiteSeo({
      ...payload.site,
      seo: {
        ...(payload.site?.seo || {}),
        title: 'TrackNode - создание сайтов, аналитика, заявки и SEO в одной платформе',
        description: 'TrackNode создает сайты под заказ или подключается к существующему сайту: заявки, управление обращениями, аналитика, Telegram-уведомления, SEO-аудит, конкуренты и AI-рекомендации.',
        canonical: 'https://tracknode.ru/',
        og_title: 'TrackNode - цифровая платформа для сайта, заявок, аналитики и SEO',
        og_description: 'Создание сайтов, подключение аналитики, управление заявками, Telegram-уведомления, SEO-аудит, конкуренты и AI-рекомендации в одном кабинете.',
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
    ensurePublicSiteTracker(payload.site)
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
    <div v-if="loading" class="state">Загружаем TrackNode...</div>
    <div v-else-if="loadError" class="state"><strong>Сайт временно недоступен</strong><span>{{ loadError }}</span></div>
    <template v-else>
      <header class="header">
        <nav class="wrap nav" aria-label="Основная навигация">
          <a class="brand" href="#top" @click="closeMenu">
            <span class="brand-mark" aria-hidden="true"><i v-for="dot in 7" :key="dot" /></span>
            <strong>TRACKNODE</strong>
          </a>
          <div class="desktop-nav">
            <a href="#features">Возможности</a>
            <a href="#pricing">Тарифы</a>
            <a href="#website">Решения</a>
            <a href="#developer">О нас</a>
            <a href="#faq">Блог</a>
            <a href="#analytics">Аналитика</a>
            <a href="#contact">Контакты</a>
          </div>
          <div class="nav-actions">
            <RouterLink to="/login" class="login">Войти</RouterLink>
            <a class="button small" href="#contact" @click="track('website_order_cta_click', { placement: 'header' })">Заказать сайт</a>
          </div>
          <button class="menu-button" type="button" :aria-expanded="menuOpen" aria-label="Открыть меню" @click="menuOpen = !menuOpen">
            <X v-if="menuOpen" /><Menu v-else />
          </button>
        </nav>
        <div v-if="menuOpen" class="mobile-nav">
          <a href="#features" @click="closeMenu">Возможности</a>
          <a href="#pricing" @click="closeMenu">Тарифы</a>
          <a href="#website" @click="closeMenu">Решения</a>
          <a href="#developer" @click="closeMenu">О нас</a>
          <a href="#faq" @click="closeMenu">Блог</a>
          <a href="#analytics" @click="closeMenu">Аналитика</a>
          <a href="#contact" @click="closeMenu">Контакты</a>
          <RouterLink to="/login" @click="closeMenu">Войти</RouterLink>
          <a href="#contact" @click="closeMenu">Заказать сайт</a>
        </div>
      </header>

      <main id="top">
        <section class="hero wrap">
          <div class="hero-copy" data-reveal>
            <p class="kicker"><Sparkles :size="14" /> Разработка сайтов и аналитика для бизнеса</p>
            <h1>
              <span>Создаем сайты.</span>
              <span>Анализируем.</span>
              <span class="accent-text">Помогаем расти.</span>
            </h1>
            <p class="lead">Создаем современные сайты под задачи бизнеса и подключаем аналитику, SEO-аудит, заявки, CRM и уведомления в Telegram.</p>
            <div class="hero-actions">
              <a class="button" href="#contact" @click="track('website_order_cta_click', { placement: 'hero' })">Заказать сайт <ArrowRight :size="18" /></a>
              <RouterLink class="button secondary" to="/register" @click="track('analytics_connect_cta_click', { placement: 'hero' })">Подключить аналитику <ChevronRight :size="17" /></RouterLink>
            </div>
          </div>

          <div class="hero-visual" data-reveal aria-label="Компас возможностей TrackNode">
            <div class="hero-compass-stage">
              <div class="orbit orbit-one" />
              <div class="orbit orbit-two" />
              <div class="orbit-dot dot-a" />
              <div class="orbit-dot dot-b" />
              <div class="orbit-dot dot-c" />
              <img class="compass-img" src="/images/landing/compas.png" alt="Компас TrackNode: сайты, SEO, аналитика и CRM" />
              <div class="compass-label label-sites">
                <span><Code2 :size="28" /></span>
                <b>Сайты</b>
              </div>
              <div class="compass-label label-analytics">
                <span><BarChart3 :size="28" /></span>
                <b>Аналитика</b>
              </div>
              <div class="compass-label label-crm">
                <span><UsersRound :size="28" /></span>
                <b>CRM</b>
              </div>
              <div class="compass-label label-seo">
                <span><SearchCheck :size="30" /></span>
                <b>SEO-аудит</b>
              </div>
              <div class="compass-label label-telegram">
                <span><Send :size="28" /></span>
                <b>Telegram</b>
              </div>
            </div>
          </div>
        </section>

        <section class="value wrap" data-reveal>
          <p class="kicker">Единая экосистема</p>
          <h2>От идеи сайта до первой заявки и дальнейшей аналитики</h2>
          <div class="value-line">
            <article v-for="[number, title, text] in valueSteps" :key="number">
              <span>{{ number }}</span><h3>{{ title }}</h3><p>{{ text }}</p>
            </article>
          </div>
        </section>

        <section class="scenarios wrap" data-reveal>
          <article class="glass scenario website-scenario">
            <Code2 :size="34" />
            <h2>Нужен новый сайт</h2>
            <p>Проектируем структуру, готовим индивидуальный дизайн, адаптивную верстку, формы заявок, подключение домена, аналитику, Telegram-уведомления и личный кабинет для контента и обращений.</p>
            <ul>
              <li v-for="item in ['Структура под задачи компании', 'Уникальный дизайн', 'Адаптивная верстка', 'Формы заявок', 'SEO-подготовка', 'Дальнейшее развитие']" :key="item"><Check :size="16" />{{ item }}</li>
            </ul>
            <a class="button" href="#contact">Обсудить создание сайта</a>
          </article>
          <article class="glass scenario existing-scenario">
            <BarChart3 :size="34" />
            <h2>Сайт уже существует</h2>
            <p>Подключаем TrackNode к текущему сайту: посещения, действия, заявки, управление обращениями, Telegram, SEO-аудит, конкуренты, отчеты и AI-рекомендации.</p>
            <ul>
              <li v-for="item in ['Аналитический скрипт', 'Отслеживание заявок', 'Управление обращениями', 'SEO-аудит', 'Анализ конкурентов', 'AI-рекомендации']" :key="item"><Check :size="16" />{{ item }}</li>
            </ul>
            <RouterLink class="button secondary" to="/register">Подключить существующий сайт</RouterLink>
          </article>
        </section>

        <section id="features" class="features wrap" data-reveal>
          <p class="kicker">Возможности платформы</p>
          <h2>Инструменты, которые связаны с реальной работой сайта</h2>
          <div class="bento">
            <article v-for="feature in features" :key="feature.title" class="glass feature" :class="feature.class">
              <component :is="feature.icon" :size="26" />
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.text }}</p>
            </article>
          </div>
        </section>

        <section class="connected wrap" data-reveal>
          <p class="kicker">Как всё связано</p>
          <h2>Сайт превращается в управляемую систему</h2>
          <div class="flow">
            <template v-for="(item,index) in platformFlow" :key="item">
              <span>{{ item }}</span>
              <i v-if="index < platformFlow.length - 1" />
            </template>
          </div>
        </section>

        <section id="website" class="website-build">
          <div class="wrap website-layout" data-reveal>
            <div>
              <p class="kicker">Создание сайтов</p>
              <h2>Не просто красивый сайт, а рабочий инструмент для бизнеса</h2>
              <p>Сайт проектируется вокруг задачи: объяснить предложение, принять обращение, передать данные в систему и показать, какие каналы работают.</p>
              <ul>
                <li v-for="item in ['Индивидуальный дизайн', 'Структура под задачи компании', 'Быстрая загрузка', 'Формы заявок', 'SEO-подготовка', 'Аналитика сразу после запуска', 'Telegram-уведомления']" :key="item"><Check :size="16" />{{ item }}</li>
              </ul>
              <p class="price-note">Стоимость рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности.</p>
              <a class="button" href="#contact">Получить оценку проекта</a>
            </div>
            <div class="device-mockup" aria-label="Демонстрационный макет сайта">
              <div class="laptop glass"><span /><b>Главный экран</b><i /><i /><i /></div>
              <div class="phone glass"><span /><b>Форма заявки</b><i /><i /></div>
            </div>
          </div>
        </section>

        <section id="analytics" class="analytics wrap" data-reveal>
          <div>
            <p class="kicker">Аналитика</p>
            <h2>Понимайте, как посетители взаимодействуют с сайтом</h2>
            <p>TrackNode показывает посещаемость, заявки, конверсию, источники трафика, популярные страницы и ключевые действия без неподтвержденных обещаний роста.</p>
          </div>
          <div class="analytics-board glass">
            <div class="metrics"><span>Посещения<b>1 248</b></span><span>Заявки<b>34</b></span><span>Конверсия<b>2.7%</b></span></div>
            <div class="traffic"><i v-for="height in [48, 72, 54, 98, 82, 120, 94, 132]" :key="height" :style="{height:`${height}px`}" /></div>
            <div class="sources"><span>Поиск</span><b /><span>Реклама</span><b /><span>Прямые</span><b /></div>
          </div>
        </section>

        <section id="leads" class="leads wrap" data-reveal>
          <div class="lead-card glass">
            <small>Новая заявка</small><h3>Обсудить сайт</h3>
            <dl><dt>Контакт</dt><dd>Telegram</dd><dt>Источник</dt><dd>SEO-аудит</dd><dt>Статус</dt><dd>Новая</dd><dt>Дата</dt><dd>Сегодня</dd><dt>Комментарий</dt><dd>Нужна оценка проекта</dd></dl>
          </div>
          <div>
            <p class="kicker">Заявки и CRM-направление</p>
            <h2>Единый центр обращений вместо разрозненных сообщений</h2>
            <p>TrackNode сохраняет заявки, источники, статусы и контекст обращения. Если нужна полноценная CRM, интеграцию можно спроектировать отдельно под процесс клиента.</p>
          </div>
        </section>

        <section class="telegram wrap" data-reveal>
          <div>
            <p class="kicker">Telegram-уведомления</p>
            <h2>Новая заявка приходит сразу в Telegram</h2>
            <p>Команда видит обращение без постоянного входа в кабинет и может быстрее перейти к обработке.</p>
          </div>
          <div class="telegram-card glass">
            <MessageSquare :size="26" /><b>TrackNode</b><p>Новая заявка: создание сайта<br>Источник: форма лендинга</p><button type="button">Открыть в кабинете</button>
          </div>
        </section>

        <section id="seo" class="seo wrap" data-reveal>
          <div>
            <p class="kicker">SEO-аудит и конкуренты</p>
            <h2>TrackNode помогает понимать, что улучшать дальше</h2>
            <p>SEO-аудит проверяет техническое состояние, заголовки, description, скорость, мобильную адаптацию и ошибки. Анализ конкурентов показывает различия в структуре, контенте и предложении.</p>
          </div>
          <div class="seo-grid">
            <article class="glass"><FileSearch /><h3>SEO-аудит</h3><p>Оценка, ошибки и рекомендации по страницам.</p></article>
            <article class="glass"><SearchCheck /><h3>Конкуренты</h3><p>Сравнение сайтов и идеи для улучшения.</p></article>
            <article class="glass"><Bot /><h3>AI-рекомендации</h3><p>Идеи по контенту, структуре и продвижению.</p></article>
          </div>
        </section>

        <section id="pricing" class="pricing wrap" data-reveal>
          <div>
            <p class="kicker">Тарифы</p>
            <h2>Подписка TrackNode и индивидуальная разработка</h2>
          </div>
          <div class="pricing-grid">
            <article v-for="plan in plans" :key="plan.title" class="glass plan">
              <h3>{{ plan.title }}</h3><strong>{{ plan.price }} <small>{{ plan.price_suffix || plan.period }}</small></strong><p>{{ plan.description }}</p>
            </article>
            <article class="glass plan custom-price">
              <CircleDollarSign :size="26" /><h3>Разработка сайта</h3><p>Стоимость рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности.</p><a href="#contact">Получить оценку</a>
            </article>
          </div>
        </section>

        <section id="developer" class="developer wrap" data-reveal>
          <div>
            <p class="kicker">Разработчик TrackNode</p>
            <h2>Разработка и развитие платформы - Александр Тишечкин</h2>
            <p>Веб-разработка, сайты, сервисы, автоматизация и аналитические решения.</p>
          </div>
          <a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" class="button secondary" @click="trackPortfolioLink('developer')">Сайт разработчика <ExternalLink :size="16" /></a>
        </section>

        <section id="faq" class="faq wrap" data-reveal>
          <p class="kicker">FAQ</p><h2>Коротко о главном</h2>
          <article v-for="(item,index) in faq" :key="item[0]">
            <button type="button" :aria-expanded="openFaq===index" @click="openFaq=openFaq===index?-1:index"><span>{{ item[0] }}</span><b>{{ openFaq===index ? '-' : '+' }}</b></button>
            <p v-show="openFaq===index">{{ item[1] }}</p>
          </article>
        </section>

        <section id="contact" class="contact">
          <div class="wrap contact-layout">
            <div data-reveal>
              <p class="kicker">Обсудим ваш проект</p><h2>Расскажите, что нужно подключить или создать</h2>
              <p>Можно заказать новый сайт, подключить текущий проект, обсудить управление заявками, CRM-интеграцию, Telegram, аналитику, SEO или конкурентов.</p>
            </div>
            <form class="glass" data-reveal novalidate @submit.prevent="submitLead" @focusin="formStarted">
              <label>Имя<input v-model="form.name" maxlength="255" autocomplete="name" required /></label>
              <label>Телефон<input v-model="form.phone" maxlength="100" autocomplete="tel" /></label>
              <label>Telegram<input v-model="form.telegram" maxlength="100" autocomplete="off" /></label>
              <label>Email<input v-model="form.email" maxlength="255" type="email" autocomplete="email" /></label>
              <label>Тип задачи<select v-model="form.taskType"><option v-for="item in taskTypes" :key="item" :value="item">{{ item }}</option></select></label>
              <label>Есть действующий сайт<select v-model="form.hasExistingSite"><option value="no">Нет</option><option value="yes">Да</option></select></label>
              <label>Адрес сайта<input v-model="form.existingSiteUrl" maxlength="300" placeholder="https://example.ru" /></label>
              <label>Предпочтительный способ связи<select v-model="form.preferredContact"><option value="telegram">Telegram</option><option value="phone">Телефон</option><option value="email">Email</option></select></label>
              <label class="wide-field">Краткое описание<textarea v-model="form.message" maxlength="2000" rows="5" /></label>
              <label class="honeypot" aria-hidden="true">Сайт<input v-model="form.website" tabindex="-1" autocomplete="off" /></label>
              <label class="consent"><input v-model="form.consent" type="checkbox" required /><span>Согласен на обработку персональных данных и принимаю <RouterLink to="/privacy">политику конфиденциальности</RouterLink> и <RouterLink to="/terms">пользовательское соглашение</RouterLink>.</span></label>
              <p v-if="formState.success" class="success" role="status">{{ formState.success }}</p>
              <p v-if="formState.error" class="error" role="alert">{{ formState.error }}</p>
              <button class="button" type="submit" :disabled="formState.submitting">{{ formState.submitting ? 'Отправляем...' : 'Отправить заявку' }}</button>
            </form>
          </div>
        </section>

        <section class="final-cta wrap" data-reveal>
          <div class="glass">
            <h2>Создадим сайт или подключим TrackNode к вашему текущему проекту</h2>
            <div><a class="button" href="#contact">Обсудить проект</a><RouterLink class="button secondary" to="/register">Подключить аналитику</RouterLink></div>
          </div>
        </section>
      </main>

      <footer>
        <div class="wrap footer-inner">
          <div><a class="brand" href="#top"><span>TN</span><strong>TrackNode</strong></a><p>Платформа для создания сайтов, заявок, аналитики, Telegram-уведомлений, SEO-аудита и развития проекта.</p></div>
          <nav>
            <a href="#website">Создание сайтов</a><a href="#analytics">Аналитика</a><a href="#leads">Заявки</a><a href="#features">Telegram</a><a href="#seo">SEO-аудит</a><a href="#seo">Анализ конкурентов</a><a href="#pricing">Тарифы</a><RouterLink to="/terms">Пользовательское соглашение</RouterLink><RouterLink to="/privacy">Политика конфиденциальности</RouterLink><RouterLink to="/login">Вход</RouterLink><RouterLink to="/register">Регистрация</RouterLink><a href="#contact">Контакты</a><a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" @click="trackPortfolioLink('footer')">Сайт разработчика</a>
          </nav>
          <small>© {{ new Date().getFullYear() }} TrackNode</small>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
:global(*){box-sizing:border-box}:global(html){scroll-behavior:smooth;scroll-padding-top:96px}:global(body){margin:0;background:#f6f9fe}.landing{--ink:#101828;--muted:#5d6b82;--line:rgba(119,137,166,.22);--glass:rgba(255,255,255,.72);--soft:#edf4fb;--accent:#3568ff;--cyan:#21a6c7;--green:#16906a;min-height:100vh;overflow-x:hidden;color:var(--ink);background:radial-gradient(circle at 12% 4%,rgba(53,104,255,.12),transparent 30%),radial-gradient(circle at 88% 12%,rgba(33,166,199,.12),transparent 28%),linear-gradient(180deg,#fbfdff,#f4f8fd 46%,#ffffff);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{width:min(calc(100% - 44px),1200px);margin-inline:auto}.glass{border:1px solid rgba(255,255,255,.78);background:var(--glass);box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 24px 80px rgba(28,45,79,.1);backdrop-filter:blur(18px)}.state{display:grid;min-height:100vh;place-content:center;gap:8px;text-align:center}.header{position:fixed;z-index:50;top:14px;left:0;width:100%;pointer-events:none}.nav{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:24px;min-height:66px;padding:0 16px;border:1px solid rgba(255,255,255,.72);border-radius:22px;background:rgba(255,255,255,.76);box-shadow:0 18px 60px rgba(25,45,81,.12);backdrop-filter:blur(18px);pointer-events:auto}.brand{display:inline-flex;align-items:center;gap:10px;color:var(--ink);font-weight:900;text-decoration:none}.brand span{display:grid;width:34px;height:34px;place-items:center;border-radius:11px;color:#fff;background:linear-gradient(135deg,#12203a,#3568ff);font-size:.74rem}.desktop-nav{display:flex;align-items:center;justify-content:center;gap:18px}.desktop-nav a,.nav-actions a,footer a,.ghost-link{color:#536176;text-decoration:none;font-size:.88rem;font-weight:750}.desktop-nav a:hover,.nav-actions a:hover,footer a:hover,.ghost-link:hover{color:var(--accent)}.nav-actions{display:flex;align-items:center;gap:12px}.button{display:inline-flex;min-height:50px;align-items:center;justify-content:center;gap:9px;padding:0 22px;border:0;border-radius:14px;color:#fff;background:linear-gradient(135deg,#13213d,#3568ff);box-shadow:0 16px 36px rgba(53,104,255,.2);font:inherit;font-weight:850;text-decoration:none;transition:transform .22s ease,box-shadow .22s ease}.button:hover{transform:translateY(-2px);box-shadow:0 22px 44px rgba(53,104,255,.26)}.button.secondary{color:#13213d;background:rgba(255,255,255,.76);border:1px solid var(--line);box-shadow:inset 0 1px 0 rgba(255,255,255,.75)}.button.small{min-height:40px;padding-inline:16px;border-radius:12px;font-size:.86rem}.button:disabled{cursor:wait;opacity:.62}.menu-button,.mobile-nav{display:none}.hero{display:grid;grid-template-columns:.9fr 1.1fr;align-items:center;gap:54px;min-height:860px;padding-top:120px}.kicker{margin:0 0 18px;color:var(--accent);font-size:.76rem;font-weight:900;letter-spacing:.11em;text-transform:uppercase}.hero h1,.value h2,.features h2,.connected h2,.website-build h2,.analytics h2,.leads h2,.telegram h2,.seo h2,.pricing h2,.developer h2,.faq h2,.contact h2,.final-cta h2{margin:0;font-size:clamp(2.75rem,5vw,5.55rem);line-height:.98;letter-spacing:-.055em}.lead{max-width:680px;margin:26px 0 0;color:var(--muted);font-size:1.12rem;line-height:1.72}.hero-actions{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-top:34px}.ghost-link{display:inline-flex;align-items:center;gap:6px}.hero-visual{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:16px;min-height:560px;padding:18px;border-radius:34px;background:linear-gradient(145deg,rgba(255,255,255,.4),rgba(232,240,252,.66));box-shadow:0 34px 100px rgba(35,61,102,.16)}.panel{display:grid;align-content:start;gap:8px;min-height:150px;padding:20px;border-radius:24px}.panel small{color:var(--accent);font-weight:900;text-transform:uppercase;font-size:.7rem}.panel b,.panel strong{font-size:1.04rem}.panel span{color:var(--muted);font-size:.88rem}.lead-panel,.chart-panel{transform:translateY(20px)}.telegram-panel{transform:translateY(-10px)}.seo-panel{min-height:180px;text-align:center}.seo-panel strong{font-size:4.4rem;line-height:1;color:var(--green)}.competitors-panel{grid-column:span 2}.bars{display:flex;height:114px;align-items:flex-end;gap:9px}.bars i,.traffic i{flex:1;border-radius:9px 9px 3px 3px;background:linear-gradient(180deg,#3568ff,#8fd5ea)}.value,.features,.connected,.analytics,.leads,.telegram,.seo,.pricing,.developer,.faq,.final-cta{padding-block:110px}.value{text-align:center}.value h2{max-width:880px;margin:auto}.value-line{position:relative;display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:52px;padding:18px;border-radius:28px;background:rgba(255,255,255,.56);border:1px solid var(--line)}.value-line:before{content:"";position:absolute;left:11%;right:11%;top:45px;height:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.34}.value-line article{position:relative;padding:44px 28px}.value-line span{display:grid;width:54px;height:54px;place-items:center;margin:0 auto 20px;border-radius:50%;color:#fff;background:linear-gradient(135deg,#13213d,#3568ff);font-weight:900}.value-line h3{margin:0 0 10px;font-size:1.25rem}.value-line p,.features p,.website-build p,.analytics p,.leads p,.telegram p,.seo p,.pricing p,.developer p,.faq p,.contact p{color:var(--muted);line-height:1.7}.scenarios{display:grid;grid-template-columns:1fr 1fr;gap:22px;padding-block:70px 110px}.scenario{padding:38px;border-radius:30px}.scenario h2{margin:18px 0;font-size:2.1rem;letter-spacing:-.035em}.scenario ul,.website-build ul{display:grid;gap:11px;margin:26px 0;padding:0;list-style:none}.scenario li,.website-build li{display:flex;gap:9px;align-items:center;color:#2d3b52;font-weight:750}.scenario li svg,.website-build li svg{color:var(--green)}.features h2{max-width:850px}.bento{display:grid;grid-template-columns:repeat(6,1fr);grid-auto-rows:minmax(190px,auto);gap:16px;margin-top:48px}.feature{grid-column:span 2;padding:26px;border-radius:26px}.feature.wide{grid-column:span 4}.feature.tall{grid-row:span 2}.feature svg{color:var(--accent)}.feature h3{margin:18px 0 10px;font-size:1.35rem}.connected{text-align:center}.flow{display:flex;align-items:center;justify-content:center;gap:10px;margin-top:46px}.flow span{position:relative;z-index:1;padding:14px 18px;border-radius:999px;background:rgba(255,255,255,.78);border:1px solid var(--line);font-weight:900;box-shadow:0 14px 34px rgba(28,45,79,.08)}.flow i{width:40px;height:2px;background:linear-gradient(90deg,var(--accent),var(--cyan));opacity:.55}.website-build,.contact{padding-block:120px;background:linear-gradient(180deg,rgba(237,244,251,.7),rgba(255,255,255,.92))}.website-layout,.analytics,.leads,.telegram,.seo,.pricing{display:grid;grid-template-columns:.9fr 1.1fr;gap:64px;align-items:center}.price-note{font-weight:850}.device-mockup{position:relative;min-height:410px}.laptop{position:absolute;inset:30px 40px auto 0;height:260px;padding:26px;border-radius:28px}.laptop span,.phone span{display:block;width:62px;height:8px;border-radius:999px;background:#d8e2f1}.laptop b,.phone b{display:block;margin:28px 0 20px;font-size:1.4rem}.laptop i,.phone i{display:block;height:16px;margin-top:13px;border-radius:999px;background:linear-gradient(90deg,#dce7f5,#f8fbff)}.phone{position:absolute;right:0;bottom:0;width:190px;height:300px;padding:22px;border-radius:30px}.analytics-board{padding:28px;border-radius:30px}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.metrics span{padding:16px;border-radius:18px;background:rgba(255,255,255,.68);color:var(--muted);font-size:.85rem}.metrics b{display:block;margin-top:7px;color:var(--ink);font-size:1.4rem}.traffic{display:flex;height:160px;align-items:flex-end;gap:10px;margin:28px 0;padding:20px;border-radius:22px;background:rgba(255,255,255,.58)}.sources{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:center}.sources b{height:9px;border-radius:999px;background:linear-gradient(90deg,#3568ff,#b7cdfd)}.lead-card{padding:30px;border-radius:30px}.lead-card small{color:var(--accent);font-weight:900;text-transform:uppercase}.lead-card h3{font-size:2rem;margin:12px 0 20px}.lead-card dl{display:grid;grid-template-columns:auto 1fr;gap:12px 18px}.lead-card dt{color:var(--muted)}.lead-card dd{margin:0;font-weight:850}.telegram-card{justify-self:end;width:min(100%,430px);padding:30px;border-radius:30px}.telegram-card button{min-height:42px;padding:0 16px;border:0;border-radius:12px;color:#fff;background:#27a7e7;font-weight:850}.seo-grid,.pricing-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.seo-grid article,.plan{padding:26px;border-radius:26px}.seo-grid svg{color:var(--accent);width:28px;height:28px}.plan strong{display:block;margin:18px 0;font-size:2rem}.plan small{font-size:.88rem}.custom-price a{display:inline-flex;margin-top:12px;color:var(--accent);font-weight:900;text-decoration:none}.developer{display:grid;grid-template-columns:1fr auto;gap:30px;align-items:center}.faq article{border-bottom:1px solid var(--line)}.faq button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:18px;padding:24px 0;border:0;background:none;color:var(--ink);text-align:left;font:inherit;font-weight:900}.faq button b{font-size:1.4rem;font-weight:500}.faq p{margin:0 0 24px}.contact-layout{display:grid;grid-template-columns:.8fr 1.2fr;gap:62px;align-items:start}.contact form{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:30px;border-radius:30px}.contact label{display:grid;gap:8px;font-size:.88rem;font-weight:850}.wide-field,.consent,.success,.error,.contact button{grid-column:1/-1}.contact input,.contact textarea,.contact select{width:100%;min-height:50px;padding:13px 14px;border:1px solid rgba(111,130,159,.28);border-radius:14px;color:var(--ink);background:rgba(255,255,255,.74);font:inherit}.contact textarea{min-height:126px;resize:vertical}.contact input:focus,.contact textarea:focus,.contact select:focus{border-color:rgba(53,104,255,.62);outline:3px solid rgba(53,104,255,.13)}.consent{display:flex!important;align-items:flex-start;font-weight:600!important;line-height:1.5}.consent input{width:18px;min-height:18px;flex:0 0 18px}.consent a{color:var(--accent);font-weight:850}.honeypot{position:absolute!important;left:-10000px!important}.success{color:var(--green)}.error{color:#b42318}.final-cta .glass{padding:56px;border-radius:34px;text-align:center;background:linear-gradient(135deg,rgba(255,255,255,.78),rgba(226,238,255,.7))}.final-cta h2{max-width:860px;margin:auto}.final-cta .glass>div{display:flex;justify-content:center;gap:14px;margin-top:30px}footer{padding:56px 0;background:#f8fbff;border-top:1px solid var(--line)}.footer-inner{display:grid;grid-template-columns:.8fr 1.2fr;gap:38px}footer p{max-width:420px;color:var(--muted);line-height:1.65}footer nav{display:flex;flex-wrap:wrap;gap:14px 22px}footer small{grid-column:1/-1;padding-top:22px;border-top:1px solid var(--line);color:#718096}[data-reveal]{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}[data-reveal].is-visible{opacity:1;transform:none}.hero-visual .panel{animation:float-panel 7s ease-in-out infinite}.hero-visual .panel:nth-child(2n){animation-delay:1.2s}@keyframes float-panel{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@media(max-width:1100px){.desktop-nav,.nav-actions{display:none}.nav{grid-template-columns:1fr auto}.menu-button{display:grid;width:42px;height:42px;place-items:center;border:0;border-radius:14px;background:rgba(240,246,255,.9);color:var(--ink)}.mobile-nav{display:grid;position:fixed;top:92px;left:22px;right:22px;gap:0;padding:12px 18px;border:1px solid rgba(255,255,255,.72);border-radius:22px;background:rgba(255,255,255,.92);box-shadow:0 22px 70px rgba(28,45,79,.16);backdrop-filter:blur(18px);pointer-events:auto}.mobile-nav a{padding:12px 4px;color:var(--ink);text-decoration:none;font-weight:850}.hero,.website-layout,.analytics,.leads,.telegram,.seo,.pricing,.contact-layout,.developer,.footer-inner{grid-template-columns:1fr}.hero{min-height:0;padding-top:150px;padding-bottom:70px}.hero-visual{min-height:0}.scenarios{grid-template-columns:1fr}.bento{grid-template-columns:repeat(2,1fr)}.feature,.feature.wide,.feature.tall{grid-column:auto;grid-row:auto}.flow{flex-wrap:wrap}.flow i{width:22px}.seo-grid,.pricing-grid{grid-template-columns:1fr}.telegram-card{justify-self:start}.footer-inner small{grid-column:auto}}
@media(max-width:680px){.wrap{width:min(calc(100% - 28px),1200px)}.header{top:8px}.nav{min-height:60px;border-radius:18px}.mobile-nav{top:76px;left:14px;right:14px}.hero h1,.value h2,.features h2,.connected h2,.website-build h2,.analytics h2,.leads h2,.telegram h2,.seo h2,.pricing h2,.developer h2,.faq h2,.contact h2,.final-cta h2{font-size:clamp(2.35rem,12vw,3.45rem)}.hero-actions,.final-cta .glass>div{display:grid}.hero-visual,.value-line,.bento,.metrics,.contact form{grid-template-columns:1fr}.competitors-panel{grid-column:auto}.value-line article{padding:28px 20px}.value-line:before{display:none}.value,.features,.connected,.website-build,.analytics,.leads,.telegram,.seo,.pricing,.developer,.faq,.final-cta{padding-block:78px}.scenarios{padding-block:40px 78px}.device-mockup{min-height:330px}.laptop{left:0;right:20px;height:220px}.phone{width:150px;height:240px}.contact form{padding:22px}.wide-field,.consent,.success,.error,.contact button{grid-column:auto}.flow{display:grid;grid-template-columns:1fr}.flow i{width:2px;height:18px;margin:auto}.footer-inner{gap:26px}}
@media(prefers-reduced-motion:reduce){:global(html){scroll-behavior:auto}[data-reveal]{opacity:1;transform:none;transition:none}.button,.hero-visual .panel{transition:none;animation:none}}

/* TrackNode landing refresh: header + hero */
:global(html){scroll-padding-top:94px}
:global(body){background:#f7faff}
.landing{
  --ink:#10254a;
  --muted:#52678d;
  --line:rgba(145,161,190,.24);
  --glass:rgba(255,255,255,.82);
  --soft:#f3f7ff;
  --accent:#246bfd;
  --accent-2:#2f6df6;
  --cyan:#70d9ff;
  color:var(--ink);
  background:
    radial-gradient(circle at 72% 44%, rgba(36,107,253,.12), transparent 34%),
    radial-gradient(circle at 88% 72%, rgba(112,217,255,.16), transparent 28%),
    linear-gradient(180deg,#fff 0%,#f8fbff 58%,#fff 100%);
}
.wrap{width:min(calc(100% - 96px),1460px)}
.header{
  position:fixed;
  top:0;
  left:0;
  z-index:50;
  width:100%;
  border-bottom:1px solid rgba(143,160,190,.18);
  background:rgba(255,255,255,.88);
  box-shadow:0 1px 0 rgba(255,255,255,.92);
  backdrop-filter:blur(18px);
  pointer-events:auto;
}
.nav{
  min-height:88px;
  padding:0;
  border:0;
  border-radius:0;
  background:transparent;
  box-shadow:none;
  backdrop-filter:none;
}
.brand{
  gap:14px;
  color:#0d2148;
  font-size:1.54rem;
  letter-spacing:0;
}
.brand-mark{
  position:relative;
  display:block;
  width:36px;
  height:36px;
  flex:0 0 36px;
  border-radius:0;
  background:none;
  box-shadow:none;
}
.brand-mark i{
  position:absolute;
  width:7px;
  height:7px;
  border-radius:50%;
  background:linear-gradient(135deg,#61a1ff,#246bfd);
  box-shadow:0 0 0 3px rgba(36,107,253,.08);
}
.brand-mark i:nth-child(1){left:3px;top:15px}
.brand-mark i:nth-child(2){left:13px;top:4px}
.brand-mark i:nth-child(3){left:26px;top:8px}
.brand-mark i:nth-child(4){left:17px;top:17px}
.brand-mark i:nth-child(5){left:28px;top:25px}
.brand-mark i:nth-child(6){left:9px;top:29px}
.brand-mark i:nth-child(7){left:1px;top:2px}
.brand-mark:before,
.brand-mark:after{
  content:"";
  position:absolute;
  height:1px;
  background:rgba(36,107,253,.54);
  transform-origin:left center;
}
.brand-mark:before{left:8px;top:17px;width:22px;transform:rotate(-31deg)}
.brand-mark:after{left:16px;top:20px;width:18px;transform:rotate(31deg)}
.desktop-nav{gap:36px}
.desktop-nav a{
  color:#001b5a;
  font-size:.93rem;
  font-weight:600;
}
.desktop-nav a:hover{color:var(--accent)}
.nav-actions{gap:22px}
.nav-actions .login{
  display:inline-flex;
  min-height:44px;
  align-items:center;
  justify-content:center;
  padding:0 28px;
  border:1px solid rgba(151,165,190,.28);
  border-radius:12px;
  color:#001b5a;
  background:rgba(255,255,255,.7);
  font-weight:700;
}
.button{
  min-height:52px;
  border-radius:12px;
  background:linear-gradient(135deg,#246bfd,#1454ed);
  box-shadow:0 14px 30px rgba(36,107,253,.18);
  font-weight:700;
}
.button:hover{
  transform:translateY(-1px);
  box-shadow:0 18px 34px rgba(36,107,253,.22);
}
.button.small{
  min-height:44px;
  padding-inline:28px;
  border-radius:12px;
  font-size:.93rem;
}
.button.secondary{
  color:#10254a;
  background:rgba(255,255,255,.78);
  border:1px solid rgba(146,162,191,.27);
  box-shadow:0 12px 26px rgba(28,45,79,.06);
}
.hero{
  grid-template-columns:minmax(0,.43fr) minmax(0,.57fr);
  gap:36px;
  min-height:100vh;
  padding-top:132px;
  padding-bottom:72px;
}
.hero-copy{
  position:relative;
  z-index:2;
}
.kicker{
  display:inline-flex;
  width:max-content;
  max-width:100%;
  align-items:center;
  gap:8px;
  margin:0 0 48px;
  padding:9px 13px;
  border:1px solid rgba(146,162,191,.27);
  border-radius:999px;
  color:#27477d;
  background:rgba(255,255,255,.72);
  box-shadow:0 10px 30px rgba(45,67,109,.05);
  font-size:.84rem;
  font-weight:600;
  letter-spacing:0;
  text-transform:none;
}
.kicker svg{color:var(--accent)}
.hero h1{
  display:grid;
  gap:4px;
  margin:0;
  color:#10254a;
  font-size:4.7rem;
  line-height:1.06;
  letter-spacing:0;
  font-weight:800;
}
.accent-text{
  color:var(--accent);
  background:linear-gradient(90deg,#246bfd,#5e8dff);
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
}
.lead{
  max-width:560px;
  margin:28px 0 0;
  color:#405984;
  font-size:1.15rem;
  line-height:1.62;
}
.hero-actions{
  gap:18px;
  margin-top:36px;
}
.hero-visual{
  position:relative;
  display:grid;
  min-height:640px;
  place-items:center;
  padding:0;
  border-radius:0;
  background:none;
  box-shadow:none;
  overflow:visible;
}
.compass-img{
  position:relative;
  z-index:2;
  width:clamp(460px,48vw,780px);
  max-width:100%;
  height:auto;
  object-fit:contain;
  filter:drop-shadow(0 34px 62px rgba(34,58,98,.2)) drop-shadow(0 0 22px rgba(36,107,253,.16));
  animation:compass-float 7.5s ease-in-out infinite;
  transition:transform .5s ease, filter .5s ease;
}
.hero-visual:hover .compass-img{
  transform:translate3d(0,-4px,0) scale(1.01);
  filter:drop-shadow(0 40px 70px rgba(34,58,98,.23)) drop-shadow(0 0 28px rgba(36,107,253,.2));
}
.orbit{
  position:absolute;
  z-index:1;
  border:1px solid rgba(87,169,255,.22);
  border-radius:50%;
  pointer-events:none;
}
.orbit-one{width:82%;aspect-ratio:1.45/1;transform:rotate(-8deg)}
.orbit-two{width:96%;aspect-ratio:1.7/1;transform:rotate(13deg)}
.orbit-dot{
  position:absolute;
  z-index:1;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#c7f1ff;
  box-shadow:0 0 0 5px rgba(112,217,255,.18);
}
.dot-a{right:5%;top:43%}
.dot-b{left:12%;top:45%}
.dot-c{right:27%;bottom:11%}
.compass-label{
  position:absolute;
  z-index:3;
  display:grid;
  justify-items:center;
  gap:8px;
  color:#10254a;
  font-size:.92rem;
  font-weight:600;
  text-align:center;
}
.compass-label:before{
  content:"";
  position:absolute;
  top:34px;
  width:92px;
  height:1px;
  background:linear-gradient(90deg,rgba(36,107,253,.42),rgba(36,107,253,0));
  border-top:1px dashed rgba(36,107,253,.28);
}
.compass-label span{
  display:grid;
  width:68px;
  height:68px;
  place-items:center;
  border:1px solid rgba(146,162,191,.2);
  border-radius:50%;
  color:var(--accent);
  background:rgba(255,255,255,.84);
  box-shadow:0 18px 42px rgba(31,54,96,.08);
  backdrop-filter:blur(12px);
}
.compass-label b{font-weight:600}
.label-sites{left:8%;top:5%}
.label-sites:before{left:54px;transform:rotate(36deg)}
.label-analytics{right:1%;top:12%}
.label-analytics:before{right:54px;transform:rotate(145deg)}
.label-crm{left:2%;bottom:20%}
.label-crm:before{left:58px;transform:rotate(-18deg)}
.label-seo{left:45%;bottom:0}
.label-seo:before{left:34px;top:-18px;transform:rotate(-84deg)}
.label-telegram{right:4%;bottom:13%}
.label-telegram:before{right:56px;transform:rotate(202deg)}
.value{
  margin-top:0;
  padding-top:80px;
}
@keyframes compass-float{
  0%,100%{transform:translate3d(0,0,0)}
  50%{transform:translate3d(0,-7px,0)}
}
@media(max-width:1180px){
  .desktop-nav,.nav-actions{display:none}
  .nav{grid-template-columns:1fr auto}
  .menu-button{
    display:grid;
    width:44px;
    height:44px;
    place-items:center;
    border:1px solid rgba(146,162,191,.24);
    border-radius:12px;
    color:#10254a;
    background:rgba(255,255,255,.74);
  }
  .mobile-nav{
    display:grid;
    position:fixed;
    top:92px;
    left:24px;
    right:24px;
    gap:0;
    padding:12px 18px;
    border:1px solid rgba(146,162,191,.22);
    border-radius:18px;
    background:rgba(255,255,255,.94);
    box-shadow:0 22px 70px rgba(28,45,79,.14);
    backdrop-filter:blur(18px);
    pointer-events:auto;
  }
  .mobile-nav a{
    padding:12px 4px;
    color:#10254a;
    text-decoration:none;
    font-weight:700;
  }
  .hero{
    grid-template-columns:1fr;
    min-height:0;
    padding-top:140px;
  }
  .hero h1{font-size:4.05rem}
  .hero-visual{min-height:560px}
  .compass-img{width:min(720px,92vw)}
}
@media(max-width:760px){
  .wrap{width:min(calc(100% - 32px),1460px)}
  .header{background:rgba(255,255,255,.94)}
  .nav{min-height:72px}
  .brand{font-size:1.18rem}
  .brand-mark{width:32px;height:32px;flex-basis:32px}
  .mobile-nav{top:80px;left:16px;right:16px}
  .hero{
    gap:32px;
    padding-top:112px;
    padding-bottom:56px;
  }
  .kicker{
    width:auto;
    margin-bottom:28px;
    font-size:.78rem;
  }
  .hero h1{
    font-size:3.05rem;
    line-height:1.08;
  }
  .lead{
    font-size:1rem;
    line-height:1.58;
  }
  .hero-actions{
    display:grid;
    align-items:stretch;
  }
  .hero-actions .button{width:100%}
  .hero-visual{
    min-height:auto;
    padding:8px 0 4px;
  }
  .compass-img{width:100%}
  .orbit,.orbit-dot,.compass-label{display:none}
}
@media(max-width:420px){
  .wrap{width:min(calc(100% - 24px),1460px)}
  .hero h1{font-size:2.55rem}
  .button{padding-inline:18px}
}
@media(prefers-reduced-motion:reduce){
  .compass-img{animation:none;transition:none}
}

.brand .brand-mark{
  position:relative;
  display:block;
  width:36px;
  height:36px;
  flex:0 0 36px;
  border-radius:0;
  color:inherit;
  background:transparent;
  box-shadow:none;
}
.brand .brand-mark i{display:block}
.compass-img{
  width:clamp(760px,60vw,1060px);
  max-width:none;
}
@media(max-width:1180px){
  .compass-img{
    width:min(880px,110vw);
    max-width:none;
  }
}
@media(max-width:760px){
  .brand .brand-mark{width:32px;height:32px;flex-basis:32px}
  .compass-img{
    width:100%;
    max-width:100%;
  }
}

.hero-compass-stage{
  position:relative;
  display:grid;
  width:clamp(720px,52vw,900px);
  max-width:calc(100vw - 48px);
  aspect-ratio:1.32/1;
  place-items:center;
  overflow:visible;
}
.hero-compass-stage .compass-img{
  z-index:3;
  width:90%;
  max-width:none;
}
.hero-compass-stage .orbit{
  z-index:1;
  opacity:.74;
}
.hero-compass-stage .orbit-one{
  width:78%;
  aspect-ratio:1.55/1;
}
.hero-compass-stage .orbit-two{
  width:92%;
  aspect-ratio:1.72/1;
}
.hero-compass-stage .orbit-dot{z-index:2}
.hero-compass-stage .dot-a{right:8%;top:44%}
.hero-compass-stage .dot-b{left:11%;top:46%}
.hero-compass-stage .dot-c{right:26%;bottom:13%}
.hero-compass-stage .compass-label{
  z-index:4;
  gap:7px;
  min-width:92px;
  transform:translate(-50%,-50%);
}
.hero-compass-stage .compass-label span{
  width:58px;
  height:58px;
  box-shadow:0 16px 34px rgba(31,54,96,.07);
}
.hero-compass-stage .compass-label:before{
  z-index:0;
  top:28px;
  width:70px;
  opacity:.42;
  pointer-events:none;
}
.hero-compass-stage .label-sites{left:50%;top:5%}
.hero-compass-stage .label-sites:before{left:62px;transform:rotate(28deg)}
.hero-compass-stage .label-analytics{left:91%;top:25%}
.hero-compass-stage .label-analytics:before{right:60px;transform:rotate(154deg)}
.hero-compass-stage .label-crm{left:9%;top:63%}
.hero-compass-stage .label-crm:before{left:60px;transform:rotate(-20deg)}
.hero-compass-stage .label-telegram{left:91%;top:73%}
.hero-compass-stage .label-telegram:before{right:60px;transform:rotate(204deg)}
.hero-compass-stage .label-seo{left:50%;top:97%}
.hero-compass-stage .label-seo:before{
  left:50%;
  top:-38px;
  width:54px;
  transform:translateX(-50%) rotate(-90deg);
}
@media(min-width:1181px){
  .hero-visual{
    min-height:700px;
  }
}
@media(max-width:1180px){
  .hero-compass-stage{
    width:min(860px,calc(100vw - 48px));
    aspect-ratio:1.28/1;
    margin-left:0;
  }
  .hero-compass-stage .compass-img{
    width:78%;
  }
  .hero-compass-stage .compass-label span{
    width:54px;
    height:54px;
  }
  .hero-compass-stage .compass-label:before{
    width:52px;
    opacity:.3;
  }
  .hero-compass-stage .label-sites{top:7%}
  .hero-compass-stage .label-analytics{left:92%;top:28%}
  .hero-compass-stage .label-crm{left:8%;top:64%}
  .hero-compass-stage .label-telegram{left:92%;top:73%}
  .hero-compass-stage .label-seo{top:95%}
}
@media(max-width:900px){
  .hero-compass-stage{
    width:min(760px,calc(100vw - 32px));
    aspect-ratio:1.12/1;
  }
  .hero-compass-stage .compass-img{
    width:76%;
  }
  .hero-compass-stage .compass-label:before,
  .hero-compass-stage .orbit-dot{
    display:none;
  }
  .hero-compass-stage .label-sites{top:8%}
  .hero-compass-stage .label-analytics{left:91%;top:30%}
  .hero-compass-stage .label-crm{left:9%;top:67%}
  .hero-compass-stage .label-telegram{left:91%;top:74%}
  .hero-compass-stage .label-seo{top:95%}
}
@media(max-width:760px){
  .hero-compass-stage{
    width:100%;
    aspect-ratio:auto;
  }
  .hero-compass-stage .compass-img{
    width:100%;
    max-width:100%;
  }
}

@media(min-width:1181px){
  .hero-compass-stage{margin-left:clamp(-90px,-5vw,-48px)}
}
</style>
