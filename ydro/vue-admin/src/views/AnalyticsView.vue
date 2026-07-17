<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Activity,
  ArrowRight,
  BarChart3,
  Clock3,
  FileText,
  Flame,
  MousePointerClick,
  RefreshCw,
  Send,
  Users,
} from '@lucide/vue'

import {
  getSiteAnalyticsSectionRequest,
  getSiteAnalyticsSummaryRequest,
} from '../api/analytics'
import EmptyAnalyticsState from '../components/EmptyAnalyticsState.vue'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const loading = ref(false)
const error = ref('')
const summary = ref(null)
const days = ref(7)
const customFrom = ref('')
const customTo = ref('')
const periodMode = ref('7')
const advancedOpen = ref(false)
const heatmapOpen = ref(false)
const advancedLoading = ref(false)
const advancedError = ref('')
const advancedData = ref({})

const siteId = computed(() => Number(route.params.siteId))

const periodLabel = computed(() => {
  if (periodMode.value === 'today') return 'сегодня'
  if (periodMode.value === 'custom' && customFrom.value && customTo.value) return `${customFrom.value} - ${customTo.value}`
  return `последние ${days.value} дней`
})

const visitors = computed(() => numberValue(summary.value?.unique_real_visitors ?? summary.value?.visitors_unique))
const visits = computed(() => numberValue(summary.value?.real_visitors ?? summary.value?.visit_count))
const pageviews = computed(() => numberValue(summary.value?.pageviews_count))
const leads = computed(() => numberValue(summary.value?.leads_count))
const conversion = computed(() => Number(summary.value?.conversion || 0))
const avgDuration = computed(() => numberValue(summary.value?.avg_duration))
const hasData = computed(() => visitors.value > 0 || pageviews.value > 0 || leads.value > 0)

const sources = computed(() => {
  const rows = Array.isArray(summary.value?.sources) ? summary.value.sources : []
  const normalized = rows.map((item) => ({
    name: sourceLabel(item.source || item.medium || item.referrer),
    count: numberValue(item.count),
  }))
  return groupRows(normalized).slice(0, 5)
})

const topPages = computed(() => {
  const rows = Array.isArray(summary.value?.top_pages) ? summary.value.top_pages : []
  return rows.slice(0, 5).map((page) => ({
    title: pageTitle(page.title || page.name || page.pathname || page.path),
    views: numberValue(page.views ?? page.count),
    avgTime: numberValue(page.avg_time || page.avg_duration),
  }))
})

const actionRows = computed(() => {
  const events = advancedData.value.events?.events || []
  const mapped = groupRows(events.map((item) => ({
    name: eventLabel(item.event_type || item.type || item.element),
    count: numberValue(item.count),
  })))
  const leadRow = leads.value ? [{ name: 'Заявки', count: leads.value }] : []
  return [...leadRow, ...mapped].filter((item) => item.count > 0).slice(0, 5)
})

const pathRows = computed(() => {
  const paths = advancedData.value.paths?.paths || []
  return paths.slice(0, 5).map((item) => ({
    path: humanPath(item.path),
    sessions: numberValue(item.sessions),
  }))
})

const chartRows = computed(() => {
  const daily = Array.isArray(summary.value?.daily) ? summary.value.daily : []
  if (!daily.length) {
    return [{ label: 'Период', visitors: visitors.value, leads: leads.value }]
  }
  return daily.slice(-14).map((item) => ({
    label: shortDate(item.date || item.day),
    visitors: numberValue(item.visitors || item.unique_visitors || item.visits),
    leads: numberValue(item.leads),
  }))
})

const maxChartValue = computed(() => Math.max(1, ...chartRows.value.flatMap((row) => [row.visitors, row.leads])))

