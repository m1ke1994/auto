<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  ArrowRight,
  BarChart3,
  Check,
  Code2,
  ExternalLink,
  FileSearch,
  LayoutDashboard,
  Menu,
  Send,
  Sparkles,
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
  hasExistingSite: 'no',
  existingSiteUrl: '',
  siteType: '',
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

const capabilities = [
  ['Аналитика сайта', BarChart3],
  ['Заявки и источники обращений', Send],
  ['Управление сайтом и контентом', LayoutDashboard],
  ['SEO-аудит', FileSearch],
  ['Анализ конкурентов', BarChart3],
  ['AI-рекомендации', Sparkles],
  ['Telegram-уведомления', Send],
  ['Отчеты и подписка', LayoutDashboard],
]

const processSteps = [
  'Знакомство и обсуждение задачи',
  'Сбор требований',
  'Подготовка структуры',
  'Разработка индивидуального дизайна',
  'Создание и адаптация сайта',
  'Подключение форм и домена',
  'Подключение аналитики TrackNode',
  'Запуск и передача доступа',
]

const projects = [
  {
    title: 'TrackNode',
    category: 'Платформа',
    image: '/images/landing/cube.png',
    text: 'Сервис для аналитики, заявок, SEO-аудита, AI-рекомендаций и управления сайтами.',
    href: 'https://tracknode.ru/',
  },
  {
    title: 'A Meditation',
    category: 'Публичный сайт',
    image: '/images/landing/cube.png',
    text: 'Сайт проекта leelabird.ru с управлением контентом и медиа через TrackNode.',
    href: 'https://leelabird.ru/',
  },
  {
    title: 'Новое Конаково',
    category: 'Многостраничный сайт',
    image: '/images/landing/cube.png',
    text: 'Публичный сайт проекта novoe-konakovo.ru с контентом и аналитикой.',
    href: 'https://novoe-konakovo.ru/',
  },
  {
    title: 'Сайт разработчика Александра Тишечкина',
    category: 'Портфолио',
    image: '/images/landing/cube.png',
    text: 'Персональное портфолио, опыт, технологии и примеры работ разработчика.',
    href: PORTFOLIO_URL,
  },
]

const faq = [
  ['Можно ли заказать только разработку сайта?', 'Да. TrackNode может быть частью проекта, но разработку сайта можно обсудить как отдельную услугу.'],
  ['Можно ли подключить TrackNode к существующему сайту?', 'Да. Для этого добавляется аналитический скрипт, после чего данные отображаются в личном кабинете.'],
  ['Будет ли дизайн уникальным?', 'Да, дизайн готовится под задачу проекта. При желании можно использовать готовый макет или дизайн-систему.'],
  ['Смогу ли я редактировать сайт самостоятельно?', 'Если сайт размещен на платформе TrackNode, контент можно редактировать через личный кабинет.'],
  ['Входит ли аналитика в разработку?', 'Аналитику можно подключить сразу при запуске нового сайта или отдельно к существующему проекту.'],
  ['Как рассчитывается стоимость?', 'Стоимость разработки рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности проекта.'],
  ['Сколько времени занимает разработка?', 'Срок зависит от объема проекта, количества страниц, функциональности и требований к дизайну.'],
  ['Можно ли доработать сайт после запуска?', 'Да. После запуска можно развивать контент, функциональность, аналитику и SEO.'],
  ['Какие данные собирает аналитика?', 'Посещения, просмотры страниц, источники переходов, технические события и отправки форм без передачи лишних персональных данных.'],
  ['Где посмотреть примеры работ?', 'Часть проектов показана на этой странице, больше контекста есть на сайте разработчика Александра Тишечкина.'],
  ['Кто занимается разработкой проектов?', 'Разработкой и развитием проектов занимается Александр Тишечкин. Его портфолио: https://tishechkinalexandr.ru/.'],
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
  track('lead_form_started', { placement: 'website_order' })
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
      email: sanitize(form.email),
      message: sanitize(form.message),
      source_url: window.location.href,
      section_key: 'website-order',
      form_name: 'Обсудить создание сайта',
      service_type: 'tracknode_website_order',
      service_title: sanitize(form.siteType) || 'Разработка сайта / подключение аналитики',
      consent: form.consent,
      website: sanitize(form.website),
      payload: {
        source: 'tracknode_website_order',
        consent_at: new Date().toISOString(),
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
    Object.assign(form, { name: '', phone: '', telegram: '', email: '', hasExistingSite: 'no', existingSiteUrl: '', siteType: '', message: '', preferredContact: 'telegram', consent: false, website: '' })
    formState.success = 'Заявка отправлена. Я свяжусь с вами выбранным способом.'
    track('lead_form_success', { source: 'tracknode_website_order' })
  } catch (error) {
    formState.error = error?.message || 'Не удалось отправить заявку. Проверьте поля и попробуйте еще раз.'
    track('lead_form_error', { source: 'tracknode_website_order' })
  } finally {
    formState.submitting = false
  }
}

