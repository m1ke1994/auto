<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
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

import { applyPublicSiteSeo, ensurePublicSiteTracker, loadTrackNodePublicSite } from '../api/publicSite'

const mobileMenuOpen = ref(false)
const activeSection = ref('features')
const activePricingDuration = ref('')
const openFaq = ref(0)
const site = ref(null)
const sections = ref([])
const loading = ref(true)
const loadError = ref('')
let sectionObserver
let statsAnimationFrame
let statsUpdateTimer

const liveStats = reactive({
  visitors: 0,
  views: 0,
  leads: 0,
  conversion: 0,
})

const iconMap = {
  analytics: BarChart3,
  bell: BellRing,
  blocks: Blocks,
  check: CheckCircle2,
  click: MousePointerClick,
  device: Smartphone,
  funnel: Funnel,
  inbox: Inbox,
  report: FileText,
  route: Route,
  search: FileSearch,
  seo: SearchCheck,
  sparkles: Sparkles,
  zap: Zap,
}

const sectionsByKey = computed(() => Object.fromEntries(sections.value.map((section) => [section.key, section])))
const sectionContent = (key) => sectionsByKey.value[key]?.content || {}
const sectionOrder = (key) => Number(sectionsByKey.value[key]?.order || 0)
const hasSection = (key) => Boolean(sectionsByKey.value[key])
const resolveIcon = (name) => iconMap[name] || Blocks

const navigation = computed(() => sectionContent('navigation'))
const hero = computed(() => sectionContent('hero'))
const featuresSection = computed(() => sectionContent('features'))
const analyticsSection = computed(() => sectionContent('analytics'))
const seoSection = computed(() => sectionContent('seo_analysis'))
const tariffsSection = computed(() => sectionContent('tariffs'))
const faqSection = computed(() => sectionContent('faq'))
const finalCta = computed(() => sectionContent('final_cta'))
const footer = computed(() => sectionContent('footer'))

const navItems = computed(() => navigation.value.left_links || [])
const rightNavItems = computed(() => navigation.value.right_links || [])
const heroBenefits = computed(() => (hero.value.benefits || []).map((item) => ({ ...item, icon: resolveIcon(item.icon) })))
const heroStats = computed(() => hero.value.stats || [])
const featurePromises = computed(() => (featuresSection.value.promises || []).map((item) => ({ ...item, icon: resolveIcon(item.icon) })))
const features = computed(() => (featuresSection.value.items || []).map((item) => ({ ...item, icon: resolveIcon(item.icon), type: item.visual_type })))
const ecosystemItems = computed(() => (analyticsSection.value.items || []).map((item) => ({ ...item, icon: resolveIcon(item.icon) })))
const seoChecks = computed(() => seoSection.value.checks || [])
const pricingTabs = computed(() => tariffsSection.value.tabs || [])
const pricingPlans = computed(() => tariffsSection.value.plans || [])
const visiblePlans = computed(() => pricingPlans.value.filter((plan) => plan.duration === activePricingDuration.value))
const faqItems = computed(() => faqSection.value.items || [])

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function formatInteger(value) {
  return Math.round(value).toLocaleString('ru-RU')
}

function formatConversion(value) {
  return Number(value).toFixed(2)
}

function formatStat(stat) {
  const value = liveStats[stat.key] || 0
  return stat.format === 'percent' ? `${formatConversion(value)}%` : formatInteger(value)
}

function statByKey(key) {
  return heroStats.value.find((item) => item.key === key) || { key, label: '', delta: '', format: 'integer' }
}

function startLiveUpdates() {
  statsUpdateTimer = window.setInterval(() => {
    liveStats.visitors += 1 + Math.floor(Math.random() * 3)
    liveStats.views += 3 + Math.floor(Math.random() * 5)
    if (Math.random() > 0.55) liveStats.leads += 1
    const conversionTarget = Number(heroStats.value.find((item) => item.key === 'conversion')?.target || 0)
    liveStats.conversion = Math.min(conversionTarget + 0.12, Math.max(conversionTarget - 0.07, liveStats.conversion + (Math.random() - 0.48) * 0.012))
  }, 2800)
}

function animateStats() {
  const targets = Object.fromEntries(heroStats.value.map((item) => [item.key, Number(item.target || 0)]))
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    Object.assign(liveStats, targets)
    return
  }

  const startedAt = performance.now()
  const duration = 1600

  const update = (now) => {
    const progress = Math.min((now - startedAt) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    for (const key of Object.keys(liveStats)) liveStats[key] = Number(targets[key] || 0) * eased

    if (progress < 1) statsAnimationFrame = requestAnimationFrame(update)
    else startLiveUpdates()
  }

  statsAnimationFrame = requestAnimationFrame(update)
}

function setupSectionObserver() {
  const sections = [...navItems.value, ...rightNavItems.value]
    .map((item) => document.getElementById(item.section_id))
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
}