const metricCards = computed(() => [
  {
    label: 'Посетители',
    value: formatNumber(visitors.value),
    hint: 'Количество людей, которые заходили на сайт.',
    icon: Users,
    delta: activityText(visitors.value),
  },
  {
    label: 'Просмотры страниц',
    value: formatNumber(pageviews.value),
    hint: 'Сколько страниц открыли посетители.',
    icon: FileText,
    delta: pageviews.value > visitors.value ? 'Люди смотрят больше одной страницы.' : 'Переходов между страницами пока мало.',
  },
  {
    label: 'Заявки',
    value: formatNumber(leads.value),
    hint: 'Отправленные формы и обращения.',
    icon: Send,
    delta: leads.value ? 'Есть обращения за выбранный период.' : 'Заявок за период пока нет.',
  },
  {
    label: 'Конверсия',
    value: `${conversion.value.toLocaleString('ru-RU')}%`,
    hint: 'Доля посетителей, которые оставили заявку.',
    icon: Activity,
    delta: `${conversion.value.toLocaleString('ru-RU')}% посетителей оставили заявку.`,
  },
  {
    label: 'Среднее время',
    value: formatSeconds(avgDuration.value),
    hint: 'Сколько в среднем посетитель находится на сайте.',
    icon: Clock3,
    delta: avgDuration.value > 60 ? 'Посетители задерживаются на сайте.' : 'Проверьте понятность первого экрана.',
  },
])

const overviewText = computed(() => {
  if (!hasData.value) {
    return [
      'Пока недостаточно данных для подробной сводки.',
      'Аналитика появится после первых посещений сайта.',
    ]
  }
  const topSource = sources.value[0]?.name || 'не определенного источника'
  const topPage = topPages.value[0]?.title || 'Главная'
  const trend = visitors.value > 0 ? 'Активность можно оценивать по графику посещаемости ниже.' : 'Посещений пока мало.'
  return [
    `За ${periodLabel.value} сайт посетили ${formatNumber(visitors.value)} человек.`,
    `Больше всего посетителей пришло из канала «${topSource}».`,
    `Самая популярная страница - «${topPage}».`,
    `Получено ${formatNumber(leads.value)} заявок.`,
    trend,
  ]
})

const insightItems = computed(() => {
  const items = []
  if (!hasData.value) items.push('Проверьте, установлен ли код аналитики на публичном сайте.')
  if (visitors.value > 0 && leads.value === 0) items.push('За выбранный период заявок не было. Проверьте форму и контактные данные.')
  if (conversion.value > 0 && conversion.value < 2) items.push('Конверсия ниже 2%. Сделайте кнопку связи заметнее.')
  if (topPages.value[0]?.title && leads.value === 0) items.push(`Посетители открывают страницу «${topPages.value[0].title}», но пока не оставляют заявку.`)
  if (avgDuration.value < 30 && visitors.value > 3) items.push('Среднее время на сайте низкое. Проверьте скорость загрузки и первый экран.')
  const mobile = numberValue(summary.value?.devices?.mobile)
  const deviceTotal = Object.values(summary.value?.devices || {}).reduce((sum, value) => sum + numberValue(value), 0)
  if (deviceTotal && mobile / deviceTotal >= 0.6) items.push('Большинство посетителей заходит с телефона. Проверьте мобильную форму заявки.')
  if (!items.length) items.push('Критичных проблем за выбранный период не видно.')
  return items.slice(0, 3)
})

function numberValue(value) {
  const number = Number(value || 0)
  return Number.isFinite(number) ? number : 0
}

function formatNumber(value) {
  return numberValue(value).toLocaleString('ru-RU')
}

function formatSeconds(value) {
  const total = Math.max(0, Math.round(numberValue(value)))
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  if (minutes <= 0) return `${seconds} сек`
  return `${minutes} мин ${seconds} сек`
}

function percent(value) {
  return `${Math.round((numberValue(value) / maxChartValue.value) * 100)}%`
}

function sourceLabel(value) {
  const text = String(value || '').toLowerCase()
  if (!text || text === 'direct' || text === '(none)' || text === 'none') return 'Прямые заходы'
  if (text.includes('google') || text.includes('yandex') || text.includes('bing') || text.includes('search') || text.includes('organic')) return 'Поиск'
  if (text.includes('vk') || text.includes('telegram') || text.includes('instagram') || text.includes('facebook') || text.includes('social')) return 'Социальные сети'
  if (text.includes('cpc') || text.includes('ads') || text.includes('ad') || text.includes('utm')) return 'Реклама'
  return 'Другие сайты'
}

function eventLabel(value) {
  const text = String(value || '').toLowerCase()
  if (text.includes('form') || text.includes('lead')) return 'Заявки'
  if (text.includes('phone') || text.includes('tel')) return 'Клики по телефону'
  if (text.includes('email') || text.includes('mail')) return 'Клики по email'
  if (text.includes('telegram')) return 'Переходы в Telegram'
  if (text.includes('whatsapp') || text.includes('messenger')) return 'Переходы в мессенджеры'
  if (text.includes('click')) return 'Клики по кнопкам'
  return 'Действия на сайте'
}

