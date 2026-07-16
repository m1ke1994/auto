<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ArrowRight, Check, Menu, X } from '@lucide/vue'

import {
  applyPublicSiteSeo,
  ensurePublicSiteTracker,
  loadTrackNodePublicSite,
  submitPublicSiteLead,
} from '../api/publicSite'

const site = ref(null)
const sections = ref([])
const loading = ref(true)
const loadError = ref('')
const menuOpen = ref(false)
const openFaq = ref(0)
const form = reactive({ name: '', contact: '', message: '', consent: false, website: '' })
const formState = reactive({ submitting: false, success: '', error: '', started: false })
let revealObserver

const sectionsByKey = computed(() => Object.fromEntries(sections.value.map((item) => [item.key, item.content || {}])))
const backendPlans = computed(() => sectionsByKey.value.tariffs?.plans || [])
const plans = computed(() => {
  const seen = new Set()
  return backendPlans.value.filter((plan) => {
    const key = plan.title || plan.name
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  }).slice(0, 2)
})

function featureLabel(feature) {
  if (typeof feature === 'string') return feature
  if (!feature || typeof feature !== 'object') return ''
  return feature.label || feature.title || feature.text || feature.name || ''
}

function planFeatures(plan) {
  if (!Array.isArray(plan?.features)) return []
  return plan.features.map(featureLabel).filter(Boolean)
}

const problems = [
  'Неясно, почему посетители не оставляют заявки',
  'Ошибки на сайте замечают слишком поздно',
  'После запуска рекламы видны расходы, но не результат',
  'Обращения клиентов теряются между формой и мессенджерами',
  'Непонятно, какие страницы действительно работают',
]

const flow = ['Посетитель', 'Ваш сайт', 'TrackNode', 'Личный кабинет', 'Telegram', 'Решение']

const productStories = [
  {
    key: 'analytics', kicker: 'Аналитика', title: 'Сразу видно главное',
    text: 'Посетители, заявки, конверсия и просмотры собраны на одном экране. TrackNode объясняет ситуацию простыми словами и помогает выбрать следующий шаг.',
    route: '/dashboard', reverse: false,
  },
  {
    key: 'leads', kicker: 'Заявки', title: 'Ни одно обращение не потеряется',
    text: 'Имя, контакты, сообщение, источник и статус заявки остаются в кабинете. Команда видит историю и понимает, кому нужно ответить.',
    route: '/dashboard', reverse: true,
  },
  {
    key: 'seo', kicker: 'SEO и конкуренты', title: 'Проблемы становятся конкретными задачами',
    text: 'Проверка сайта находит технические и содержательные ошибки. Анализ конкурентов помогает понять, что стоит улучшить — без таблиц на сотни строк.',
    route: '/dashboard', reverse: false,
  },
  {
    key: 'notifications', kicker: 'Telegram', title: 'О новом клиенте узнаёте сразу',
    text: 'TrackNode отправляет уведомление после заявки. Не нужно постоянно обновлять почту или держать открытым кабинет.',
    route: '/dashboard', reverse: true,
  },
  {
    key: 'ai', kicker: 'Рекомендации', title: 'Не просто данные, а понятный следующий шаг',
    text: 'Рекомендации опираются на аналитику сайта и расставляют приоритеты: что проверить сейчас, а что можно отложить.',
    route: '/dashboard', reverse: false,
  },
  {
    key: 'sites', kicker: 'Несколько сайтов', title: 'Один кабинет для всей работы',
    text: 'Переключайтесь между сайтами без смешивания данных. Для каждого сохраняются свои заявки, аналитика, аудит и настройки.',
    route: '/dashboard', reverse: true,
  },
]

const audiences = [
  ['Малый бизнес', 'Контролировать сайт и обращения без отдельного аналитика.'],
  ['Веб-студии', 'Следить за сайтами клиентов и показывать результат работы.'],
  ['Специалисты', 'Понимать, какие услуги интересуют людей и откуда они приходят.'],
  ['Компании', 'Дать маркетингу и продажам общую картину по сайту.'],
  ['Несколько сайтов', 'Переключаться между проектами в одном кабинете.'],
]

