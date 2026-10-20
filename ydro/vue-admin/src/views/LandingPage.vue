<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { ArrowRight, Menu, X } from '@lucide/vue'

import FilmExperience from '../components/landing/FilmExperience.vue'
import { marketingPageList } from '../content/marketingPages.js'
import TrackNodeIcon from '../components/TrackNodeIcon.vue'
import {
  applyPublicSiteSeo,
  ensurePublicSiteTracker,
  loadTrackNodePublicSite,
  submitPublicSiteLead,
} from '../api/publicSite'

const PORTFOLIO_URL = 'https://tishechkinalexandr.ru/'
const site = ref(null)
const menuOpen = ref(false)
const cookieChoice = ref(null)
const cookiePreferencesOpen = ref(false)
const COOKIE_KEY = 'tracknode:analytics-consent:v1'
let disposed = false
const features = [
  {
    title: 'Аналитика',
    label: '01 / Видеть поведение',
    headline: 'Понимайте, что происходит на сайте.',
    description:
      'Посещения, источники переходов, страницы и события помогают изучать путь посетителя и находить точки для улучшения.',
  },
  {
    title: 'Заявки',
    label: '02 / Работать с обращениями',
    headline: 'У каждого обращения есть своё место.',
    description:
      'Контакты, комментарий, страница обращения и статус — в одном списке. От новой заявки до завершённой работы.',
  },
  {
    title: 'SEO-аудит',
    label: '03 / Находить проблемы',
    headline: 'Замечайте то, что мешает сайту.',
    description:
      'Запускайте техническую проверку и изучайте найденные проблемы по уровню важности: критично, важно и рекомендации.',
  },
  {
    title: 'Разделы сайта',
    label: '04 / Управлять содержанием',
    headline: 'Содержание сайта — под контролем.',
    description:
      'Открывайте разделы сайта и редактируйте доступные поля в кабинете. Состав настроек зависит от выбранного раздела.',
  },
]
const configuredContact = String(import.meta.env.VITE_LEGAL_CONTACT_EMAIL || '').trim()
const operatorEmail = /^(email@example\.ru|[^@]+@example\.(ru|com|org))$/i.test(configuredContact) ? '' : configuredContact

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
const formState = reactive({
  submitting: false,
  success: '',
  error: '',
  started: false,
})

const taskTypes = [
  'Создание сайта с нуля',
  'Индивидуальный дизайн',
  'Структура и прототип',
  'Кабинет аналитики TrackNode',
  'SEO и развитие сайта',
  'Другое',
]

const faq = [
  [
    'Сайт делается по шаблону?',
    'Нет. Структура, дизайн и интерфейс проектируются под конкретный бизнес.',
  ],
  [
    'Что получает клиент после запуска?',
    'Сайт и кабинет TrackNode с данными по посетителям, заявкам, источникам и SEO.',
  ],
  [
    'Где смотреть заявки?',
    'Все новые обращения отображаются в личном кабинете вместе с аналитикой сайта.',
  ],
  [
    'Что показывает SEO-блок?',
    'Техническое состояние, базовые ошибки и точки для дальнейшего развития сайта.',
  ],
  [
    'Как рассчитывается стоимость сайта?',
    'Стоимость рассчитывается индивидуально после обсуждения структуры, дизайна и функциональности.',
  ],
]

function track(type, payload = {}) {
  window.tracknode?.track?.(type, {
    source_site: 'tracknode',
    page_path: window.location.pathname,
    ...payload,
  })
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
  try {
    localStorage.setItem(COOKIE_KEY, choice)
  } catch {
    /* Browsers may restrict storage */
  }
  if (choice === 'all' && site.value) ensurePublicSiteTracker(site.value)
  if (choice === 'essential') {
    window.__trackNodeTracker?.destroy?.('consent_revoked')
    document
      .querySelectorAll('script[data-tracknode-managed="true"]')
      .forEach((el) => el.remove())
  }
}

function sanitize(value) {
  return String(value || '')
    .replace(/[<>]/g, '')
    .trim()
}