onMounted(async () => {
  try {
    const payload = await loadTrackNodePublicSite()
    site.value = payload.site
    sections.value = [...payload.sections].sort((left, right) => Number(left.order) - Number(right.order))
    activePricingDuration.value = pricingTabs.value[0]?.id || ''
    applyPublicSiteSeo(site.value)
    ensurePublicSiteTracker(site.value)
    await nextTick()
    setupSectionObserver()
    animateStats()
  } catch (error) {
    loadError.value = error?.message || 'Не удалось загрузить данные лендинга из ядра.'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  sectionObserver?.disconnect()
  cancelAnimationFrame(statsAnimationFrame)
  window.clearInterval(statsUpdateTimer)
})
</script>

<template>
  <div class="landing-page">
    <div v-if="loading" class="landing-state" role="status">Загружаем TrackNode…</div>
    <div v-else-if="loadError" class="landing-state landing-state-error" role="alert">
      <strong>Лендинг временно недоступен</strong>
      <span>{{ loadError }}</span>
    </div>
    <template v-else>
    <header v-if="hasSection('navigation')" class="landing-header">
      <nav class="nav-shell" aria-label="Основная навигация">
        <div class="nav-side nav-left">
          <a
            v-for="item in navItems"
            :key="item.href"
            :href="item.href"
            class="nav-link"
            :class="{ active: activeSection === item.section_id }"
          >{{ item.label }}</a>
        </div>

        <a class="brand" href="#top" :aria-label="`${navigation.brand_name} — на главную`">
          <span class="brand-cube" aria-hidden="true">
            <img src="/images/landing/cube.png" :alt="navigation.cube_alt" />
          </span>
          <span class="brand-copy">
            <span class="brand-kicker">{{ navigation.brand_kicker }}</span>
            <span class="brand-line">{{ navigation.brand_name.slice(0, -4) }}<span>{{ navigation.brand_name.slice(-4) }}</span></span>
          </span>
        </a>

        <div class="nav-side nav-right">
          <a
            v-for="item in rightNavItems"
            :key="item.href"
            :href="item.href"
            class="nav-link"
            :class="{ active: activeSection === item.section_id }"
          >{{ item.label }}</a>
          <a class="login-button" :href="navigation.login_route">{{ navigation.login_label }} <ArrowRight :size="17" /></a>
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
        <a :href="navigation.login_route" class="login-button" @click="closeMobileMenu">{{ navigation.login_label }} <ArrowRight :size="17" /></a>
      </div>
    </header>

    <main id="top" class="landing-main">
      <section v-if="hasSection('hero')" class="hero-section" aria-labelledby="hero-title" :style="{ order: sectionOrder('hero') }">
        <div class="ambient ambient-one"></div>
        <div class="ambient ambient-two"></div>
        <div class="landing-container hero-grid">
          <div class="hero-copy">
            <p class="eyebrow"><BarChart3 :size="15" /> {{ hero.eyebrow }}</p>
            <h1 id="hero-title">{{ hero.title_line_1 }}<br />{{ hero.title_line_2 }}<br /><span>{{ hero.title_accent }}</span></h1>
            <p class="hero-lead">{{ hero.description }}</p>
            <div class="hero-actions">
              <a class="primary-button" :href="hero.primary_route">{{ hero.primary_label }} <Zap :size="18" /></a>
              <a class="secondary-button" :href="hero.secondary_href"><span class="play">▶</span> {{ hero.secondary_label }}</a>
            </div>
            <div class="hero-benefits">
              <div v-for="item in heroBenefits" :key="item.label" class="hero-benefit">
                <span><component :is="item.icon" :size="16" /></span>
                {{ item.label }}
              </div>
            </div>
          </div>

          <div class="hero-visual" aria-label="Визуализация аналитики TrackNode">
            <div class="hero-orbit orbit-a"></div>
            <div class="hero-orbit orbit-b"></div>
            <div class="cube-stage"></div>
            <img class="hero-cube" src="/images/landing/cube.png" :alt="hero.cube_alt" />
            <article class="float-card visitors-card">
              <small>{{ hero.visitors_card_label }}</small><strong class="live-number">{{ formatInteger(liveStats.visitors) }} <em>{{ statByKey('visitors').delta }}</em></strong>
              <svg viewBox="0 0 190 45" aria-hidden="true"><path d="M2 36 24 26 45 34 66 18 88 29 110 17 134 30 160 20 188 6" /></svg>
            </article>
            <article class="float-card conversion-card">
              <small>{{ hero.conversion_card_label }}</small><strong class="live-number">{{ formatConversion(liveStats.conversion) }}% <em>{{ statByKey('conversion').delta }}</em></strong>
              <div class="donut"></div>
            </article>
            <article class="float-card heat-card">
              <small>{{ hero.heatmap_card_label }}</small>
              <div class="mini-heat"><i></i><i></i><i></i><i></i></div>
            </article>
            <article class="float-card traffic-card">
              <small>{{ hero.traffic_card_label }}</small>
              <span><i style="width: 84%"></i></span><span><i style="width: 61%"></i></span><span><i style="width: 42%"></i></span>
            </article>
          </div>
        </div>
        <div class="landing-container metrics-strip">
          <div v-for="stat in heroStats" :key="stat.key"><component :is="resolveIcon(stat.icon)" :size="20" /><span><strong class="live-number">{{ formatStat(stat) }}</strong><small>{{ stat.label }} <em>{{ stat.delta }}</em></small></span></div>
        </div>
      </section>

      <section v-if="hasSection('features')" id="features" class="section features-section" aria-labelledby="features-title" :style="{ order: sectionOrder('features') }">
        <div class="landing-container">
          <div class="features-heading">
            <div>
              <p class="eyebrow"><Zap :size="15" /> {{ featuresSection.eyebrow }}</p>
              <h2 id="features-title">{{ featuresSection.title }}<br />{{ featuresSection.title_line_2 }} <span>{{ featuresSection.title_accent }}</span></h2>
              <p>{{ featuresSection.description }}</p>
            </div>
            <div class="feature-promises">
              <div v-for="item in featurePromises" :key="item.title"><component :is="item.icon" :size="22" /><span><strong>{{ item.title }}</strong><small>{{ item.text }}</small></span></div>
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
                  <strong class="live-number">{{ formatInteger(liveStats.visitors) }} <em>{{ statByKey('visitors').delta }}</em></strong><svg viewBox="0 0 160 60"><path d="M2 48 24 35 46 44 70 25 92 39 115 18 138 31 158 10" /></svg>
                </template>
                <template v-else-if="feature.type === 'heatmap'">
                  <div class="feature-heat"><i></i><i></i><i></i><i></i><i></i></div>
                </template>
                <template v-else-if="feature.type === 'funnel'">
                  <i class="funnel-layer"></i><i class="funnel-layer"></i><i class="funnel-layer"></i><i class="funnel-layer"></i>
                </template>
                <template v-else-if="feature.type === 'score'">
                  <div class="score-ring" :style="{ '--health-score': `${feature.visual_items?.[0]?.label || 0}%` }"><strong>{{ feature.visual_items?.[0]?.label }}</strong><small>{{ feature.visual_items?.[1]?.label }}</small></div>
                </template>
                <template v-else-if="feature.type === 'compare'">
                  <span v-for="width in [92, 74, 58, 41]" :key="width"><i :style="{ width: `${width}%` }"></i></span>
                </template>
                <template v-else-if="feature.type === 'alerts'">
                  <p v-for="(item, index) in feature.visual_items" :key="item.label"><i :class="`alert-${index}`"></i>{{ item.label }}</p>
                </template>
                <template v-else-if="feature.type === 'reports'">
                  <span v-for="(item, index) in feature.visual_items" :key="item.label" class="report-file" :class="{ green: index === 1 }">{{ item.label }}</span>
                </template>
                <template v-else-if="feature.type === 'devices'">
                  <div class="device-donut"></div><p><template v-for="item in feature.visual_items" :key="item.label">{{ item.label }}<br /></template></p>
                </template>
                <template v-else>
                  <strong class="ai-growth">{{ feature.visual_items?.[0]?.label }}</strong><svg viewBox="0 0 160 60"><path d="M2 52 28 42 51 48 78 20 101 36 128 8 158 17" /></svg>
                </template>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section v-if="hasSection('analytics')" id="ecosystem" class="section ecosystem-section" aria-labelledby="ecosystem-title" :style="{ order: sectionOrder('analytics') }">
        <div class="landing-container">
          <div class="section-heading centered">
            <p class="eyebrow"><Blocks :size="15" /> {{ analyticsSection.eyebrow }}</p>
            <h2 id="ecosystem-title">{{ analyticsSection.title }} <span>{{ analyticsSection.title_accent }}</span></h2>
            <p>{{ analyticsSection.description }}</p>
          </div>

          <div class="ecosystem-canvas">
            <div class="orbit-line orbit-line-1"></div>
            <div class="orbit-line orbit-line-2"></div>
            <div class="orbit-line orbit-line-3"></div>
            <div class="orbit-glow"></div>
            <div class="ecosystem-cube-wrap">
              <img src="/images/landing/cube.png" :alt="analyticsSection.cube_alt" />
            </div>
            <div class="ecosystem-nodes">
              <article v-for="item in ecosystemItems" :key="item.title" class="ecosystem-node" :class="item.position" tabindex="0">
                <div class="ecosystem-node-content">
                  <component :is="item.icon" :size="26" />
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.text }}</span>
                </div>
              </article>
            </div>
          </div>

          <div class="ecosystem-mobile-grid">
            <article v-for="item in ecosystemItems" :key="`mobile-${item.title}`">
              <component :is="item.icon" :size="22" /><span><strong>{{ item.title }}</strong><small>{{ item.text }}</small></span>
            </article>
          </div>
        </div>
      </section>

      <section v-if="hasSection('seo_analysis')" id="seo-audit" class="section seo-section" aria-labelledby="seo-title" :style="{ order: sectionOrder('seo_analysis') }">
        <div class="landing-container seo-grid">
          <div class="seo-copy">
            <p class="eyebrow"><SearchCheck :size="15" /> {{ seoSection.eyebrow }}</p>
            <h2 id="seo-title">{{ seoSection.title }} <span>{{ seoSection.title_accent }}</span></h2>
            <p>{{ seoSection.description }}</p>
            <div class="seo-summary">
              <div v-for="item in seoSection.summary" :key="item.label"><strong>{{ item.value }}</strong><small>{{ item.label }}</small></div>
            </div>
            <a class="primary-button" :href="seoSection.cta_route">{{ seoSection.cta_label }} <ArrowRight :size="18" /></a>
          </div>

          <div class="seo-dashboard">
            <div class="browser-bar"><i></i><i></i><i></i><span>{{ seoSection.dashboard_domain }}</span><SearchCheck :size="17" /></div>
            <div class="seo-dashboard-body">
              <div class="health-card">
                <div class="health-ring" :style="{ '--health-score': `${seoSection.health_value}%` }"><span><strong>{{ seoSection.health_value }}</strong><small>{{ seoSection.health_scale }}</small></span></div>
                <div><small>{{ seoSection.health_label }}</small><strong>{{ seoSection.health_status }}</strong><p>{{ seoSection.health_description }}</p></div>
              </div>
              <div class="seo-checks">
                <div v-for="item in seoChecks" :key="item.label" :class="`status-${item.status}`">
                  <span><CheckCircle2 v-if="item.status === 'ok'" :size="17" /><Zap v-else-if="item.status === 'warn'" :size="17" /><X v-else :size="17" /></span>
                  <strong>{{ item.label }}</strong><small>{{ item.result }}</small>
                </div>
              </div>
              <div class="ai-recommendation">
                <span><Sparkles :size="22" /></span>
                <div><small>{{ seoSection.recommendation_label }}</small><strong>{{ seoSection.recommendation_title }}</strong><p>{{ seoSection.recommendation_text }}</p></div>
                <ArrowRight :size="20" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="hasSection('tariffs')" id="pricing" class="section pricing-section" aria-labelledby="pricing-title" :style="{ order: sectionOrder('tariffs') }">
        <div class="landing-container">
          <div class="section-heading centered">
            <p class="eyebrow"><Zap :size="15" /> {{ tariffsSection.eyebrow }}</p>
            <h2 id="pricing-title">{{ tariffsSection.title }} <span>{{ tariffsSection.title_accent }}</span></h2>
            <p>{{ tariffsSection.description }}</p>
          </div>
          <div class="pricing-tabs" role="tablist" aria-label="Период оплаты">
            <button v-for="tab in pricingTabs" :key="tab.id" type="button" :class="{ active: activePricingDuration === tab.id }" @click="activePricingDuration = tab.id">
              {{ tab.label }} <small v-if="tab.saving">{{ tab.saving }}</small>
            </button>
          </div>
          <div class="pricing-grid">
            <article v-for="plan in visiblePlans" :key="`${plan.duration}-${plan.title}`" class="pricing-card" :class="{ featured: plan.featured }">
              <span v-if="plan.featured" class="popular">{{ tariffsSection.popular_label }}</span>
              <p class="pricing-label">{{ plan.title }}</p>
              <div class="price"><strong>{{ plan.price }} ₽</strong><small>{{ plan.period }}</small></div>
              <p>{{ plan.description }}</p>
              <ul><li v-for="item in plan.features" :key="item.label"><CheckCircle2 :size="18" />{{ item.label }}</li></ul>
              <a :class="plan.featured ? 'primary-button' : 'secondary-button'" :href="tariffsSection.cta_route">{{ tariffsSection.cta_label }} <ArrowRight :size="17" /></a>
            </article>
          </div>
        </div>
      </section>

      <section v-if="hasSection('faq')" id="faq" class="section faq-section" aria-labelledby="faq-title" :style="{ order: sectionOrder('faq') }">
        <div class="landing-container faq-layout">
          <div class="faq-heading"><p class="eyebrow">{{ faqSection.eyebrow }}</p><h2 id="faq-title">{{ faqSection.title }}</h2><p>{{ faqSection.description }}</p></div>
          <div class="faq-list">
            <article v-for="(item, index) in faqItems" :key="item.question" :class="{ open: openFaq === index }">
              <button type="button" :aria-expanded="openFaq === index" @click="openFaq = openFaq === index ? -1 : index"><span>{{ item.question }}</span><span>+</span></button>
              <div v-show="openFaq === index"><p>{{ item.answer }}</p></div>
            </article>
          </div>
        </div>
      </section>

      <section v-if="hasSection('final_cta')" class="final-cta" :style="{ order: sectionOrder('final_cta') }">
        <div class="landing-container final-cta-inner">
          <div><p>{{ finalCta.eyebrow }}</p><h2>{{ finalCta.title }}</h2></div>
          <a class="cta-white" :href="finalCta.button_route">{{ finalCta.button_label }} <ArrowRight :size="18" /></a>
        </div>
      </section>
    </main>

    <footer v-if="hasSection('footer')" class="landing-footer">
      <div class="landing-container footer-grid">
        <a class="footer-brand" href="#top"><span><img src="/images/landing/cube.png" :alt="footer.cube_alt" /></span>{{ footer.brand_name }}</a>
        <p>{{ footer.description }}</p>
        <div><a v-for="link in footer.links" :key="link.href" :href="link.href">{{ link.label }}</a></div>
        <small>© {{ new Date().getFullYear() }} {{ footer.copyright }}</small>
      </div>
    </footer>
    </template>
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