function pageTitle(value) {
  const raw = String(value || '/').split('?')[0].replace(/\/+/g, '/')
  if (raw === '/' || raw === '') return 'Главная'
  const last = raw.split('/').filter(Boolean).pop() || raw
  const labels = { services: 'Услуги', contacts: 'Контакты', contact: 'Контакты', about: 'О компании', portfolio: 'Портфолио', projects: 'Проекты' }
  return labels[last] || decodeURIComponent(last).replace(/[-_]/g, ' ')
}

function humanPath(value) {
  return String(value || '')
    .split('->')
    .map((item) => pageTitle(item.trim()))
    .filter(Boolean)
    .slice(0, 4)
    .join(' -> ')
}

function groupRows(rows) {
  const map = new Map()
  for (const row of rows) {
    if (!row.name) continue
    map.set(row.name, (map.get(row.name) || 0) + numberValue(row.count))
  }
  const total = Array.from(map.values()).reduce((sum, value) => sum + value, 0)
  return Array.from(map.entries())
    .map(([name, count]) => ({ name, count, percent: total ? Math.round((count / total) * 100) : 0 }))
    .filter((item) => item.count > 0)
    .sort((left, right) => right.count - left.count)
}

function shortDate(value) {
  if (!value) return 'Период'
  return new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

function activityText(value) {
  if (numberValue(value) <= 0) return 'Данных за период пока нет.'
  return 'Сравните с предыдущим периодом по графику.'
}

function setPeriod(mode) {
  periodMode.value = mode
  if (mode === 'today') days.value = 1
  if (mode === '7') days.value = 7
  if (mode === '30') days.value = 30
  loadSummary()
}

async function loadSummary() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, { days: days.value })
    summary.value = data
    loadSupportingSections()
  } catch (requestError) {
    error.value = requestError?.response?.data?.detail || 'Не удалось загрузить аналитику. Попробуйте обновить страницу.'
  } finally {
    loading.value = false
  }
}

async function loadSupportingSections() {
  const sections = ['events', 'paths']
  const results = await Promise.allSettled(
    sections.map((section) => getSiteAnalyticsSectionRequest(siteId.value, section, { days: days.value, limit: 50 })),
  )
  const nextData = { ...advancedData.value }
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') nextData[sections[index]] = result.value.data
  })
  advancedData.value = nextData
}

async function loadAdvanced() {
  advancedOpen.value = !advancedOpen.value
  if (!advancedOpen.value || Object.keys(advancedData.value).length) return
  advancedLoading.value = true
  advancedError.value = ''
  const sections = ['events', 'pages', 'paths', 'heatmap', 'sessions'].filter((section) => !advancedData.value[section])
  if (!sections.length) {
    advancedLoading.value = false
    return
  }
  const results = await Promise.allSettled(
    sections.map((section) => getSiteAnalyticsSectionRequest(siteId.value, section, { days: days.value, limit: 50 })),
  )
  const nextData = {}
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') nextData[sections[index]] = result.value.data
  })
  advancedData.value = nextData
  if (results.some((result) => result.status === 'rejected')) {
    advancedError.value = 'Часть подробных данных не загрузилась. Основная сводка продолжает работать.'
  }
  advancedLoading.value = false
}

watch(siteId, () => {
  summary.value = null
  advancedData.value = {}
  advancedOpen.value = false
  loadSummary()
})

onMounted(loadSummary)
</script>