async function submitLead() {
  if (formState.submitting) return
  formState.error = ''
  formState.success = ''
  const hasContact = [form.phone, form.email].some((value) => sanitize(value))
  if (!sanitize(form.name) || !hasContact || !form.consent) {
    formState.error =
      'Укажите имя, хотя бы один способ связи и подтвердите согласие на обработку данных.'
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
        consent_document: '/consent',
        consent_document_version: '2026-10-15',
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
    formState.success =
      'Заявка отправлена. Я свяжусь с вами выбранным способом.'
    track('lead_form_success', { source: 'tracknode_landing_contact' })
  } catch (error) {
    formState.error =
      error?.message ||
      'Не удалось отправить заявку. Проверьте поля и попробуйте еще раз.'
    track('lead_form_error', { source: 'tracknode_landing_contact' })
  } finally {
    formState.submitting = false
  }
}

function closeMenu() {
  menuOpen.value = false
}

onMounted(async () => {
  try {
    const saved = localStorage.getItem(COOKIE_KEY)
    cookieChoice.value = ['all', 'essential'].includes(saved) ? saved : null
  } catch {
    cookieChoice.value = null
  }
  try {
    const payload = await loadTrackNodePublicSite()
    if (disposed) return
    site.value = payload.site
    applyPublicSiteSeo({
      ...payload.site,
      seo: {
        ...(payload.site?.seo || {}),
        title: 'TrackNode — платформа для сайтов, аналитики, заявок и SEO',
        description:
          'TrackNode: создание и развитие сайтов, аналитика посещений и источников, обработка заявок, технический SEO-аудит и управление разделами в одном кабинете.',
        canonical: 'https://tracknode.ru/',
        og_title:
          'TrackNode - цифровая платформа для сайта, заявок, аналитики и SEO',
        og_description:
          'Создание сайта под бизнес, данные после запуска, заявки, SEO и уведомления в одном кабинете.',
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
              serviceType: [
                'создание сайтов',
                'аналитика сайта',
                'управление заявками',
                'SEO-аудит',
                'анализ конкурентов',
              ],
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
  } catch {
    /* Public content stays accessible if optional site metadata cannot load. */
  }
})

onUnmounted(() => {
  disposed = true
})
</script>

<template>
  <div class="landing">
    <a class="skip-link" href="#main">К содержимому</a>
    <header class="header">
      <nav class="wrap nav" aria-label="Основная навигация">
        <a class="brand" href="#top" @click="closeMenu"
          ><TrackNodeIcon class="brand-icon" /><strong
            >tracknode<span>.</span></strong
          ></a
        >
        <div class="desktop-nav">
          <a href="#system">Фильм</a><a href="#solutions">Решения</a><a href="#features">Возможности</a
          ><a href="#pricing">Условия</a>
        </div>
        <div class="nav-actions">
          <RouterLink class="login" to="/login"
            >Войти <ArrowRight :size="15" /></RouterLink
          ><RouterLink class="button small" to="/register"
            >Начать работу <ArrowRight :size="15"
          /></RouterLink>
        </div>
        <button
          class="menu-button"
          type="button"
          :aria-expanded="menuOpen"
          aria-controls="tracknode-mobile-menu"
          :aria-label="menuOpen ? 'Закрыть меню' : 'Открыть меню'"
          @click="menuOpen = !menuOpen"
        >
          <X v-if="menuOpen" :size="23" /><Menu v-else :size="23" />
        </button>
      </nav>
      <div v-if="menuOpen" id="tracknode-mobile-menu" class="mobile-nav">
        <a href="#solutions" @click="closeMenu">Решения</a><a href="#features" @click="closeMenu">Возможности</a
        ><a href="#system" @click="closeMenu">Фильм</a
        ><a href="#pricing" @click="closeMenu">Условия</a
        ><a href="#contact" @click="closeMenu">Обсудить сайт</a
        ><RouterLink to="/login" @click="closeMenu">Войти</RouterLink
        ><RouterLink to="/register" @click="closeMenu"
          >Начать работу</RouterLink
        >
      </div>
    </header>
    <main id="main">
      <FilmExperience :services="features" />
      <section class="platform-summary wrap" aria-labelledby="platform-summary-title">
        <h2 id="platform-summary-title">TrackNode — платформа для сайта и работы с его данными</h2>
        <p>Создание и развитие сайтов, аналитика посещений, обработка заявок, технический SEO-аудит и редактирование доступных разделов — в одном кабинете TrackNode.</p>
        <p>Платформа помогает проследить путь посетителя от источника перехода до обращения и определить, что улучшить на сайте. Состав инструментов зависит от проекта и условий подключения.</p>
      </section>
      <section id="solutions" class="seo-directions wrap" aria-labelledby="seo-directions-title">
        <div class="seo-directions-head">
          <div><span class="section-number">Истории / Возможности</span><h2 id="seo-directions-title">Каждой задаче — свой маршрут.</h2></div>
          <p>От разработки сайта до работы с данными — познакомьтесь с отдельными направлениями TrackNode.</p>
        </div>
        <div class="seo-directions-grid">
          <RouterLink v-for="page in marketingPageList" :key="page.key" class="seo-directions-card" :to="page.path">
            <span class="seo-directions-top"><span>{{ page.number }} / 04</span><ArrowRight :size="18" aria-hidden="true" /></span>
            <strong>{{ page.short }}</strong>
            <span class="seo-directions-desc">{{ page.lead }}</span>
            <span class="seo-directions-more">Подробнее о решении ↗</span>
          </RouterLink>
        </div>
      </section>
      <section id="contact" class="contact">
        <div class="wrap contact-layout">
          <div class="contact-copy">
            <span class="section-number light">Эпилог / Разговор</span>
            <p class="kicker">Начнём с разговора</p>
            <h2>Ваша история.<br /><em>Следующий шаг.</em></h2>
            <p>
              Расскажите, какой сайт нужен вашему бизнесу. Вернёмся с вопросами
              по задаче и обсудим возможный формат работы.
            </p>
            <div class="contact-side-note">
              <span class="status-light"></span> Каждая заявка попадает в
              рабочий кабинет TrackNode
            </div>
            <div id="faq" class="closing-faq">
              <details v-for="item in faq" :key="item[0]">
                <summary>{{ item[0] }}</summary>
                <p>{{ item[1] }}</p>
              </details>
            </div>
          </div>
          <form novalidate @submit.prevent="submitLead" @focusin="formStarted">
            <div class="form-header">
              <span>Заявка на проект</span><span>01 / 01</span>
            </div>
            <div class="form-grid">
              <label
                >Как к вам обращаться? <span aria-hidden="true">*</span
                ><input
                  v-model="form.name"
                  maxlength="255"
                  autocomplete="name"
                  placeholder="Ваше имя"
                  required
              /></label>
              <label
                >Телефон<input
                  v-model="form.phone"
                  maxlength="100"
                  type="tel"
                  autocomplete="tel"
                  placeholder="+7 (999) 000-00-00"
              /></label>
              <label
                >Email<input
                  v-model="form.email"
                  maxlength="255"
                  type="email"
                  autocomplete="email"
                  placeholder="name@company.ru"
              /></label>
              <label
                >Что нужно сделать?<select v-model="form.taskType">
                  <option v-for="item in taskTypes" :key="item" :value="item">
                    {{ item }}
                  </option>
                </select></label
              >
              <label class="wide-field"
                >Как удобнее связаться?<select v-model="form.preferredContact">
                  <option value="phone">По телефону</option>
                  <option value="email">По email</option>
                </select></label
              >
              <label class="wide-field"
                >Расскажите о задаче<textarea
                  v-model="form.message"
                  maxlength="2000"
                  rows="4"
                  placeholder="Пару слов о проекте, целях и пожеланиях..."
                ></textarea>
              </label>
            </div>
            <p class="required-note">
              * Имя и хотя бы один контакт обязательны.
            </p>
            <label class="honeypot" aria-hidden="true"
              >Сайт<input
                v-model="form.website"
                tabindex="-1"
                autocomplete="off"
            /></label>
            <label class="consent"
              ><input v-model="form.consent" type="checkbox" required /><span
                >Даю отдельное
                <RouterLink
                  to="/consent"
                  target="_blank"
                  rel="noopener noreferrer"
                  >согласие на обработку данных заявки</RouterLink
                >
                для ответа на моё обращение. С условиями обработки можно
                ознакомиться в
                <RouterLink
                  to="/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  >политике персональных данных</RouterLink
                >.</span
              ></label
            >
            <p class="form-legal-note">
              Отправка заявки не означает согласия на рекламу. Условия
              использования сервиса — в
              <RouterLink to="/terms">пользовательском соглашении</RouterLink>.
            </p>
            <p v-if="formState.success" class="success" role="status">
              {{ formState.success }}
            </p>
            <p v-if="formState.error" class="error" role="alert">
              {{ formState.error }}
            </p>
            <button
              class="button submit-button"
              type="submit"
              :disabled="formState.submitting"
            >
              {{
                formState.submitting
                  ? 'Отправляем...'
                  : 'Обсудить создание сайта'
              }}
              <ArrowRight :size="19" />
            </button>
          </form>
        </div>
      </section>
    </main>

    <footer>
      <div class="wrap footer-inner">
        <div class="footer-brand">
          <a class="brand" href="#top"
            ><TrackNodeIcon class="brand-icon" /><strong
              >tracknode<span class="brand-dot">.</span></strong
            ></a
          >
          <p>Сайт, аналитика и развитие бизнеса в единой системе.</p>
          <small>© {{ new Date().getFullYear() }} TrackNode</small>
        </div>
        <nav aria-label="Ссылки в подвале">
          <RouterLink to="/sozdanie-saitov">Создание сайтов</RouterLink>
          <RouterLink to="/analitika-saita">Аналитика</RouterLink>
          <RouterLink to="/seo-audit">SEO-аудит</RouterLink>
          <RouterLink to="/upravlenie-zayavkami">Заявки</RouterLink>
          <a href="#features">Возможности</a><a href="#pwa">На смартфоне</a
          ><a href="#pricing">Стоимость</a><a href="#contact">Контакты</a>
          <RouterLink to="/login">Вход</RouterLink
          ><RouterLink to="/register">Регистрация</RouterLink>
          <RouterLink to="/privacy"
            >Политика обработки персональных данных</RouterLink
          ><RouterLink to="/consent">Согласие на заявку</RouterLink
          ><RouterLink to="/cookies">Файлы cookie</RouterLink
          ><RouterLink to="/terms">Пользовательское соглашение</RouterLink>
          <a
            :href="PORTFOLIO_URL"
            target="_blank"
            rel="noopener noreferrer"
            @click="trackPortfolioLink('footer')"
            >Сайт разработчика</a
          >
        </nav>
        <div class="operator-details">
          <span
            >Исполнитель применяет налог на профессиональный доход (НПД).</span
          ><a v-if="operatorEmail" :href="'mailto:' + operatorEmail">{{
            operatorEmail
          }}</a
          ><RouterLink to="/terms#operator">Сведения об исполнителе</RouterLink
          ><a
            :href="PORTFOLIO_URL"
            target="_blank"
            rel="noopener noreferrer"
            @click="trackPortfolioLink('developer')"
            >Сайт разработчика ↗</a
          >
        </div>
        <div class="footer-bottom">
          <span>Делаем сложное понятным.</span
          ><button
            type="button"
            class="cookie-manage"
            @click="cookiePreferencesOpen = true"
          >
            Настройки cookies
          </button>
        </div>
      </div>
    </footer>

    <aside
      v-if="cookieChoice === null || cookiePreferencesOpen"
      class="cookie-notice"
      aria-label="Настройки файлов cookie"
    >
      <div>
        <strong>Вы управляете данными</strong>
        <p>
          Необходимые файлы и локальные настройки помогают работе сайта.
          Необязательную аналитику посещений включаем только с вашего
          разрешения.
        </p>
        <RouterLink to="/privacy">Обработка данных</RouterLink>
        <RouterLink to="/cookies">Подробнее о cookies</RouterLink>
      </div>
      <div class="cookie-actions">
        <button
          type="button"
          class="cookie-accept"
          @click="setAnalyticsConsent('all')"
        >
          Разрешить аналитику
        </button>
        <button
          type="button"
          class="cookie-essential"
          @click="setAnalyticsConsent('essential')"
        >
          Только необходимые
        </button>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.platform-summary { padding-block: 64px; color: #b7c3d5; line-height: 1.8; }
.platform-summary h2 { max-width: 860px; color: #f1f4fa; font-size: clamp(24px, 3vw, 38px); line-height: 1.2; }
.platform-summary p { max-width: 880px; margin-top: 20px; }
.seo-directions{padding-block:clamp(55px,7vw,110px) clamp(95px,10vw,150px)}
.seo-directions-head{display:flex;justify-content:space-between;gap:40px;align-items:end;margin-bottom:44px}
.seo-directions-head h2{margin-top:22px;max-width:660px;font-size:clamp(31px,3.7vw,52px)}
.seo-directions-head>p{max-width:360px;font-size:14px;line-height:1.85;color:#aeb9c9;margin:0}
.seo-directions-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid #ffffff26;border-left:1px solid #ffffff26}
.seo-directions-card{display:flex;flex-direction:column;padding:27px;min-height:300px;border-right:1px solid #ffffff26;border-bottom:1px solid #ffffff26;transition:background .22s}
.seo-directions-card:hover{background:#22344d7b}
.seo-directions-top{display:flex;justify-content:space-between;align-items:center;color:#80a4f8;font-size:10px;letter-spacing:.14em}
.seo-directions-card strong{margin-top:50px;letter-spacing:-.04em;line-height:1.15;font-weight:550;font-size:clamp(20px,2vw,28px)}
.seo-directions-desc{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin-top:18px;line-height:1.6;font-size:12px;color:#9eabbc}
.seo-directions-more{margin-top:auto;padding-top:22px;color:#91b0ff;font-size:12px}
@media(max-width:1020px){.seo-directions-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){.seo-directions-head{align-items:start;flex-direction:column;gap:18px}.seo-directions-grid{grid-template-columns:1fr}.seo-directions-card{min-height:250px}.seo-directions-card strong{margin-top:26px}}

.landing {
  --blue: #467dff;
  --muted: #a0a9b8;
  --line: #ffffff16;
  background: #101216;
  color: #f1f3f7;
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
  overflow: clip;
  min-height: 100vh;
}
.landing * {
  box-sizing: border-box;
}
.landing a {
  color: inherit;
  text-decoration: none;
}
.landing button,
.landing input,
.landing select,
.landing textarea {
  font: inherit;
}
.landing button,
.landing a {
  -webkit-tap-highlight-color: transparent;
}
.landing :focus-visible {
  outline: 2px solid #8cb0ff;
  outline-offset: 5px;
}
.landing button {
  cursor: pointer;
}
.wrap {
  width: min(calc(100% - 96px), 1280px);
  margin-inline: auto;
}
.skip-link {
  position: fixed;
  top: 8px;
  left: 10px;
  z-index: 200;
  background: #255ce3;
  padding: 15px;
  transform: translateY(-150%);
}
.skip-link:focus {
  transform: none;
}
.header {
  position: absolute;
  inset: 0 0 auto;
  z-index: 40;
  border-bottom: 1px solid #ffffff09;
  background: linear-gradient(#0b0f16c9, transparent);
}
.nav {
  height: 88px;
  display: flex;
  align-items: center;
  gap: 40px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 25px;
  letter-spacing: -1.2px;
}
.brand strong {
  font-weight: 750;
}
.brand strong span {
  color: var(--blue);
}
.brand-icon {
  width: 31px;
  height: 31px;
}
.desktop-nav {
  display: flex;
  gap: 30px;
  margin: auto;
  font-size: 13px;
  color: #aeb5c2;
}
.desktop-nav a:hover,
.login:hover {
  color: #fff;
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 28px;
  font-size: 13px;
}
.login {
  display: flex;
  align-items: center;
  gap: 12px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
  min-height: 54px;
  padding: 0 24px;
  border: 1px solid #6c96ff;
  background: #356cf1;
  border-radius: 7px;
  color: #fff !important;
  font-size: 14px;
  font-weight: 650;
  transition:
    transform 0.2s,
    background 0.2s;
}
.button:hover {
  background: #4c80fa;
  transform: translateY(-2px);
}
.button.small {
  min-height: 42px;
  font-size: 12px;
  padding: 0 17px;
  gap: 18px;
}
.menu-button,
.mobile-nav {
  display: none;
}
h2 {
  font-size: clamp(32px, 3.4vw, 49px);
  line-height: 1.17;
  letter-spacing: -1.9px;
  font-weight: 500;
  margin: 0;
}
.section-number {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1.8px;
  color: #6e92d0;
  line-height: 1.7;
  display: block;
}
.status-light {
  width: 5px;
  height: 5px;
  background: #598bff;
  border-radius: 50%;
  display: inline-block;
  flex: none;
}
.closing-faq {
  margin-top: 42px;
  max-width: 420px;
}
.closing-faq details {
  border-top: 1px solid #ffffff14;
  padding: 15px 0;
}
.closing-faq summary {
  font-size: 11px;
  color: #aabbd6;
  cursor: pointer;
  line-height: 1.6;
}
.closing-faq details p {
  font-size: 11px;
  line-height: 1.8;
  color: #788eae;
  margin: 13px 0 0;
}
.contact {
  padding: 95px 0;
  background: #151a23;
  border-block: 1px solid var(--line);
}
.contact-layout {
  display: grid;
  grid-template-columns: 1fr 1.1fr;
  gap: 95px;
  align-items: start;
}
.contact-copy .kicker {
  color: #8d9ab0;
  font-size: 12px;
  margin-top: 25px;
}
.contact-copy h2 {
  font-size: clamp(35px, 4.3vw, 60px);
  margin-top: 20px;
}
.contact-copy h2 em {
  font-style: normal;
  color: #89adff;
}
.contact-copy > p:not(.kicker) {
  max-width: 370px;
  margin-top: 26px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.8;
}
.contact-side-note {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 45px;
  color: #8293ae;
  font-size: 11px;
  line-height: 1.7;
}
.contact form {
  padding: 28px;
  border: 1px solid #ffffff14;
  border-radius: 10px;
  background: #1c2330;
}
.form-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}
.form-header span:last-child {
  color: #6e7e99;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 23px;
}
.form-grid label {
  display: grid;
  gap: 8px;
  font-size: 11px;
  color: #b1bed2;
}
.form-grid input,
.form-grid select,
.form-grid textarea {
  display: block;
  width: 100%;
  min-height: 46px;
  min-width: 0;
  padding: 12px 13px;
  border: 1px solid #ffffff20;
  border-radius: 5px;
  color: #e3eaf7;
  background: #151b25;
  font-size: 13px;
}
.form-grid input::placeholder,
.form-grid textarea::placeholder {
  color: #6d7a90;
}
.form-grid textarea {
  min-height: 105px;
  resize: vertical;
}
.wide-field {
  grid-column: 1/-1;
}
.required-note {
  margin: 14px 0;
  color: #8091ac;
  font-size: 10px;
}
.honeypot {
  position: absolute !important;
  width: 1px;
  height: 1px;
  clip-path: inset(50%);
  overflow: hidden;
  white-space: nowrap;
}
.consent {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 18px;
  font-size: 11px;
  line-height: 1.7;
  color: #98a8c2;
  cursor: pointer;
}
.consent input {
  width: 17px;
  height: 17px;
  flex: 0 0 17px;
  margin: 2px 0 0;
  accent-color: #467dff;
}
.consent a,
.form-legal-note a {
  color: #9fbdff;
  text-decoration: underline;
}
.form-legal-note {
  color: #8393af;
  font-size: 10px;
  line-height: 1.7;
}
.success {
  color: #8bdbc0;
  font-size: 13px;
}
.error {
  color: #ffb7b7;
  font-size: 13px;
}
.submit-button {
  width: 100%;
  margin-top: 12px;
}
.button:disabled {
  opacity: 0.6;
  cursor: wait;
  transform: none;
}
footer {
  padding: 60px 0 25px;
  background: #0d1015;
}
.footer-inner {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 40px;
}
.footer-brand p {
  max-width: 260px;
  color: #7f8b9e;
  font-size: 12px;
  line-height: 1.8;
  margin: 20px 0;
}
.footer-brand small {
  color: #626e82;
  font-size: 10px;
}
footer nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px 20px;
  align-content: start;
}
footer nav a {
  font-size: 11px;
  color: #9ca9bf;
}
footer a:hover {
  color: #a7c3ff;
}
.operator-details {
  grid-column: 1/-1;
  display: flex;
  flex-wrap: wrap;
  gap: 15px 25px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  line-height: 1.8;
  color: #8b98ad;
}
.operator-details > span:first-child {
  width: 100%;
}
.operator-details a {
  color: #a3b8dc;
}
.footer-bottom {
  grid-column: 1/-1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
  color: #6e7e98;
  font-size: 10px;
}
.cookie-manage {
  padding: 0;
  border: 0;
  background: none;
  color: #a5bce4;
  font-size: 10px;
  text-decoration: underline;
}
.cookie-notice {
  position: fixed;
  z-index: 90;
  right: 20px;
  bottom: 20px;
  display: flex;
  align-items: center;
  gap: 25px;
  width: min(calc(100% - 40px), 690px);
  padding: 20px 22px;
  border: 1px solid #4a5971;
  border-radius: 10px;
  background: #1b2331;
  color: #e6ecf7;
  box-shadow: 0 20px 65px #0006;
}
.cookie-notice strong {
  font-size: 13px;
}
.cookie-notice p {
  max-width: 420px;
  margin: 7px 0;
  color: #aab7cc;
  font-size: 11px;
  line-height: 1.6;
}
.cookie-notice a {
  color: #9cbbff;
  font-size: 10px;
  text-decoration: underline;
}
.cookie-actions {
  display: grid;
  gap: 9px;
  flex: 0 0 170px;
}
.cookie-actions button {
  min-height: 39px;
  padding: 8px 12px;
  border: 1px solid #61718a;
  border-radius: 5px;
  background: #293344;
  color: #e5edfc;
  font-size: 10px;
}
.cookie-actions .cookie-accept {
  background: #356cf1;
  border-color: #6b94f8;
}
@media (max-width: 1100px) {
  .wrap {
    width: calc(100% - 56px);
  }
  .nav {
    gap: 25px;
  }
  .desktop-nav {
    gap: 20px;
  }
  .contact-layout {
    gap: 40px;
  }
}
@media (max-width: 767px) {
  .wrap {
    width: calc(100% - 40px);
  }
  .nav {
    height: 72px;
  }
  .desktop-nav,
  .nav-actions {
    display: none;
  }
  .brand {
    font-size: 23px;
  }
  .menu-button {
    display: grid;
    place-items: center;
    margin-left: auto;
    color: #d2ddf0;
    border: 1px solid #ffffff25;
    background: transparent;
    border-radius: 5px;
    width: 40px;
    height: 40px;
  }
  .mobile-nav {
    display: grid;
    position: absolute;
    top: 72px;
    left: 0;
    right: 0;
    padding: 14px 20px 23px;
    background: #141a25;
    border-bottom: 1px solid #3c4a64;
  }
  .mobile-nav a {
    padding: 12px;
    border-bottom: 1px solid #ffffff12;
    font-size: 14px;
  }
  .button {
    font-size: 12px;
    min-height: 48px;
    padding-inline: 19px;
    gap: 22px;
  }
  .contact {
    padding-block: 65px;
  }
  .contact-layout {
    grid-template-columns: 1fr;
    gap: 35px;
  }
  .contact-copy h2 {
    font-size: 40px;
  }
  .contact-copy > p:not(.kicker) {
    font-size: 13px;
  }
  .contact-side-note {
    margin-top: 25px;
    font-size: 10px;
  }
  .contact form {
    padding: 20px;
  }
  .form-grid {
    gap: 15px;
    grid-template-columns: 1fr;
  }
  .form-grid label {
    font-size: 11px;
  }
  .wide-field {
    grid-column: 1;
  }
  .form-grid input,
  .form-grid select,
  .form-grid textarea {
    font-size: 16px;
  }
  .consent {
    font-size: 10px;
  }
  footer {
    padding-top: 45px;
  }
  .footer-inner {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .footer-brand p {
    max-width: 300px;
  }
  .footer-bottom {
    align-items: start;
    font-size: 9px;
  }
  .cookie-notice {
    right: 12px;
    bottom: 12px;
    width: calc(100% - 24px);
    padding: 14px;
    display: block;
  }
  .cookie-notice strong {
    font-size: 12px;
  }
  .cookie-notice p {
    font-size: 10px;
    line-height: 1.5;
    max-width: none;
    margin-block: 5px;
  }
  .cookie-actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }
  .cookie-actions button {
    flex: 1;
    min-height: 38px;
    font-size: 9px;
  }
  .cookie-notice a {
    font-size: 9px;
  }
  .closing-faq {
    margin-top: 28px;
  }
}
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .contact-copy,
    .contact form,
    .footer-inner {
      animation: film-enter both linear;
      animation-timeline: view();
      animation-range: entry 0% entry 30%;
    }
  }
}
@keyframes film-enter {
  from {
    opacity: 0.2;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@media (prefers-reduced-motion: reduce) {
  .landing * {
    scroll-behavior: auto !important;
    animation: none !important;
    transition: none !important;
  }
  .button:hover {
    transform: none;
  }
}
</style>