function closeMenu() { menuOpen.value = false }

function setupReveal() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => entry.isIntersecting && entry.target.classList.add('is-visible'))
  }, { threshold: 0.12 })
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
        title: 'TrackNode - разработка сайтов с уникальным дизайном и аналитикой',
        description: 'TrackNode помогает создать сайт под заказ или подключить аналитику, заявки, SEO-аудит, конкурентов и AI-рекомендации к существующему сайту.',
        canonical: 'https://tracknode.ru/',
        og_title: 'TrackNode - сайты под заказ и встроенная бизнес-аналитика',
        og_description: 'Создание сайтов, подключение аналитики TrackNode, заявки, SEO-аудит, конкуренты и AI-рекомендации в одном кабинете.',
        og_image: 'https://tracknode.ru/og-image.svg',
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
          <a class="brand" href="#top" @click="closeMenu"><span>TN</span>TrackNode</a>
          <div class="desktop-nav">
            <a href="#services">Услуги</a><a href="#platform">Платформа</a><a href="#projects">Проекты</a><a href="#pricing">Тарифы</a><a href="#faq">FAQ</a>
          </div>
          <div class="nav-actions">
            <RouterLink to="/login">Войти</RouterLink>
            <RouterLink to="/register" class="button small">Регистрация</RouterLink>
          </div>
          <button class="menu-button" type="button" :aria-expanded="menuOpen" aria-label="Открыть меню" @click="menuOpen = !menuOpen"><X v-if="menuOpen" /><Menu v-else /></button>
        </nav>
        <div v-if="menuOpen" class="mobile-nav">
          <a href="#services" @click="closeMenu">Услуги</a><a href="#platform" @click="closeMenu">Платформа</a><a href="#projects" @click="closeMenu">Проекты</a><a href="#contact" @click="closeMenu">Контакты</a><RouterLink to="/login">Войти</RouterLink>
        </div>
      </header>

      <main id="top">
        <section class="hero wrap">
          <div class="hero-copy" data-reveal>
            <p class="kicker">Сайты и аналитика в одной системе</p>
            <h1>Создадим сайт с уникальным дизайном и сразу подключим аналитику</h1>
            <p class="lead">TrackNode объединяет разработку сайтов, заявки, веб-аналитику, SEO-аудит, анализ конкурентов и AI-рекомендации в личном кабинете.</p>
            <div class="hero-actions">
              <a class="button" href="#contact" @click="track('website_order_cta_click', { placement: 'hero' })">Заказать разработку сайта <ArrowRight :size="18" /></a>
              <RouterLink class="button secondary" to="/register" @click="track('analytics_connect_cta_click', { placement: 'hero' })">Подключить аналитику</RouterLink>
            </div>
            <a class="portfolio-link" :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" @click="trackPortfolioLink('hero')">Портфолио Александра Тишечкина <ExternalLink :size="16" /></a>
          </div>
          <div class="system-map" data-reveal aria-label="Сайт, заявки, аналитика и улучшение результата">
            <div>Сайт</div><ArrowRight /><div>Заявки</div><ArrowRight /><div>Аналитика</div><ArrowRight /><div>Улучшение результата</div>
          </div>
        </section>

        <section id="services" class="wrap split" data-reveal>
          <article>
            <Code2 :size="34" /><h2>Нужен новый сайт</h2>
            <p>Проектирование структуры, индивидуальный дизайн, frontend и backend при необходимости, формы заявок, домен, техническая SEO-подготовка и подключение TrackNode при запуске.</p>
            <ul><li v-for="item in ['Уникальный дизайн', 'Мобильная адаптация', 'Управление контентом', 'Формы заявок', 'Аналитика TrackNode']" :key="item"><Check :size="16" />{{ item }}</li></ul>
            <a class="button" href="#contact">Обсудить создание сайта</a>
          </article>
          <article>
            <BarChart3 :size="34" /><h2>Сайт уже работает</h2>
            <p>Подключим TrackNode через аналитический скрипт: посещения, просмотры страниц, источники, действия, заявки, SEO-аудит, конкуренты, AI-рекомендации и отчеты.</p>
            <ul><li v-for="item in ['Статистика посещений', 'Отслеживание заявок', 'SEO-аудит', 'Анализ конкурентов', 'Единый кабинет']" :key="item"><Check :size="16" />{{ item }}</li></ul>
            <RouterLink class="button secondary" to="/register">Подключить мой сайт</RouterLink>
          </article>
        </section>

        <section class="process">
          <div class="wrap" data-reveal>
            <p class="kicker">Процесс</p><h2>Этапы разработки сайта</h2>
            <ol><li v-for="step in processSteps" :key="step">{{ step }}</li></ol>
            <p class="note">Срок и стоимость зависят от объема проекта, количества страниц, функциональности и требований к дизайну.</p>
          </div>
        </section>

        <section id="platform" class="wrap capabilities" data-reveal>
          <p class="kicker">Возможности TrackNode</p><h2>Один кабинет для сайта, заявок и роста</h2>
          <div class="capability-grid"><article v-for="[label, Icon] in capabilities" :key="label"><Icon :size="22" /><span>{{ label }}</span></article></div>
        </section>

        <section id="projects" class="projects">
          <div class="wrap" data-reveal>
            <p class="kicker">Примеры работ</p><h2>Реальные проекты</h2>
            <div class="project-grid">
              <article v-for="project in projects" :key="project.title">
                <img :src="project.image" :alt="project.title" loading="lazy" width="520" height="320" />
                <span>{{ project.category }}</span><h3>{{ project.title }}</h3><p>{{ project.text }}</p>
                <a :href="project.href" target="_blank" rel="noopener noreferrer" @click="project.href === PORTFOLIO_URL && trackPortfolioLink('projects')">Смотреть проект <ExternalLink :size="15" /></a>
              </article>
            </div>
          </div>
        </section>

        <section class="developer wrap" data-reveal>
          <div><p class="kicker">Кто разрабатывает проекты</p><h2>Александр Тишечкин</h2></div>
          <p>Веб-разработка, создание сайтов, frontend и backend, интеграции, аналитические системы, автоматизация и развитие TrackNode.</p>
          <a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" class="button secondary" @click="trackPortfolioLink('developer')">Посмотреть сайт разработчика и портфолио</a>
        </section>

        <section id="pricing" class="pricing wrap" data-reveal>
          <div><p class="kicker">Стоимость</p><h2>Подписка TrackNode и разработка сайта</h2></div>
          <div class="plans" v-if="plans.length"><article v-for="plan in plans" :key="plan.title"><h3>{{ plan.title }}</h3><strong>{{ plan.price }} <small>{{ plan.price_suffix || plan.period }}</small></strong><p>{{ plan.description }}</p></article></div>
          <article class="custom-price"><h3>Разработка сайта под заказ</h3><p>Стоимость разработки рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности проекта.</p><a class="button" href="#contact">Получить предварительную оценку</a></article>
        </section>

        <section id="faq" class="faq wrap" data-reveal>
          <p class="kicker">FAQ</p><h2>Ответы на частые вопросы</h2>
          <article v-for="(item,index) in faq" :key="item[0]"><button type="button" :aria-expanded="openFaq===index" @click="openFaq=openFaq===index?-1:index"><span>{{ item[0] }}</span><b>{{ openFaq===index ? '-' : '+' }}</b></button><p v-show="openFaq===index">{{ item[1] }}</p></article>
        </section>

        <section id="contact" class="contact">
          <div class="wrap contact-layout">
            <div data-reveal><p class="kicker">Обсудить создание сайта</p><h2>Расскажите о задаче</h2><p>Не нужно заполнять все контакты: достаточно телефона, Telegram или email.</p></div>
            <form data-reveal novalidate @submit.prevent="submitLead" @focusin="formStarted">
              <label>Имя<input v-model="form.name" maxlength="255" autocomplete="name" required /></label>
              <label>Телефон<input v-model="form.phone" maxlength="100" autocomplete="tel" /></label>
              <label>Telegram<input v-model="form.telegram" maxlength="100" autocomplete="off" /></label>
              <label>Email<input v-model="form.email" maxlength="255" type="email" autocomplete="email" /></label>
              <label>Есть ли действующий сайт<select v-model="form.hasExistingSite"><option value="no">Нет</option><option value="yes">Да</option></select></label>
              <label>Адрес действующего сайта<input v-model="form.existingSiteUrl" maxlength="300" placeholder="https://example.ru" /></label>
              <label>Тип будущего сайта<input v-model="form.siteType" maxlength="255" placeholder="Лендинг, корпоративный сайт, сервис" /></label>
              <label>Краткое описание задачи<textarea v-model="form.message" maxlength="2000" rows="5" /></label>
              <label>Предпочтительный способ связи<select v-model="form.preferredContact"><option value="telegram">Telegram</option><option value="phone">Телефон</option><option value="email">Email</option></select></label>
              <label class="honeypot" aria-hidden="true">Сайт<input v-model="form.website" tabindex="-1" autocomplete="off" /></label>
              <label class="consent"><input v-model="form.consent" type="checkbox" required /><span>Согласен на обработку персональных данных.</span></label>
              <p v-if="formState.success" class="success" role="status">{{ formState.success }}</p>
              <p v-if="formState.error" class="error" role="alert">{{ formState.error }}</p>
              <button class="button" type="submit" :disabled="formState.submitting">{{ formState.submitting ? 'Отправляем...' : 'Отправить заявку' }}</button>
            </form>
          </div>
        </section>
      </main>

      <footer>
        <div class="wrap footer-inner">
          <a class="brand" href="#top"><span>TN</span>TrackNode</a>
          <nav>
            <a href="#services">Разработка сайтов</a><a href="#platform">Аналитика</a><a href="#pricing">Тарифы</a><a href="#projects">Примеры работ</a><a href="#faq">FAQ</a><RouterLink to="/terms">Пользовательское соглашение</RouterLink><RouterLink to="/privacy">Политика конфиденциальности</RouterLink><RouterLink to="/login">Вход</RouterLink><RouterLink to="/register">Регистрация</RouterLink><a :href="PORTFOLIO_URL" target="_blank" rel="noopener noreferrer" @click="trackPortfolioLink('footer')">Сайт разработчика</a>
          </nav>
          <small>© {{ new Date().getFullYear() }} TrackNode</small>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