<template>
  <div class="page-stack analytics-simple">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Аналитика сайта</p>
        <h1>Краткая сводка за выбранный период</h1>
        <p>Главные показатели без технических терминов и лишних графиков.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="period-button" :class="{ active: periodMode === 'today' }" @click="setPeriod('today')">Сегодня</button>
        <button type="button" class="period-button" :class="{ active: periodMode === '7' }" @click="setPeriod('7')">7 дней</button>
        <button type="button" class="period-button" :class="{ active: periodMode === '30' }" @click="setPeriod('30')">30 дней</button>
        <button type="button" class="period-button" :class="{ active: periodMode === 'custom' }" @click="periodMode = 'custom'">Свой период</button>
        <button type="button" class="icon-button" title="Обновить" aria-label="Обновить" @click="loadSummary">
          <RefreshCw :size="18" />
        </button>
      </div>
    </header>

    <section v-if="periodMode === 'custom'" class="surface compact-controls">
      <input v-model="customFrom" type="date" class="form-control">
      <input v-model="customTo" type="date" class="form-control">
      <button type="button" class="action-button-primary" @click="loadSummary">Показать</button>
    </section>

    <p v-if="error" class="notice-error">
      {{ error }}
      <button type="button" class="ml-2 font-semibold underline" @click="loadSummary">Повторить</button>
    </p>

    <section v-if="loading" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <div v-for="index in 5" :key="index" class="skeleton-card" />
    </section>

    <template v-else>
      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-card">
          <div class="flex items-center justify-between gap-3">
            <p>{{ metric.label }}</p>
            <component :is="metric.icon" :size="19" />
          </div>
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.hint }}</span>
          <small>{{ metric.delta }}</small>
        </article>
      </section>

      <section v-if="!hasData" class="empty-state">
        <h2>За выбранный период данных пока нет.</h2>
        <p>Аналитика появится после первых посещений сайта.</p>
      </section>

      <section class="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <article class="surface">
          <div class="section-heading">
            <div>
              <h2>Посещаемость</h2>
              <p>Посетители и заявки за период.</p>
            </div>
            <BarChart3 :size="21" class="text-brand-700" />
          </div>
          <div class="simple-chart" :style="{ '--rows': chartRows.length }">
            <div v-for="row in chartRows" :key="row.label" class="chart-row">
              <span>{{ row.label }}</span>
              <div>
                <i class="visitors" :style="{ width: percent(row.visitors) }" />
                <i class="leads" :style="{ width: percent(row.leads) }" />
              </div>
            </div>
          </div>
          <div class="chart-legend">
            <span><i class="visitors" /> Посетители</span>
            <span><i class="leads" /> Заявки</span>
          </div>
        </article>

        <article class="surface">
          <div class="section-heading">
            <div>
              <h2>Краткий итог</h2>
              <p>Что произошло на сайте простыми словами.</p>
            </div>
          </div>
          <ul class="summary-list">
            <li v-for="line in overviewText" :key="line">{{ line }}</li>
          </ul>
        </article>
      </section>

      <section class="grid gap-4 xl:grid-cols-2">
        <article class="surface">
          <div class="section-heading"><div><h2>Откуда пришли посетители</h2><p>Каналы без технических меток.</p></div></div>
          <div v-if="sources.length" class="bar-list">
            <div v-for="item in sources" :key="item.name">
              <div><span>{{ item.name }}</span><b>{{ item.percent }}%</b></div>
              <i :style="{ width: `${item.percent}%` }" />
            </div>
          </div>
          <EmptyAnalyticsState v-else />
        </article>

        <article class="surface">
          <div class="section-heading"><div><h2>Популярные страницы</h2><p>Максимум 5 страниц, которые смотрели чаще всего.</p></div></div>
          <div v-if="topPages.length" class="plain-list">
            <div v-for="page in topPages" :key="page.title">
              <span>{{ page.title }}</span>
              <b>{{ formatNumber(page.views) }} просмотров</b>
              <small v-if="page.avgTime">Среднее время: {{ formatSeconds(page.avgTime) }}</small>
            </div>
          </div>
          <EmptyAnalyticsState v-else />
        </article>

        <article class="surface">
          <div class="section-heading"><div><h2>Действия посетителей</h2><p>Заявки, клики и переходы к контактам.</p></div></div>
          <div v-if="actionRows.length" class="plain-list">
            <div v-for="item in actionRows" :key="item.name">
              <span>{{ item.name }}</span>
              <b>{{ formatNumber(item.count) }}</b>
            </div>
          </div>
          <p v-else class="text-sm leading-6 text-slate-500">Действий за период пока нет.</p>
        </article>

        <article class="surface">
          <div class="section-heading"><div><h2>Частые переходы</h2><p>Популярные маршруты по сайту.</p></div></div>
          <div v-if="pathRows.length" class="plain-list">
            <div v-for="item in pathRows" :key="item.path">
              <span>{{ item.path }}</span>
              <b>{{ formatNumber(item.sessions) }} сессий</b>
            </div>
          </div>
          <p v-else class="text-sm leading-6 text-slate-500">Маршруты появятся после нескольких переходов между страницами.</p>
        </article>
      </section>

      <section class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <article class="surface heatmap-card">
          <Flame :size="24" />
          <div>
            <h2>Тепловая карта</h2>
            <p>Посмотрите, на какие элементы сайта посетители нажимают чаще всего.</p>
          </div>
          <button type="button" class="action-button-primary" @click="heatmapOpen = !heatmapOpen; if (!advancedOpen) loadAdvanced()">
            Открыть тепловую карту
          </button>
        </article>

        <article class="surface">
          <div class="section-heading"><div><h2>На что обратить внимание</h2><p>Короткие автоматические подсказки.</p></div></div>
          <ul class="summary-list">
            <li v-for="item in insightItems" :key="item">{{ item }}</li>
          </ul>
        </article>
      </section>

      <section v-if="heatmapOpen" class="surface">
        <div class="section-heading"><div><h2>Тепловая карта</h2><p>Подробные клики открыты вручную.</p></div></div>
        <div v-if="advancedData.heatmap?.points?.length" class="heatmap-preview">
          <span
            v-for="point in advancedData.heatmap.points.slice(0, 120)"
            :key="`${point.x}-${point.y}-${point.count}`"
            :style="{ left: `${Math.min(100, Math.max(0, point.x_percent || point.x / 14.4))}%`, top: `${Math.min(100, Math.max(0, point.y_percent || point.y / 18))}%`, opacity: Math.min(0.9, 0.25 + numberValue(point.count) / 10) }"
          />
        </div>
        <p v-else class="text-sm leading-6 text-slate-500">Для построения тепловой карты пока недостаточно действий посетителей.</p>
      </section>

      <section class="surface">
        <button type="button" class="advanced-toggle" :aria-expanded="advancedOpen" @click="loadAdvanced">
          <span>Расширенная аналитика</span>
          <ArrowRight :size="18" :class="{ 'rotate-90': advancedOpen }" />
        </button>
        <p class="mt-2 text-sm text-slate-500">Технические таблицы, события, пути, сессии и подробные данные скрыты по умолчанию.</p>
        <p v-if="advancedError" class="notice-error mt-3">{{ advancedError }}</p>
        <div v-if="advancedOpen" class="mt-5">
          <div v-if="advancedLoading" class="empty-state"><span class="loading-dot" /><p>Загружаем подробные данные...</p></div>
          <div v-else class="grid gap-4 lg:grid-cols-2">
            <article class="advanced-panel">
              <h3>События</h3>
              <div v-if="(advancedData.events?.events || []).length" class="plain-list dense">
                <div v-for="item in advancedData.events.events.slice(0, 10)" :key="`${item.event_type}-${item.page}-${item.element}`">
                  <span>{{ eventLabel(item.event_type || item.type) }}</span>
                  <b>{{ item.count }}</b>
                </div>
              </div>
              <EmptyAnalyticsState v-else />
            </article>
            <article class="advanced-panel">
              <h3>Страницы</h3>
              <div v-if="(advancedData.pages?.pages || []).length" class="plain-list dense">
                <div v-for="page in advancedData.pages.pages.slice(0, 10)" :key="page.path">
                  <span>{{ pageTitle(page.path) }}</span>
                  <b>{{ page.views }}</b>
                </div>
              </div>
              <EmptyAnalyticsState v-else />
            </article>
            <article class="advanced-panel">
              <h3>Сессии</h3>
              <p class="text-sm text-slate-500">{{ advancedData.sessions?.count || 0 }} сессий за период.</p>
            </article>
            <article class="advanced-panel">
              <h3>Пути пользователей</h3>
              <div v-if="pathRows.length" class="plain-list dense">
                <div v-for="item in pathRows" :key="item.path">
                  <span>{{ item.path }}</span>
                  <b>{{ item.sessions }}</b>
                </div>
              </div>
              <EmptyAnalyticsState v-else />
            </article>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.analytics-simple {
  --simple-ink: #17223b;
  --simple-muted: #64748b;
}