const faq = [
  ['Нужно ли менять существующий сайт?', 'Нет. TrackNode подключается к уже работающему сайту с помощью кода отслеживания.'],
  ['Нужно ли разбираться в аналитике?', 'Нет. Основные показатели и выводы написаны обычным языком. Подробные данные остаются доступны, когда они нужны.'],
  ['Где появляются заявки?', 'В личном кабинете TrackNode и в подключённом Telegram.'],
  ['Можно ли подключить несколько сайтов?', 'Да. Сайты переключаются внутри одного кабинета, а их данные не смешиваются.'],
  ['Подходит ли сервис малому бизнесу?', 'Да. TrackNode рассчитан на владельца бизнеса, которому важно быстро понять ситуацию и принять решение.'],
]

function closeMenu() { menuOpen.value = false }

function track(type, payload = {}) {
  window.tracknode?.track?.(type, { page: window.location.pathname, ...payload })
}

function formStarted() {
  if (formState.started) return
  formState.started = true
  track('lead_form_started')
}

async function submitLead() {
  if (formState.submitting) return
  formState.error = ''
  formState.success = ''
  if (!form.name.trim() || !form.contact.trim() || !form.consent) {
    formState.error = 'Заполните имя, телефон или email и подтвердите согласие.'
    return
  }
  formState.submitting = true
  const query = new URLSearchParams(window.location.search)
  try {
    await submitPublicSiteLead(site.value?.slug, {
      name: form.name.trim(), contact: form.contact.trim(), message: form.message.trim(),
      consent: form.consent, website: form.website, source_url: window.location.href,
      section_key: 'contact', form_name: 'Новый лендинг TrackNode',
      payload: {
        referrer: document.referrer || '',
        utm_source: query.get('utm_source') || '', utm_medium: query.get('utm_medium') || '',
        utm_campaign: query.get('utm_campaign') || '', utm_term: query.get('utm_term') || '',
        utm_content: query.get('utm_content') || '',
      },
    })
    Object.assign(form, { name: '', contact: '', message: '', consent: false, website: '' })
    formState.success = 'Спасибо! Заявка отправлена. Мы свяжемся с вами в ближайшее время.'
    track('lead_form_success')
  } catch {
    formState.error = 'Не удалось отправить заявку. Попробуйте ещё раз или напишите нам в Telegram.'
    track('lead_form_error')
  } finally {
    formState.submitting = false
  }
}

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
    applyPublicSiteSeo(site.value)
    ensurePublicSiteTracker(site.value)
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
    <div v-if="loading" class="page-state">Загружаем TrackNode…</div>
    <div v-else-if="loadError" class="page-state"><strong>Сайт временно недоступен</strong><span>{{ loadError }}</span></div>
    <template v-else>
      <header class="header">
        <nav class="nav wrap" aria-label="Основная навигация">
          <a href="#top" class="brand" @click="closeMenu"><span>TN</span>TrackNode</a>
          <div class="desktop-nav">
            <a href="#product">Возможности</a><a href="#audience">Для кого</a><a href="#pricing">Тарифы</a><a href="#faq">FAQ</a>
          </div>
          <div class="nav-actions"><RouterLink to="/login" class="login" @click="track('login_click')">Войти</RouterLink><RouterLink to="/register" class="button small">Попробовать</RouterLink></div>
          <button class="menu-button" type="button" :aria-expanded="menuOpen" aria-label="Открыть меню" @click="menuOpen = !menuOpen"><X v-if="menuOpen" /><Menu v-else /></button>
        </nav>
        <div v-if="menuOpen" class="mobile-nav"><a href="#product" @click="closeMenu">Возможности</a><a href="#audience" @click="closeMenu">Для кого</a><a href="#pricing" @click="closeMenu">Тарифы</a><a href="#faq" @click="closeMenu">FAQ</a><RouterLink to="/login">Войти</RouterLink></div>
      </header>

      <main id="top">
        <section class="hero wrap">
          <div class="hero-copy" data-reveal>
            <p class="kicker">Помощник владельца сайта</p>
            <h1>Управляйте сайтом так, словно рядом работает аналитик</h1>
            <p class="lead">TrackNode показывает, что происходит с сайтом, где теряются клиенты и что стоит сделать дальше.</p>
            <div class="hero-actions"><RouterLink to="/register" class="button" @click="track('primary_cta_click')">Подключить TrackNode <ArrowRight :size="18" /></RouterLink><a href="#product" class="text-link">Посмотреть продукт</a></div>
            <p class="fine">Для малого бизнеса, специалистов, компаний и веб-студий.</p>
          </div>
          <a href="#product" class="hero-product product-window" data-reveal aria-label="Посмотреть интерфейс TrackNode">
            <div class="window-bar"><i /><i /><i /><span>TrackNode · Аналитика</span></div>
            <div class="live-screen analytics-screen">
              <aside><b>TN</b><span>Главная</span><strong>Аналитика</strong><span>Заявки</span><span>SEO-аудит</span><span>Telegram</span></aside>
              <div class="screen-body"><small>АНАЛИТИКА</small><h2>Главное за 14 дней</h2><div class="metrics"><div><span>Посетители</span><b>34</b></div><div><span>Заявки</span><b>2</b></div><div><span>Конверсия</span><b>5,9%</b></div><div><span>Просмотры</span><b>81</b></div></div><div class="insight"><b>Сайт посещают и оставляют заявки.</b><span>Больше всего людей открывают главную страницу.</span></div><div class="trend"><span v-for="height in [28,42,36,58,47,72,62,85,70,96,78,102]" :key="height" :style="{height:`${height}px`}" /></div></div>
            </div>
          </a>
        </section>

        <section class="problem-section">
          <div class="wrap problem-layout">
            <div data-reveal><p class="kicker">Обычная ситуация</p><h2>Сайт работает. Но что происходит внутри — непонятно.</h2></div>
            <div class="problem-list" data-reveal><p v-for="item in problems" :key="item">{{ item }}</p></div>
          </div>
          <p class="solution-line wrap" data-reveal>TrackNode собирает эту картину в одном кабинете и переводит её на понятный язык.</p>
        </section>

        <section class="flow-section wrap" data-reveal>
          <p class="kicker">Как это работает</p><h2>От первого посещения — до вашего решения</h2>
          <div class="flow"><template v-for="(item,index) in flow" :key="item"><span>{{ item }}</span><ArrowRight v-if="index < flow.length - 1" :size="18" /></template></div>
        </section>

        <section id="product" class="product-stories">
          <article v-for="story in productStories" :key="story.key" class="story wrap" :class="{ reverse: story.reverse }">
            <div class="story-copy" data-reveal><p class="kicker">{{ story.kicker }}</p><h2>{{ story.title }}</h2><p>{{ story.text }}</p><RouterLink :to="story.route" class="text-link">Открыть кабинет <ArrowRight :size="16" /></RouterLink></div>
            <div class="product-window story-window" data-reveal>
              <div class="window-bar"><i /><i /><i /><span>TrackNode · {{ story.kicker }}</span></div>
              <div class="live-screen story-screen">
                <div class="screen-sidebar"><b>TN</b><span>Главная</span><span :class="{selected: story.key === 'analytics'}">Аналитика</span><span :class="{selected: story.key === 'leads'}">Заявки</span><span :class="{selected: story.key === 'seo'}">SEO-аудит</span><span :class="{selected: story.key === 'notifications'}">Telegram</span><span :class="{selected: story.key === 'ai'}">Рекомендации</span></div>
                <div class="story-content"><small>{{ story.kicker }}</small><h3>{{ story.title }}</h3><div class="content-line wide"/><div class="content-line"/><div class="screen-panel"><b>{{ story.text.split('.')[0] }}.</b><span>{{ story.text.split('.').slice(1).join('.').trim() }}</span></div><div class="content-table"><i v-for="n in 4" :key="n" /></div></div>
              </div>
            </div>
          </article>
        </section>

        <section id="audience" class="audience-section">
          <div class="wrap"><div class="section-intro" data-reveal><p class="kicker">Для кого</p><h2>Когда сайт — часть ежедневной работы</h2><p>TrackNode подходит тем, кому важно видеть результат без погружения в сложные системы.</p></div><div class="audience-grid" data-reveal><article v-for="item in audiences" :key="item[0]"><h3>{{ item[0] }}</h3><p>{{ item[1] }}</p></article></div></div>
        </section>

        <section id="pricing" class="pricing-section wrap">
          <div class="section-intro" data-reveal><p class="kicker">Тарифы</p><h2>Выберите нужный уровень контроля</h2><p>Цены и состав тарифов загружаются из действующей системы TrackNode.</p></div>
          <div v-if="plans.length" class="plans" data-reveal><article v-for="(plan,index) in plans" :key="plan.title" :class="{primary:index===1}"><p>{{ plan.title }}</p><h3>{{ plan.price }}<small v-if="plan.price_suffix"> {{ plan.price_suffix }}</small></h3><span>{{ plan.description }}</span><ul><li v-for="(feature,index) in planFeatures(plan)" :key="`${plan.title}-feature-${index}`"><i><Check :size="15" stroke-width="3" /></i><span>{{ feature }}</span></li></ul><RouterLink to="/register" class="button">Подключить</RouterLink></article></div>
          <p v-else class="empty-pricing">Тарифы временно загружаются. Оставьте заявку — подберём подходящий вариант.</p>
        </section>

        <section id="faq" class="faq-section wrap">
          <div class="section-intro" data-reveal><p class="kicker">FAQ</p><h2>Коротко о главном</h2></div>
          <div class="faq" data-reveal><article v-for="(item,index) in faq" :key="item[0]"><button type="button" :aria-expanded="openFaq===index" @click="openFaq=openFaq===index?-1:index"><span>{{ item[0] }}</span><b>{{ openFaq===index?'−':'+' }}</b></button><p v-show="openFaq===index">{{ item[1] }}</p></article></div>
        </section>

        <section id="contact" class="contact-section">
          <div class="wrap contact-layout">
            <div data-reveal><p class="kicker">Начнём с вашего сайта</p><h2>Расскажите, что хотите улучшить</h2><p>Посмотрим задачу и объясним, как TrackNode может помочь именно в вашем случае.</p></div>
            <form data-reveal novalidate @submit.prevent="submitLead" @focusin="formStarted"><label>Имя<input v-model="form.name" maxlength="255" autocomplete="name" required /></label><label>Телефон или email<input v-model="form.contact" maxlength="255" autocomplete="email" required /></label><label>Коротко опишите задачу<textarea v-model="form.message" maxlength="2000" rows="4" /></label><label class="honeypot" aria-hidden="true">Сайт<input v-model="form.website" tabindex="-1" autocomplete="off" /></label><label class="consent"><input v-model="form.consent" type="checkbox" required /><span>Я согласен на обработку персональных данных.</span></label><p v-if="formState.success" class="success" role="status">{{ formState.success }}</p><p v-if="formState.error" class="error" role="alert">{{ formState.error }}</p><button class="button" type="submit" :disabled="formState.submitting">{{ formState.submitting ? 'Отправляем…' : 'Оставить заявку' }}</button></form>
          </div>
        </section>

        <section class="final-section wrap" data-reveal><p>Ваш сайт может объяснять, что ему мешает.</p><h2>Начните видеть главное.</h2><div><RouterLink to="/register" class="button">Попробовать TrackNode <ArrowRight :size="18" /></RouterLink><a href="#contact" class="text-link">Оставить заявку</a></div></section>
      </main>

      <footer><div class="wrap footer-inner"><a href="#top" class="brand"><span>TN</span>TrackNode</a><p>Аналитика, заявки и управление сайтом — без лишней сложности.</p><div><RouterLink to="/login">Войти</RouterLink><a href="#pricing">Тарифы</a><a href="#contact">Контакты</a></div><small>© {{ new Date().getFullYear() }} TrackNode</small></div></footer>
    </template>
  </div>