.landing-main { display: flex; flex-direction: column; }
.landing-state { min-height: 100vh; display: grid; place-content: center; gap: 8px; padding: 24px; text-align: center; color: var(--muted); }
.landing-state-error strong { color: var(--ink); font-size: 1.1rem; }

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
.brand { display: flex; min-width: 230px; align-items: center; justify-content: center; gap: 10px; padding: 0 24px; color: var(--ink); text-align: left; text-decoration: none; }
.brand-copy { display: grid; align-content: center; }
.brand-kicker { color: #777c91; font-size: .68rem; font-weight: 800; letter-spacing: .09em; line-height: 1; text-transform: uppercase; }
.brand-line { display: block; margin-top: 3px; font-size: 1.78rem; font-weight: 900; letter-spacing: -.055em; line-height: 1; }
.brand-line > span { color: var(--purple); }
.brand-cube { position: relative; display: block; width: 46px; height: 46px; flex: 0 0 46px; overflow: hidden; }
.brand-cube img { position: absolute; top: 50%; left: 50%; width: 66px; max-width: none; height: 66px; object-fit: cover; transform: translate(-50%,-50%); }
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
.hero-cube { position: absolute; z-index: 2; top: 50%; left: 50%; width: min(520px, 68%); aspect-ratio: 1; object-fit: contain; pointer-events: none; filter: saturate(1.06) drop-shadow(0 0 34px rgba(103,66,255,.35)) drop-shadow(0 30px 28px rgba(71,38,230,.16)); transform: translate(-48%,-49%); -webkit-mask-image: radial-gradient(circle, #000 42%, rgba(0,0,0,.92) 57%, transparent 74%); mask-image: radial-gradient(circle, #000 42%, rgba(0,0,0,.92) 57%, transparent 74%); }
.cube-stage { position: absolute; z-index: 1; left: 50%; bottom: 70px; width: 370px; height: 120px; border: 2px solid rgba(90,56,255,.28); border-radius: 50%; background: radial-gradient(ellipse, rgba(87,51,255,.38), rgba(255,255,255,.3) 46%, transparent 72%); box-shadow: 0 20px 55px rgba(67,36,227,.22), inset 0 0 25px white; transform: translateX(-50%); }
.hero-orbit { position: absolute; top: 50%; left: 50%; border: 1px solid rgba(93,62,255,.17); border-radius: 50%; transform: translate(-50%,-50%) rotate(-10deg); }
.orbit-a { width: 96%; height: 49%; }
.orbit-b { width: 78%; height: 38%; transform: translate(-50%,-50%) rotate(18deg); }
.float-card { position: absolute; z-index: 4; min-width: 180px; padding: 16px 18px; border: 1px solid rgba(255,255,255,.9); border-radius: 18px; cursor: default; background: rgba(255,255,255,.72); box-shadow: 0 18px 50px rgba(63,43,145,.13), inset 0 0 0 1px rgba(84,58,255,.06); backdrop-filter: blur(15px); transition: border-color .25s ease, box-shadow .25s ease; animation: cardFloat 5s ease-in-out infinite; }
.float-card:hover { border-color: rgba(93,59,255,.28); box-shadow: 0 22px 58px rgba(63,43,145,.2),0 0 24px rgba(99,64,255,.12); animation-play-state: paused; }
.float-card small { display: block; margin-bottom: 9px; color: #666c84; font-weight: 700; }
.float-card strong { font-size: 1.25rem; }
.live-number { display: inline-block; min-width: 3ch; font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
.float-card em, .metrics-strip em, .feature-mini em { color: #0cab79; font-size: .66rem; font-style: normal; }
.visitors-card { top: 40px; left: 6%; }
.visitors-card svg, .feature-mini svg { display: block; width: 100%; margin-top: 8px; fill: none; stroke: #5535ff; stroke-width: 3; }
.visitors-card svg path, .feature-mini svg path { stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 300; stroke-dashoffset: 300; animation: chartDraw 4.2s ease-in-out infinite; }
.conversion-card { bottom: 120px; left: 2%; animation-delay: -2s; }
.donut { width: 54px; height: 54px; margin-top: 9px; border-radius: 50%; background: conic-gradient(var(--purple) 0 72%, #e7e4ff 72%); -webkit-mask: radial-gradient(circle, transparent 45%, #000 47%); mask: radial-gradient(circle, transparent 45%, #000 47%); animation: ringGlow 2.8s ease-in-out infinite; }
.heat-card { top: 70px; right: 0; width: 218px; animation-delay: -1.2s; }
.mini-heat, .feature-heat { position: relative; height: 82px; overflow: hidden; border-radius: 11px; background: linear-gradient(135deg, #e6e4ff, #eff8ff); }
.mini-heat i, .feature-heat i { position: absolute; width: 32px; height: 32px; border-radius: 50%; background: #ffdf36; filter: blur(8px); }
.mini-heat i:nth-child(1), .feature-heat i:nth-child(1) { top: 32%; left: 44%; background: #ff432f; }
.mini-heat i:nth-child(2), .feature-heat i:nth-child(2) { top: 10%; left: 20%; background: #5ce070; }
.mini-heat i:nth-child(3), .feature-heat i:nth-child(3) { right: 13%; bottom: 5%; }
.mini-heat i:nth-child(4), .feature-heat i:nth-child(4) { bottom: 4%; left: 32%; background: #72de77; }
.mini-heat i, .feature-heat i { animation: heatPoint 2.6s ease-in-out infinite; }.mini-heat i:nth-child(2),.feature-heat i:nth-child(2){animation-delay:-.65s}.mini-heat i:nth-child(3),.feature-heat i:nth-child(3){animation-delay:-1.3s}.mini-heat i:nth-child(4),.feature-heat i:nth-child(4){animation-delay:-1.95s}
.traffic-card { right: 4%; bottom: 72px; width: 210px; animation-delay: -3.1s; }
.traffic-card > span, .visual-compare .feature-mini > span { display: block; height: 7px; margin: 9px 0; overflow: hidden; border-radius: 99px; background: #e9e7fa; }
.traffic-card i, .visual-compare .feature-mini i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #826aff, #4b2cff, #9b87ff, #4b2cff); background-size: 220% 100%; animation: barFlow 2.8s linear infinite; }
.metrics-strip { position: relative; z-index: 6; display: grid; grid-template-columns: repeat(4,1fr); margin-top: 16px; padding: 24px 8px; border-top: 1px solid var(--line); }
.metrics-strip > div { display: flex; align-items: center; gap: 15px; padding: 4px 26px; border-right: 1px solid var(--line); border-radius: 14px; color: var(--purple); transition: background-color .25s ease, box-shadow .25s ease, transform .25s ease; }
.metrics-strip > div:hover { background: rgba(255,255,255,.74); box-shadow: 0 12px 30px rgba(61,43,132,.09); transform: translateY(-3px); }
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
.score-ring, .device-donut { display: grid; width: 92px; height: 92px; margin: auto; place-items: center; border-radius: 50%; background: conic-gradient(#23c48a 0 var(--health-score, 87%),#eceafb var(--health-score, 87%)); -webkit-mask: radial-gradient(circle,transparent 54%,#000 56%); mask: radial-gradient(circle,transparent 54%,#000 56%); }
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
.orbit-line-1 { width: 52%; height: 37%; }.orbit-line-2{width:76%;height:57%;transform:translate(-50%,-50%) rotate(7deg)}.orbit-line-3{width:96%;height:78%;transform:translate(-50%,-50%) rotate(-4deg)}
.orbit-glow { position: absolute; top: 50%; left: 50%; width: 470px; height: 170px; border: 2px solid rgba(95,61,255,.25); border-radius: 50%; background: radial-gradient(ellipse,rgba(99,58,255,.25),transparent 68%); box-shadow: 0 20px 55px rgba(75,39,239,.2),inset 0 0 30px white; transform: translate(-50%,55%); }
.ecosystem-cube-wrap { position: absolute; z-index: 3; top: 50%; left: 50%; width: 350px; height: 350px; pointer-events: none; transform: translate(-50%,-55%); }
.ecosystem-cube-wrap img { display: block; width: 100%; height: 100%; object-fit: contain; filter: saturate(1.08) drop-shadow(0 0 30px rgba(103,66,255,.38)) drop-shadow(0 23px 28px rgba(71,38,230,.18)); -webkit-mask-image: radial-gradient(circle, #000 42%, rgba(0,0,0,.92) 57%, transparent 74%); mask-image: radial-gradient(circle, #000 42%, rgba(0,0,0,.92) 57%, transparent 74%); }
.ecosystem-nodes { position: absolute; z-index: 5; inset: 0; }
.ecosystem-node { position: absolute; width: 176px; height: 142px; outline: none; }
.ecosystem-node-content { position: relative; display: grid; width: 100%; height: 100%; place-items: center; padding: 20px 18px; border: 1px solid rgba(255,255,255,.92); border-radius: 20px; color: var(--purple); text-align: center; background: rgba(255,255,255,.78); box-shadow: 0 15px 43px rgba(61,43,132,.12),inset 0 0 0 1px rgba(83,56,230,.06); backdrop-filter: blur(14px); transition: border-color .3s ease, box-shadow .3s ease, transform .3s ease; animation: nodePulse 3.8s ease-in-out infinite; }
.ecosystem-node strong { display: block; max-width: 100%; color: var(--ink); font-size: .84rem; line-height: 1.25; overflow-wrap: anywhere; }
.ecosystem-node span { position: absolute; z-index: 4; top: calc(100% - 6px); left: 50%; width: 210px; max-width: min(210px, calc(100vw - 32px)); padding: 11px 13px; border-radius: 11px; color: white; background: #21175b; box-shadow: 0 12px 30px rgba(33,23,91,.22); font-size: .7rem; line-height: 1.45; overflow-wrap: anywhere; opacity: 0; pointer-events: none; transform: translate(-50%,8px); transition: .25s ease; }
.ecosystem-node:hover, .ecosystem-node:focus { z-index: 8; }
.ecosystem-node:hover .ecosystem-node-content, .ecosystem-node:focus .ecosystem-node-content { border-color: rgba(91,56,255,.32); box-shadow: 0 20px 52px rgba(61,43,132,.2),0 0 30px rgba(99,64,255,.18); transform: translateY(-6px) scale(1.04); animation: none; }
.ecosystem-node:hover span, .ecosystem-node:focus span { opacity: 1; transform: translate(-50%,0); }
.p1{top:0;left:calc(50% - 88px)}.p2{top:8%;right:18%}.p3{top:29%;right:2%}.p4{right:2%;bottom:23%}.p5{right:18%;bottom:1%}.p6{bottom:-2%;left:calc(50% - 88px)}.p7{bottom:1%;left:18%}.p8{bottom:23%;left:2%}.p9{top:29%;left:2%}.p10{top:8%;left:18%}
.p8 strong{font-size:.72rem;letter-spacing:-.02em;overflow-wrap:normal}
.p2 .ecosystem-node-content,.p7 .ecosystem-node-content{animation-delay:-.75s}.p3 .ecosystem-node-content,.p8 .ecosystem-node-content{animation-delay:-1.5s}.p4 .ecosystem-node-content,.p9 .ecosystem-node-content{animation-delay:-2.25s}.p5 .ecosystem-node-content,.p10 .ecosystem-node-content{animation-delay:-3s}
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
.health-ring { display:grid;width:120px;height:120px;place-items:center;border-radius:50%;background:conic-gradient(#4b2cff 0 var(--health-score, 87%),#e9e7fa var(--health-score, 87%));position:relative}.health-ring::after{position:absolute;inset:12px;border-radius:50%;background:#fff;content:''}.health-ring span{position:relative;z-index:2;text-align:center}.health-ring strong,.health-ring small{display:block}.health-ring strong{font-size:2rem}.health-card > div:last-child > small{color:var(--purple);font-weight:800;text-transform:uppercase}.health-card > div:last-child > strong{display:block;margin-top:5px;font-size:1.1rem}.health-card p{margin:7px 0 0;color:var(--muted);font-size:.73rem;line-height:1.55}
.seo-checks { display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:12px 0}.seo-checks > div{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:9px;padding:10px;border:1px solid var(--line);border-radius:11px;background:#fff}.seo-checks > div > span{display:grid;width:29px;height:29px;place-items:center;border-radius:8px}.seo-checks strong{font-size:.7rem}.seo-checks small{font-size:.6rem}.status-ok > span,.status-ok small{color:#0da777;background:#e8fbf4}.status-warn > span,.status-warn small{color:#c78109;background:#fff6dd}.status-error > span,.status-error small{color:#dc4755;background:#fff0f1}.seo-checks small{padding:4px 6px;border-radius:6px;background:transparent}
.ai-recommendation { display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:13px;padding:15px;border-radius:15px;color:white;background:linear-gradient(130deg,#271174,#5a31e8);box-shadow:0 14px 28px rgba(63,31,199,.22)}.ai-recommendation > span{display:grid;width:42px;height:42px;place-items:center;border-radius:12px;background:rgba(255,255,255,.14)}.ai-recommendation small,.ai-recommendation strong{display:block}.ai-recommendation small{color:#c9bdff;font-size:.6rem;text-transform:uppercase}.ai-recommendation strong{margin-top:3px;font-size:.8rem}.ai-recommendation p{margin:4px 0 0;color:#ded8ff;font-size:.63rem}

.pricing-section { background: linear-gradient(180deg,#faf9ff,#fff); }
.pricing-tabs { display:flex;width:max-content;max-width:100%;margin:-20px auto 38px;padding:5px;border:1px solid var(--line);border-radius:15px;background:white;box-shadow:0 10px 30px rgba(61,43,132,.08)}
.pricing-tabs button { min-height:44px;padding:0 20px;border:0;border-radius:11px;color:var(--muted);background:transparent;font-weight:750}.pricing-tabs button.active{color:white;background:var(--purple);box-shadow:0 8px 18px rgba(75,44,255,.25)}.pricing-tabs small{margin-left:4px;padding:3px 5px;border-radius:5px;color:#0a9b71;background:#e8fbf4}.pricing-tabs button.active small{color:white;background:rgba(255,255,255,.18)}
.pricing-grid { display:grid;grid-template-columns:repeat(2,minmax(0,480px));justify-content:center;gap:20px}.pricing-card{position:relative;padding:32px;border:1px solid var(--line);border-radius:23px;background:rgba(255,255,255,.84);box-shadow:0 18px 50px rgba(61,43,132,.09)}.pricing-card.featured{color:white;border-color:transparent;background:linear-gradient(145deg,#271174,#5430df);box-shadow:0 25px 60px rgba(63,31,199,.25)}.popular{position:absolute;top:20px;right:20px;padding:6px 9px;border-radius:99px;color:#4b2cff;background:#fff;font-size:.62rem;font-weight:850;text-transform:uppercase}.pricing-label{margin:0;font-weight:850}.price{margin:20px 0}.price strong,.price small{display:block}.price strong{font-size:2.5rem;letter-spacing:-.04em}.price small{margin-top:4px;color:var(--muted)}.featured .price small,.featured > p{color:#d8d1ff}.pricing-card ul{display:grid;gap:12px;margin:25px 0;padding:0;list-style:none}.pricing-card li{display:flex;gap:9px;font-size:.84rem}.pricing-card li svg{flex:0 0 auto;color:#6f54ff}.featured li svg{color:#bcb0ff}.pricing-card .primary-button,.pricing-card .secondary-button{width:100%;margin-top:5px}.pricing-card.featured .primary-button{color:var(--purple);background:white;box-shadow:none}

.faq-section { background:#fff }.faq-layout{display:grid;grid-template-columns:.65fr 1.35fr;gap:80px}.faq-heading h2{margin:17px 0;font-size:clamp(2.2rem,3.5vw,3.4rem);letter-spacing:-.05em}.faq-heading > p:last-child{color:var(--muted);line-height:1.65}.faq-list{display:grid;gap:10px}.faq-list article{border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:0 8px 26px rgba(61,43,132,.05)}.faq-list article.open{border-color:rgba(75,44,255,.25)}.faq-list button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:20px;padding:20px 22px;border:0;color:var(--ink);text-align:left;background:transparent;font-weight:800}.faq-list button span:last-child{display:grid;width:31px;height:31px;flex:0 0 auto;place-items:center;border-radius:50%;color:var(--purple);background:#f0edff;font-size:1.25rem;transition:.25s ease}.faq-list article.open button span:last-child{color:white;background:var(--purple);transform:rotate(45deg)}.faq-list article > div p{margin:0;padding:0 22px 20px;color:var(--muted);line-height:1.7}
.final-cta{padding:35px 0 70px;background:#fff}.final-cta-inner{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:40px 45px;border-radius:24px;color:white;background:radial-gradient(circle at 18% 0,rgba(145,121,255,.55),transparent 35%),linear-gradient(110deg,#241072,#4c28d5);box-shadow:0 25px 60px rgba(63,31,199,.23)}.final-cta p{margin:0;color:#cfc7ff;font-weight:750}.final-cta h2{max-width:800px;margin:8px 0 0;font-size:clamp(1.8rem,3vw,2.8rem);line-height:1.1;letter-spacing:-.04em}.cta-white{flex:0 0 auto;color:var(--purple);background:white;box-shadow:0 12px 26px rgba(20,10,70,.18)}.cta-white:hover{transform:translateY(-2px)}
.landing-footer{padding:48px 0 30px;color:#c6c9d7;background:#0d1022}.footer-grid{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:30px}.footer-brand{display:flex;align-items:center;gap:10px;color:white;font-size:1.35rem;font-weight:900;text-decoration:none}.footer-brand span{position:relative;width:36px;height:36px;overflow:hidden}.footer-brand img{position:absolute;top:50%;left:50%;width:52px;max-width:none;height:52px;object-fit:cover;transform:translate(-50%,-50%)}.footer-grid p{font-size:.82rem}.footer-grid > div{display:flex;gap:20px}.footer-grid a{color:#dfe1eb;text-decoration:none;font-size:.78rem}.footer-grid a:hover{color:white}.footer-grid > small{grid-column:1/-1;padding-top:25px;border-top:1px solid rgba(255,255,255,.1);color:#777d94}

@keyframes cardFloat { 0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)} }
@keyframes chartDraw { 0%{stroke-dashoffset:300;opacity:.35}45%,82%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:-24;opacity:.55} }
@keyframes barFlow { to{background-position:-220% 0} }
@keyframes heatPoint { 0%,100%{opacity:.55;transform:scale(.82)}50%{opacity:1;transform:scale(1.18)} }
@keyframes ringGlow { 0%,100%{filter:drop-shadow(0 0 0 rgba(75,44,255,0))}50%{filter:drop-shadow(0 0 7px rgba(75,44,255,.35))} }
@keyframes nodePulse { 0%,100%{border-color:rgba(255,255,255,.92);box-shadow:0 15px 43px rgba(61,43,132,.1),inset 0 0 0 1px rgba(83,56,230,.05)}50%{border-color:rgba(112,82,255,.27);box-shadow:0 18px 48px rgba(61,43,132,.16),0 0 26px rgba(99,64,255,.13),inset 0 0 0 1px rgba(83,56,230,.1)} }

@media (max-width: 1180px) {
  .nav-shell{grid-template-columns:1fr auto}.nav-side{display:none}.brand{justify-self:start;padding:0;min-width:0}.menu-button{display:grid;justify-self:end}.mobile-menu{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px;padding:16px;border:1px solid rgba(255,255,255,.9);border-radius:20px;background:rgba(255,255,255,.92);box-shadow:0 18px 50px rgba(61,43,132,.15);backdrop-filter:blur(20px)}.mobile-menu > a:not(.login-button){padding:13px;border-radius:10px;color:var(--ink);font-weight:750;text-align:center;text-decoration:none}.mobile-menu .login-button{grid-column:1/-1}.hero-grid{grid-template-columns:1fr 1fr}.float-card{transform:scale(.88)}.heat-card{right:-3%}.traffic-card{right:-5%}.features-heading{grid-template-columns:1fr}.feature-card{grid-template-columns:1fr}.feature-mini{min-height:90px;margin:20px 0 0}.features-grid{grid-template-columns:repeat(3,1fr)}.ecosystem-node{width:156px;height:132px}.ecosystem-node-content{padding:16px}.seo-grid{gap:35px}.footer-grid{grid-template-columns:auto 1fr}.footer-grid > div{grid-column:1/-1;grid-row:2}.footer-grid > small{grid-row:3}
}

@media (max-width: 900px) {
  .section{padding:82px 0}.hero-section{min-height:0;padding-top:155px}.hero-grid{grid-template-columns:1fr}.hero-copy{text-align:center}.hero-copy .eyebrow{margin-inline:auto}.hero-lead{margin-inline:auto}.hero-actions,.hero-benefits{justify-content:center;margin-inline:auto}.hero-visual{min-height:570px}.metrics-strip{grid-template-columns:repeat(2,1fr)}.metrics-strip > div:nth-child(2){border-right:0}.features-grid{grid-template-columns:repeat(2,1fr)}.feature-promises{grid-template-columns:repeat(3,1fr)}.ecosystem-canvas{display:none}.ecosystem-section{min-height:0}.ecosystem-mobile-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.ecosystem-mobile-grid article{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--line);border-radius:15px;color:var(--purple);background:rgba(255,255,255,.8);box-shadow:0 10px 30px rgba(61,43,132,.07)}.ecosystem-mobile-grid strong,.ecosystem-mobile-grid small{display:block}.ecosystem-mobile-grid strong{color:var(--ink);font-size:.82rem}.ecosystem-mobile-grid small{margin-top:4px;color:var(--muted);font-size:.68rem}.seo-grid{grid-template-columns:1fr}.seo-copy{text-align:center}.seo-copy .eyebrow,.seo-copy > p:not(.eyebrow),.seo-summary{margin-inline:auto}.faq-layout{grid-template-columns:1fr;gap:35px}.final-cta-inner{display:grid;text-align:center;justify-items:center}.footer-grid{display:flex;flex-direction:column;align-items:flex-start}.footer-grid > small{width:100%}
}

@media (max-width: 640px) {
  :global(html){scroll-padding-top:96px}.landing-container{width:min(100% - 24px,1440px)}.section{padding:68px 0}.landing-header{top:max(8px,env(safe-area-inset-top));width:calc(100% - 16px)}.nav-shell{min-height:66px;padding:8px 10px 8px 14px;border-radius:19px}.brand-line{font-size:1.26rem}.brand-kicker{font-size:.57rem}.brand-cube{width:34px;height:34px;flex-basis:34px}.brand-cube img{width:50px;height:50px}.mobile-menu{grid-template-columns:1fr 1fr;padding:10px}.mobile-menu > a:not(.login-button){padding:11px 5px;font-size:.82rem}.hero-section{padding:125px 0 36px}.hero-copy{padding:0}.hero-copy h1{margin-top:23px;font-size:clamp(2.55rem,12vw,3.65rem)}.hero-lead{font-size:.94rem;line-height:1.7}.hero-actions{display:grid}.hero-actions > a{width:100%}.hero-benefits{grid-template-columns:1fr 1fr;gap:10px}.hero-benefit{align-items:flex-start;text-align:left;font-size:.7rem}.hero-visual{min-height:430px;margin-top:5px}.hero-cube{width:80%}.cube-stage{bottom:35px;width:250px;height:85px}.float-card{min-width:130px;padding:10px 11px;border-radius:13px;animation:none}.float-card small{margin-bottom:5px;font-size:.6rem}.float-card strong{font-size:.85rem}.visitors-card{top:23px;left:-7%;width:148px}.heat-card{top:50px;right:-9%;width:145px}.mini-heat{height:60px}.conversion-card{bottom:58px;left:-5%}.donut{width:38px;height:38px}.traffic-card{right:-6%;bottom:35px;width:143px}.metrics-strip{gap:0;padding-top:16px}.metrics-strip > div{padding:12px 8px;gap:8px}.metrics-strip strong{font-size:1.08rem}.metrics-strip small{font-size:.65rem}.features-heading{gap:28px}.section h2,.features-heading h2{font-size:2.35rem}.feature-promises{grid-template-columns:1fr}.feature-promises > div{min-height:0}.features-grid{grid-template-columns:1fr}.feature-card{grid-template-columns:minmax(0,1fr) minmax(115px,.72fr);min-height:210px;padding:20px}.feature-mini{min-height:0;margin:0 0 0 10px}.feature-card h3{margin-top:22px}.ecosystem-mobile-grid{grid-template-columns:1fr}.seo-summary{grid-template-columns:repeat(3,1fr)}.seo-summary > div{padding:13px 8px}.seo-summary strong{font-size:1.15rem}.seo-dashboard-body{padding:12px}.health-card{grid-template-columns:95px 1fr;padding:12px}.health-ring{width:84px;height:84px}.health-ring::after{inset:9px}.health-ring strong{font-size:1.4rem}.seo-checks{grid-template-columns:1fr}.ai-recommendation{grid-template-columns:auto 1fr}.ai-recommendation > svg{display:none}.pricing-tabs{width:100%}.pricing-tabs button{flex:1;padding:0 7px;font-size:.72rem}.pricing-grid{grid-template-columns:1fr}.pricing-card{padding:25px 20px}.faq-list button{padding:17px}.faq-list article > div p{padding:0 17px 17px}.final-cta{padding-bottom:45px}.final-cta-inner{padding:32px 20px}.cta-white{width:100%}.footer-grid > div{flex-wrap:wrap}
}

@media (max-width: 390px) {
  .hero-benefits{grid-template-columns:1fr}.feature-card{grid-template-columns:1fr}.feature-mini{margin:18px 0 0}.metrics-strip{grid-template-columns:1fr}.metrics-strip > div{border-right:0;border-bottom:1px solid var(--line)}.metrics-strip > div:last-child{border-bottom:0}.seo-summary small{font-size:.58rem}.health-card{grid-template-columns:1fr;text-align:center}.health-ring{margin:auto}.brand-cube{width:31px;height:31px;flex-basis:31px}.brand-cube img{width:46px;height:46px}
}

@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}
</style>