:global(*){box-sizing:border-box}:global(html){scroll-behavior:smooth;scroll-padding-top:92px}:global(body){margin:0;background:#f8fafc}.landing{--ink:#101525;--muted:#5f687a;--line:#e3e7ef;--soft:#f4f7fb;--accent:#275de8;--green:#138a62;min-height:100vh;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{width:min(calc(100% - 40px),1180px);margin-inline:auto}.state{display:grid;min-height:100vh;place-content:center;gap:8px;text-align:center}.header{position:fixed;z-index:50;top:0;width:100%;border-bottom:1px solid rgba(16,21,37,.08);background:rgba(255,255,255,.92);backdrop-filter:blur(16px)}.nav{display:grid;grid-template-columns:auto 1fr auto;align-items:center;min-height:74px;gap:28px}.brand{display:inline-flex;align-items:center;gap:10px;color:var(--ink);font-weight:800;text-decoration:none}.brand span{display:grid;width:34px;height:34px;place-items:center;border-radius:8px;color:#fff;background:var(--ink);font-size:.75rem}.desktop-nav,.nav-actions,footer nav{display:flex;align-items:center;gap:22px}.desktop-nav a,.nav-actions a,footer a,.portfolio-link{color:#445064;text-decoration:none;font-size:.9rem;font-weight:700}.desktop-nav a:hover,.nav-actions a:hover,footer a:hover,.portfolio-link:hover{color:var(--accent)}.button{display:inline-flex;min-height:50px;align-items:center;justify-content:center;gap:8px;padding:0 22px;border:0;border-radius:8px;color:#fff;background:var(--ink);box-shadow:0 16px 34px rgba(16,21,37,.14);font:inherit;font-weight:800;text-decoration:none;transition:transform .2s,background .2s}.button:hover{background:#27314a;transform:translateY(-2px)}.button.secondary{color:var(--ink);background:#fff;border:1px solid var(--line);box-shadow:none}.button.small{min-height:40px;padding-inline:16px}.button:disabled{cursor:wait;opacity:.65}.menu-button,.mobile-nav{display:none}.hero{display:grid;grid-template-columns:1fr .95fr;gap:64px;align-items:center;min-height:820px;padding-top:110px}.kicker{margin:0 0 18px;color:var(--accent);font-size:.76rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase}.hero h1,.process h2,.capabilities h2,.projects h2,.developer h2,.pricing h2,.faq h2,.contact h2{margin:0;font-size:clamp(2.7rem,5vw,5.4rem);line-height:1;letter-spacing:-.055em}.lead{max-width:650px;margin:26px 0 0;color:var(--muted);font-size:1.12rem;line-height:1.7}.hero-actions{display:flex;flex-wrap:wrap;gap:16px;margin-top:34px}.portfolio-link{display:inline-flex;align-items:center;gap:7px;margin-top:22px}.system-map{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center;padding:34px;border:1px solid var(--line);border-radius:8px;background:#fff;box-shadow:0 34px 90px rgba(16,21,37,.12)}.system-map div{min-height:96px;display:grid;place-items:center;border-radius:8px;background:var(--soft);font-weight:900;text-align:center}.system-map svg{color:var(--accent)}.split{display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:100px 0}.split article,.custom-price,.plans article{padding:34px;border:1px solid var(--line);border-radius:8px;background:#fff}.split h2,.custom-price h3{font-size:2rem;letter-spacing:-.03em}.split p,.developer p,.custom-price p{color:var(--muted);line-height:1.7}.split ul{display:grid;gap:10px;margin:24px 0;padding:0;list-style:none}.split li{display:flex;gap:9px;align-items:center}.split li svg{color:var(--green)}.process,.projects,.contact{padding:110px 0;background:#eef3f8}.process ol{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:44px 0 0;padding:0;list-style:none}.process li{padding:20px;border-radius:8px;background:#fff;font-weight:800}.note{color:var(--muted)}.capabilities{padding:110px 0}.capability-grid,.project-grid,.plans{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:42px}.capability-grid article{display:flex;gap:12px;align-items:center;min-height:88px;padding:18px;border:1px solid var(--line);border-radius:8px;background:#fff;font-weight:800}.capability-grid svg{color:var(--accent)}.project-grid{grid-template-columns:repeat(4,1fr)}.project-grid article{overflow:hidden;border:1px solid var(--line);border-radius:8px;background:#fff}.project-grid img{display:block;width:100%;height:170px;object-fit:cover;background:#dfe6f1}.project-grid span,.project-grid h3,.project-grid p,.project-grid a{margin-inline:18px}.project-grid span{display:block;margin-top:18px;color:var(--accent);font-size:.78rem;font-weight:900;text-transform:uppercase}.project-grid h3{font-size:1.1rem}.project-grid p{color:var(--muted);font-size:.92rem;line-height:1.55}.project-grid a{display:inline-flex;align-items:center;gap:6px;margin-bottom:20px;color:var(--ink);font-weight:800;text-decoration:none}.developer{display:grid;grid-template-columns:.8fr 1fr auto;gap:30px;align-items:center;padding:100px 0}.pricing{display:grid;grid-template-columns:.8fr 1.2fr;gap:28px;padding:100px 0}.plans{grid-template-columns:repeat(2,1fr);margin:0}.plans strong{display:block;margin:18px 0;font-size:2.2rem}.plans small{font-size:.9rem}.faq{padding:100px 0}.faq article{border-bottom:1px solid var(--line)}.faq button{display:flex;width:100%;justify-content:space-between;gap:20px;padding:24px 0;border:0;background:none;color:var(--ink);text-align:left;font:inherit;font-weight:900}.faq p{margin:0 0 22px;color:var(--muted);line-height:1.7}.contact-layout{display:grid;grid-template-columns:.8fr 1.2fr;gap:64px;align-items:start}.contact form{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:28px;border:1px solid var(--line);border-radius:8px;background:#fff}.contact label{display:grid;gap:7px;font-weight:800;font-size:.88rem}.contact label:nth-of-type(8),.contact .consent,.contact .success,.contact .error,.contact button{grid-column:1/-1}.contact input,.contact textarea,.contact select{min-height:48px;width:100%;padding:12px 13px;border:1px solid #d9dee8;border-radius:8px;color:var(--ink);font:inherit}.contact textarea{min-height:118px;resize:vertical}.contact input:focus,.contact textarea:focus,.contact select:focus{border-color:var(--accent);outline:3px solid rgba(39,93,232,.14)}.consent{display:flex!important;align-items:flex-start;font-weight:600!important}.consent input{width:18px;min-height:18px;flex:0 0 18px}.honeypot{position:absolute!important;left:-10000px!important}.success{color:var(--green)}.error{color:#b42318}footer{padding:48px 0;background:var(--ink);color:#b7c0d1}.footer-inner{display:grid;gap:24px}footer .brand{color:#fff}footer nav{flex-wrap:wrap}footer a{color:#d8deeb}footer small{padding-top:20px;border-top:1px solid rgba(255,255,255,.12)}[data-reveal]{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}[data-reveal].is-visible{opacity:1;transform:none}
@media(max-width:980px){.desktop-nav,.nav-actions{display:none}.nav{grid-template-columns:1fr auto}.menu-button{display:grid;width:42px;height:42px;place-items:center;border:0;border-radius:8px;background:var(--soft)}.mobile-nav{display:grid;position:fixed;top:74px;width:100%;padding:14px 24px 24px;background:#fff;border-bottom:1px solid var(--line)}.mobile-nav a{padding:12px 0;color:var(--ink);text-decoration:none;font-weight:800}.hero,.split,.developer,.pricing,.contact-layout{grid-template-columns:1fr}.hero{min-height:0;padding:140px 0 80px}.system-map,.process ol,.capability-grid,.project-grid{grid-template-columns:1fr 1fr}.plans{grid-template-columns:1fr}.developer{align-items:start}}
@media(max-width:640px){.wrap{width:min(calc(100% - 28px),1180px)}.hero h1,.process h2,.capabilities h2,.projects h2,.developer h2,.pricing h2,.faq h2,.contact h2{font-size:2.7rem}.hero-actions,.system-map,.process ol,.capability-grid,.project-grid,.contact form{grid-template-columns:1fr}.hero-actions{display:grid}.system-map svg{margin:auto;transform:rotate(90deg)}.split,.process,.capabilities,.projects,.developer,.pricing,.faq,.contact{padding-block:76px}.contact label:nth-of-type(8),.contact .consent,.contact .success,.contact .error,.contact button{grid-column:auto}}
@media(prefers-reduced-motion:reduce){:global(html){scroll-behavior:auto}[data-reveal]{opacity:1;transform:none;transition:none}.button{transition:none}}
</style>