</template>

<style scoped>
:global(*){box-sizing:border-box}:global(html){scroll-behavior:smooth;scroll-padding-top:90px}:global(body){margin:0;background:#fff}.landing{--ink:#11182d;--muted:#687086;--soft:#f5f6f9;--accent:#6547e8;min-height:100vh;overflow:hidden;color:var(--ink);background:#fff;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{width:min(calc(100% - 48px),1180px);margin-inline:auto}.page-state{display:grid;min-height:100vh;place-content:center;gap:8px;text-align:center}.header{position:fixed;z-index:50;top:0;width:100%;border-bottom:1px solid rgba(17,24,45,.06);background:rgba(255,255,255,.9);backdrop-filter:blur(18px)}.nav{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;min-height:74px}.brand{display:inline-flex;align-items:center;gap:10px;color:var(--ink);font-size:1rem;font-weight:780;letter-spacing:-.02em;text-decoration:none}.brand>span{display:grid;width:32px;height:32px;place-items:center;border-radius:10px;color:#fff;background:var(--ink);font-size:.72rem;letter-spacing:-.04em}.desktop-nav{display:flex;gap:30px}.desktop-nav a,.login,.mobile-nav a,footer a{color:#4b5369;text-decoration:none;font-size:.88rem;font-weight:600}.desktop-nav a:hover,.login:hover,footer a:hover{color:var(--ink)}.nav-actions{display:flex;align-items:center;justify-content:flex-end;gap:20px}.button{display:inline-flex;min-height:50px;align-items:center;justify-content:center;gap:9px;padding:0 22px;border:0;border-radius:13px;color:#fff;background:var(--ink);box-shadow:0 10px 28px rgba(17,24,45,.13);font:inherit;font-weight:700;text-decoration:none;transition:transform .2s,box-shadow .2s,background .2s}.button:hover{background:#262f49;box-shadow:0 15px 34px rgba(17,24,45,.18);transform:translateY(-2px)}.button.small{min-height:40px;padding-inline:16px;font-size:.86rem}.button:disabled{cursor:wait;opacity:.65}.menu-button,.mobile-nav{display:none}.hero{display:grid;grid-template-columns:.83fr 1.17fr;align-items:center;gap:64px;min-height:820px;padding-top:110px}.kicker{margin:0 0 22px;color:var(--accent);font-size:.76rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase}.hero h1{max-width:670px;margin:0;font-size:clamp(3.4rem,5.9vw,5.8rem);font-weight:740;line-height:.98;letter-spacing:-.067em}.lead{max-width:610px;margin:28px 0 0;color:var(--muted);font-size:1.12rem;line-height:1.7}.hero-actions{display:flex;align-items:center;gap:24px;margin-top:34px}.text-link{display:inline-flex;align-items:center;gap:7px;color:var(--ink);font-weight:700;text-decoration:none}.text-link:hover{color:var(--accent)}.fine{margin:26px 0 0;color:#8b91a2;font-size:.82rem}.product-window{display:block;overflow:hidden;border:1px solid rgba(22,30,54,.08);border-radius:20px;background:#fff;box-shadow:0 35px 90px rgba(25,31,55,.16);text-decoration:none;transform:perspective(1300px) rotateY(-4deg) rotateX(1deg)}.window-bar{display:flex;height:42px;align-items:center;gap:6px;padding:0 14px;border-bottom:1px solid #eceef3;background:#f8f9fb}.window-bar i{width:8px;height:8px;border-radius:50%;background:#d8dbe3}.window-bar span{margin-left:8px;color:#8a90a0;font-size:.66rem}.live-screen{display:grid;min-height:430px;color:var(--ink);background:#f7f8fb}.analytics-screen{grid-template-columns:120px 1fr}.analytics-screen aside,.screen-sidebar{display:flex;flex-direction:column;gap:18px;padding:22px 16px;color:#8a90a0;background:#fff;font-size:.62rem}.analytics-screen aside b,.screen-sidebar b{margin-bottom:10px;color:var(--accent);font-size:1rem}.analytics-screen aside strong,.screen-sidebar .selected{color:var(--ink)}.screen-body{padding:34px}.screen-body small,.story-content small{color:var(--accent);font-size:.58rem;font-weight:800;letter-spacing:.1em}.screen-body h2{margin:7px 0 22px;font-size:1.35rem}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.metrics>div{padding:12px;border-radius:10px;background:#fff}.metrics span,.metrics b{display:block}.metrics span{color:#81889a;font-size:.54rem}.metrics b{margin-top:8px;font-size:1.15rem}.insight{display:grid;gap:5px;margin-top:12px;padding:14px;border-radius:10px;background:#eeeafd}.insight b{font-size:.7rem}.insight span{color:#696f81;font-size:.58rem}.trend{display:flex;height:118px;align-items:flex-end;gap:7px;margin-top:14px;padding:10px 15px;border-radius:10px;background:#fff}.trend span{flex:1;max-height:100%;border-radius:4px 4px 1px 1px;background:linear-gradient(#8c75ef,#dcd6fa)}.problem-section{padding:150px 0 120px;background:var(--soft)}.problem-layout{display:grid;grid-template-columns:1fr 1fr;gap:100px}.problem-layout h2,.flow-section h2,.section-intro h2,.contact-layout h2{margin:0;font-size:clamp(2.5rem,4.5vw,4.5rem);line-height:1.04;letter-spacing:-.055em}.problem-list{border-top:1px solid #dfe2e9}.problem-list p{margin:0;padding:19px 0;border-bottom:1px solid #dfe2e9;color:#4f576c;font-size:1.05rem}.solution-line{margin-top:100px!important;font-size:clamp(1.6rem,3vw,2.7rem);font-weight:650;line-height:1.25;letter-spacing:-.035em}.flow-section{padding:150px 0;text-align:center}.flow-section .kicker{margin-inline:auto}.flow{display:flex;align-items:center;justify-content:center;gap:15px;margin-top:62px}.flow span{padding:14px 18px;border-radius:999px;background:var(--soft);font-size:.86rem;font-weight:700}.flow svg{color:#a1a6b3}.product-stories{background:#fbfbfc}.story{display:grid;grid-template-columns:.72fr 1.28fr;align-items:center;gap:90px;min-height:760px;padding-block:120px}.story.reverse{grid-template-columns:1.28fr .72fr}.story.reverse .story-copy{order:2}.story-copy h2{margin:0;font-size:clamp(2.5rem,4.4vw,4.2rem);line-height:1.02;letter-spacing:-.055em}.story-copy>p:not(.kicker){margin:25px 0;color:var(--muted);font-size:1.04rem;line-height:1.75}.story-window{transform:none}.story-window:hover{box-shadow:0 42px 100px rgba(25,31,55,.2);transform:translateY(-4px)}.story-screen{grid-template-columns:115px 1fr;min-height:440px}.story-content{padding:38px}.story-content h3{margin:8px 0 25px;font-size:1.35rem}.content-line{width:54%;height:8px;margin:8px 0;border-radius:4px;background:#e9eaf0}.content-line.wide{width:82%}.screen-panel{display:grid;gap:8px;margin-top:28px;padding:24px;border-radius:14px;background:#f0edfd}.screen-panel b{font-size:.78rem}.screen-panel span{color:#686e80;font-size:.65rem;line-height:1.6}.content-table{display:grid;gap:8px;margin-top:20px}.content-table i{height:32px;border-radius:7px;background:#f1f2f5}.audience-section{padding:150px 0;background:var(--ink);color:#fff}.section-intro{max-width:760px}.section-intro>p:last-child{color:var(--muted);font-size:1.06rem;line-height:1.7}.audience-section .section-intro>p:last-child{color:#a9afbd}.audience-grid{display:grid;grid-template-columns:repeat(6,1fr);margin-top:80px;border-top:1px solid rgba(255,255,255,.15)}.audience-grid article{grid-column:span 2;min-height:210px;padding:28px 24px;border-bottom:1px solid rgba(255,255,255,.15)}.audience-grid article:not(:nth-child(3n)){border-right:1px solid rgba(255,255,255,.15)}.audience-grid article:nth-child(4){grid-column:2/span 2}.audience-grid h3{margin:0;font-size:1.25rem}.audience-grid p{color:#aeb4c1;line-height:1.65}.pricing-section{padding-block:150px}.plans{display:grid;grid-template-columns:repeat(2,minmax(0,460px));gap:28px;margin-top:70px}.plans article{padding:42px;border-radius:24px;background:var(--soft)}.plans article.primary{color:#fff;background:var(--ink)}.plans article>p{font-weight:750}.plans h3{margin:25px 0 10px;font-size:2.8rem;letter-spacing:-.05em}.plans h3 small{font-size:.9rem}.plans article>span{color:var(--muted)}.plans .primary>span{color:#acb2c0}.plans ul{display:grid;gap:13px;margin:30px 0;padding:0;list-style:none}.plans li{display:flex;gap:9px;font-size:.88rem}.plans .primary .button{color:var(--ink);background:#fff}.empty-pricing{margin-top:45px;padding:28px;border-radius:18px;background:var(--soft)}.faq-section{display:grid;grid-template-columns:.7fr 1.3fr;gap:90px;padding-block:150px}.faq{border-top:1px solid #e1e3e9}.faq article{border-bottom:1px solid #e1e3e9}.faq button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:20px;padding:24px 0;border:0;color:var(--ink);text-align:left;background:none;font:inherit;font-weight:700}.faq button b{font-size:1.35rem;font-weight:400}.faq article p{margin:0;padding:0 40px 24px 0;color:var(--muted);line-height:1.7}.contact-section{padding:150px 0;background:var(--soft)}.contact-layout{display:grid;grid-template-columns:1fr 1fr;gap:100px}.contact-layout>div>p:last-child{max-width:550px;color:var(--muted);font-size:1.05rem;line-height:1.7}.contact-layout form{display:grid;gap:17px;padding:35px;border-radius:22px;background:#fff;box-shadow:0 20px 65px rgba(25,31,55,.08)}.contact-layout label{display:grid;gap:8px;font-size:.86rem;font-weight:700}.contact-layout input,.contact-layout textarea{width:100%;min-height:50px;padding:13px 14px;border:1px solid #dfe1e7;border-radius:11px;color:var(--ink);background:#fff;font:inherit}.contact-layout textarea{min-height:110px;resize:vertical}.contact-layout input:focus,.contact-layout textarea:focus{border-color:var(--accent);outline:3px solid rgba(101,71,232,.12)}.contact-layout .consent{display:flex;align-items:flex-start;font-weight:500;line-height:1.5}.consent input{width:19px;min-height:19px;flex:0 0 19px}.honeypot{position:absolute!important;left:-10000px!important}.success{color:#08775a}.error{color:#b42318}.final-section{padding-block:170px;text-align:center}.final-section>p{color:var(--accent);font-weight:750}.final-section h2{margin:15px 0 40px;font-size:clamp(3.3rem,7vw,7rem);line-height:.95;letter-spacing:-.07em}.final-section>div{display:flex;align-items:center;justify-content:center;gap:25px}footer{padding:50px 0;color:#aeb4c1;background:var(--ink)}.footer-inner{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:35px}.footer-inner .brand{color:#fff}.footer-inner p{font-size:.83rem}.footer-inner>div{display:flex;gap:20px}.footer-inner small{grid-column:1/-1;padding-top:28px;border-top:1px solid rgba(255,255,255,.1)}[data-reveal]{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}[data-reveal].is-visible{opacity:1;transform:none}
.plans{grid-template-columns:repeat(2,minmax(0,1fr));align-items:stretch}.plans article{position:relative;display:grid;grid-template-rows:auto minmax(92px,auto) auto 1fr auto;height:100%;min-height:560px;overflow:hidden;padding:42px;border:1px solid rgba(17,24,45,.08);border-radius:28px;background:linear-gradient(180deg,rgba(255,255,255,.96),rgba(245,246,249,.92));box-shadow:0 24px 70px rgba(25,31,55,.1);transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease}.plans article:before{content:"";position:absolute;inset:0 0 auto;height:150px;background:radial-gradient(circle at 18% 0,rgba(101,71,232,.14),transparent 72%);pointer-events:none}.plans article:hover{border-color:rgba(101,71,232,.24);box-shadow:0 32px 90px rgba(25,31,55,.16);transform:translateY(-4px)}.plans article.primary{color:#fff;border-color:rgba(255,255,255,.16);background:linear-gradient(155deg,#11182d,#1f2741 58%,#513ed0)}.plans article.primary:before{background:radial-gradient(circle at 18% 0,rgba(255,255,255,.2),transparent 72%)}.plans article>p,.plans h3,.plans article>span,.plans ul,.plans .button{position:relative}.plans article>p{margin:0;font-size:1.05rem;font-weight:800;letter-spacing:-.02em}.plans h3{align-self:start;margin:28px 0 0;padding-bottom:25px;border-bottom:1px solid rgba(17,24,45,.1);font-size:clamp(3rem,5vw,4.1rem);line-height:.9;letter-spacing:-.06em}.plans article.primary h3{border-bottom-color:rgba(255,255,255,.16)}.plans h3 small{font-size:1rem;font-weight:700;letter-spacing:0;white-space:nowrap}.plans article>span{align-self:start;min-height:52px;color:var(--muted);font-size:1rem;line-height:1.65}.plans .primary>span{color:#c7cce0}.plans ul{align-self:start;display:grid;gap:15px;margin:30px 0 0;padding:0;list-style:none}.plans li{display:flex;align-items:flex-start;gap:11px;color:#3f475c;font-size:.95rem;line-height:1.45}.plans li i{display:grid;width:23px;height:23px;flex:0 0 23px;place-items:center;border-radius:50%;color:#2a8f63;background:#e9f8f0}.plans li span{min-width:0;overflow-wrap:anywhere}.plans .primary li{color:#f3f5ff}.plans .primary li i{color:#11182d;background:#fff}.plans .button{width:100%;min-height:54px;margin-top:36px;border-radius:16px}.plans .primary .button{color:var(--ink);background:#fff}.plans .primary .button:hover{background:#f2f4ff}
@media(max-width:1000px){.desktop-nav,.nav-actions{display:none}.nav{grid-template-columns:1fr auto}.menu-button{display:grid;width:42px;height:42px;place-items:center;border:0;border-radius:11px;background:var(--soft)}.mobile-nav{display:grid;position:fixed;top:74px;width:100%;gap:0;padding:12px 24px 20px;border-bottom:1px solid #e8e9ed;background:#fff}.mobile-nav a{padding:13px 0}.hero{grid-template-columns:1fr;gap:50px;padding-block:160px 90px}.hero-copy{text-align:center}.hero h1,.lead{margin-inline:auto}.hero-actions{justify-content:center}.hero-product{width:min(100%,780px);margin-inline:auto}.problem-layout,.contact-layout{grid-template-columns:1fr;gap:55px}.story,.story.reverse{grid-template-columns:1fr;gap:55px;min-height:0}.story.reverse .story-copy{order:0}.story-copy{max-width:720px}.audience-grid article{grid-column:span 3}.audience-grid article:nth-child(4){grid-column:span 3}.audience-grid article:not(:nth-child(3n)){border-right:0}.audience-grid article:nth-child(odd){border-right:1px solid rgba(255,255,255,.15)}.faq-section{grid-template-columns:1fr;gap:55px}.footer-inner{grid-template-columns:1fr}.footer-inner small{grid-column:auto}}
@media(max-width:680px){.wrap{width:min(calc(100% - 36px),1180px)}.hero{min-height:0;padding-top:130px}.hero h1{font-size:clamp(3rem,14vw,4.5rem)}.lead{font-size:1rem}.hero-actions{flex-direction:column}.product-window{border-radius:14px;transform:none}.live-screen{min-height:300px}.analytics-screen,.story-screen{grid-template-columns:1fr}.analytics-screen aside,.screen-sidebar{display:none}.screen-body,.story-content{padding:22px}.metrics{grid-template-columns:repeat(2,1fr)}.trend{height:80px}.problem-section,.flow-section,.audience-section,.pricing-section,.faq-section,.contact-section{padding-block:100px}.problem-layout h2,.flow-section h2,.section-intro h2,.contact-layout h2{font-size:2.7rem}.solution-line{margin-top:65px!important}.flow{display:grid;grid-template-columns:1fr;gap:8px}.flow svg{margin:auto;transform:rotate(90deg)}.story{padding-block:85px}.story-copy h2{font-size:2.8rem}.story-screen{min-height:330px}.audience-grid{grid-template-columns:1fr;margin-top:50px}.audience-grid article,.audience-grid article:nth-child(4){grid-column:auto;min-height:0;padding-inline:0;border-right:0!important}.plans{grid-template-columns:1fr}.plans article{padding:30px 24px}.contact-layout form{padding:24px 18px}.final-section{padding-block:110px}.final-section h2{font-size:3.8rem}.final-section>div{flex-direction:column}.footer-inner>div{flex-wrap:wrap}}
@media(prefers-reduced-motion:reduce){:global(html){scroll-behavior:auto}[data-reveal]{opacity:1;transform:none;transition:none}.button{transition:none}}
</style>