.period-button {
  min-height: 2.5rem;
  border: 1px solid rgba(109, 93, 246, 0.16);
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
  padding: 0 0.9rem;
  font-size: 0.875rem;
  font-weight: 700;
}

.period-button.active {
  border-color: transparent;
  background: #6d5df6;
  color: #fff;
}

.compact-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.metric-card,
.skeleton-card {
  min-height: 11rem;
  border: 1px solid rgba(109, 93, 246, 0.12);
  border-radius: 1.2rem;
  background: rgba(255, 255, 255, 0.92);
  padding: 1rem;
  box-shadow: 0 18px 42px rgba(32, 40, 70, 0.08);
}

.metric-card p {
  margin: 0;
  color: #475569;
  font-size: 0.86rem;
  font-weight: 750;
}

.metric-card svg {
  color: #6d5df6;
}

.metric-card strong {
  display: block;
  margin-top: 1rem;
  color: var(--simple-ink);
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  line-height: 1;
}

.metric-card span,
.metric-card small {
  display: block;
  margin-top: 0.7rem;
  color: var(--simple-muted);
  font-size: 0.82rem;
  line-height: 1.45;
}

.metric-card small {
  color: #334155;
}

.skeleton-card {
  animation: pulse 1.2s ease-in-out infinite;
  background: linear-gradient(90deg, #f1f5f9, #fff, #f1f5f9);
}

.simple-chart {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.chart-row {
  display: grid;
  grid-template-columns: 4.5rem minmax(0, 1fr);
  gap: 0.75rem;
  align-items: center;
}

.chart-row > span {
  color: #64748b;
  font-size: 0.78rem;
}

.chart-row > div {
  display: grid;
  gap: 0.22rem;
}

.chart-row i,
.chart-legend i {
  display: block;
  height: 0.55rem;
  border-radius: 999px;
}

.chart-row i.visitors,
.chart-legend i.visitors {
  background: #6d5df6;
}

.chart-row i.leads,
.chart-legend i.leads {
  background: #22c55e;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
  color: #64748b;
  font-size: 0.8rem;
}

.chart-legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.chart-legend i {
  width: 1.2rem;
}

.summary-list {
  display: grid;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.summary-list li {
  border-bottom: 1px solid #eef2f7;
  padding-bottom: 0.75rem;
  color: #334155;
  font-size: 0.95rem;
  line-height: 1.6;
}

.summary-list li:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.bar-list {
  display: grid;
  gap: 1rem;
}

.bar-list div div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 700;
}

.bar-list i {
  display: block;
  height: 0.55rem;
  margin-top: 0.45rem;
  border-radius: 999px;
  background: #6d5df6;
}

.plain-list {
  display: grid;
  gap: 0.65rem;
}

.plain-list > div {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.35rem 1rem;
  align-items: center;
  border-bottom: 1px solid #eef2f7;
  padding: 0.65rem 0;
}

.plain-list.dense > div {
  padding: 0.45rem 0;
}

.plain-list span {
  min-width: 0;
  overflow: hidden;
  color: #334155;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plain-list b {
  color: #17223b;
  font-size: 0.9rem;
}

.plain-list small {
  grid-column: 1 / -1;
  color: #64748b;
}

.heatmap-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
}

.heatmap-card svg {
  color: #f97316;
}

.heatmap-card h2 {
  margin: 0;
  color: #17223b;
  font-size: 1rem;
  font-weight: 800;
}

.heatmap-card p {
  margin: 0.35rem 0 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
}

.heatmap-preview {
  position: relative;
  min-height: 28rem;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 1.25rem;
  background: linear-gradient(180deg, #f8fafc, #eef2ff);
}

.heatmap-preview span {
  position: absolute;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(239, 68, 68, 0.72), rgba(249, 115, 22, 0.28), transparent 68%);
  transform: translate(-50%, -50%);
}

.advanced-toggle {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  border: 0;
  background: transparent;
  color: #17223b;
  padding: 0;
  text-align: left;
  font: inherit;
  font-weight: 800;
}

.advanced-toggle svg {
  transition: transform 0.2s ease;
}

.advanced-panel {
  border: 1px solid #eef2f7;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem;
}

.advanced-panel h3 {
  margin: 0 0 0.75rem;
  color: #17223b;
  font-size: 0.95rem;
  font-weight: 800;
}

.rotate-90 {
  transform: rotate(90deg);
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@media (max-width: 760px) {
  .heatmap-card {
    grid-template-columns: 1fr;
  }

  .chart-row {
    grid-template-columns: 3.8rem minmax(0, 1fr);
  }
}
</style>
