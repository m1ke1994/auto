<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  BarChart3,
  CircleAlert,
  Copy,
  FileText,
  Filter,
  Flame,
  Funnel,
  Gauge,
  KeyRound,
  ListVideo,
  MonitorSmartphone,
  MousePointerClick,
  Play,
  RefreshCw,
  Route,
  ScrollText,
  Sparkles,
} from '@lucide/vue'

import {
  getSiteAnalyticsSectionRequest,
  getSiteAnalyticsSessionRequest,
  getSiteAnalyticsSummaryRequest,
} from '../api/analytics'
import DashboardStats from '../components/DashboardStats.vue'
import { refreshSiteTrackingKeyRequest } from '../api/site'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const loading = ref(false)
const sectionLoading = ref(false)
const sessionLoading = ref(false)
const error = ref('')
const success = ref('')
const summary = ref(null)
const sectionData = ref({})
const sessionDetail = ref(null)
const activeTab = ref('overview')
const days = ref(14)
const includeBots = ref(false)
const action = ref('')
const pageFilter = ref('')
const deviceFilter = ref('all')
const eventTypeFilter = ref('')

const emptyText = 'Данных пока нет. Они появятся после новых посещений сайта.'
const siteId = computed(() => Number(route.params.siteId))
const trackerScript = computed(() => summary.value?.tracker?.script_tag || siteStore.currentSite?.tracker_script_tag || '')
const activePayload = computed(() => sectionData.value[activeTab.value] || {})

const tabs = [
  { key: 'overview', label: 'Обзор', icon: BarChart3 },
  { key: 'heatmap', label: 'Тепловая карта', icon: Flame },
  { key: 'scrollmap', label: 'Карта скроллинга', icon: ScrollText },
  { key: 'sessions', label: 'Записи сессий', icon: ListVideo },
  { key: 'paths', label: 'Пути пользователей', icon: Route },
  { key: 'funnels', label: 'Воронки', icon: Funnel },
  { key: 'events', label: 'События', icon: MousePointerClick },
  { key: 'pages', label: 'Страницы', icon: FileText },
  { key: 'errors', label: 'Ошибки', icon: CircleAlert },
  { key: 'performance', label: 'Производительность', icon: Gauge },
  { key: 'recommendations', label: 'AI-рекомендации', icon: Sparkles },
]

const endpointByTab = {
  heatmap: 'heatmap',
  scrollmap: 'scrollmap',
  sessions: 'sessions',
  paths: 'paths',
  funnels: 'funnels',
  events: 'events',
  pages: 'pages',
  errors: 'errors',
  performance: 'performance',
  recommendations: 'recommendations',
}

const stats = computed(() => [
  { label: 'Реальные', value: summary.value?.real_visitors ?? summary.value?.visit_count ?? 0, sub: 'посещения без ботов' },
  { label: 'Боты', value: summary.value?.bot_visitors ?? 0, sub: 'не входят в конверсию' },
  { label: 'Всего', value: summary.value?.total_visitors ?? summary.value?.visit_count ?? 0, sub: 'включая ботов' },
  { label: 'Уникальные', value: summary.value?.unique_real_visitors ?? summary.value?.visitors_unique ?? 0, sub: 'реальные посетители' },
  { label: 'Просмотры', value: summary.value?.pageviews_count ?? 0, sub: includeBots.value ? 'с ботами' : 'только реальные' },
  { label: 'Заявки', value: summary.value?.leads_count ?? 0, sub: `конверсия ${summary.value?.conversion ?? 0}%` },
])

const deviceRows = computed(() => distributionRows(summary.value?.devices))
const browserRows = computed(() => distributionRows(summary.value?.browsers))
const osRows = computed(() => distributionRows(summary.value?.os))
const heatmapCanvas = computed(() => activePayload.value?.canvas || { width: 1440, height: 1800 })
const heatmapPoints = computed(() => activePayload.value?.points || [])
const pageOptions = computed(() => {
  const rawPages = activePayload.value?.pages?.length ? activePayload.value.pages : (summary.value?.top_pages || [])
  const seen = new Set()
  return rawPages
    .map((page) => page.path || page.pathname || '/')
    .filter((path) => {
      if (seen.has(path)) return false
      seen.add(path)
      return true
    })
})

function distributionRows(distribution) {
  const entries = Object.entries(distribution || {})
  const total = entries.reduce((sum, [, count]) => sum + Number(count || 0), 0)
  return entries
    .map(([name, count]) => ({
      name,
      count: Number(count || 0),
      percent: total ? Math.round((Number(count || 0) / total) * 100) : 0,
    }))
    .filter((item) => item.count > 0)
    .sort((left, right) => right.count - left.count)
}

function deviceLabel(value) {
  return { desktop: 'Компьютер', mobile: 'Телефон', tablet: 'Планшет', unknown: 'Не определено' }[value] || value || 'Не определено'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatSeconds(value) {
  const seconds = Number(value || 0)
  if (seconds < 60) return `${seconds} сек.`
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return rest ? `${minutes} мин. ${rest} сек.` : `${minutes} мин.`
}

function importanceLabel(value) {
  return { high: 'Высокая', medium: 'Средняя', low: 'Низкая' }[value] || 'Низкая'
}

function importanceClass(value) {
  if (value === 'high') return 'status-danger'
  if (value === 'medium') return 'status-warning'
  return 'status-neutral'
}

function heatPointStyle(point) {
  const width = Number(heatmapCanvas.value.width || 1440)
  const height = Number(heatmapCanvas.value.height || 1800)
  const size = Math.min(42, 14 + Number(point.count || 0) * 3)
  const alpha = Math.max(0.22, Math.min(0.84, Number(point.intensity || 0.25)))
  return {
    left: `${Math.min(100, Math.max(0, (Number(point.x || 0) / width) * 100))}%`,
    top: `${Math.min(100, Math.max(0, (Number(point.y || 0) / height) * 100))}%`,
    width: `${size}px`,
    height: `${size}px`,
    backgroundColor: `rgba(220, 38, 38, ${alpha})`,
    boxShadow: `0 0 ${size}px rgba(245, 158, 11, ${alpha})`,
  }
}

function sectionParams() {
  const params = {
    days: days.value,
    include_bots: includeBots.value ? 'true' : undefined,
  }
  if (['heatmap', 'scrollmap', 'events'].includes(activeTab.value) && pageFilter.value) {
    params.page = pageFilter.value
  }
  if (['heatmap', 'events'].includes(activeTab.value) && deviceFilter.value !== 'all') {
    params.device = deviceFilter.value
  }
  if (activeTab.value === 'events' && eventTypeFilter.value) {
    params.event_type = eventTypeFilter.value
  }
  if (activeTab.value === 'sessions') {
    params.limit = 50
  }
  return params
}

async function loadSummary() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, {
      days: days.value,
      include_bots: includeBots.value ? 'true' : undefined,
    })
    summary.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить аналитику.'
  } finally {
    loading.value = false
  }
}

async function loadActiveTab() {
  if (activeTab.value === 'overview') {
    await loadSummary()
    return
  }
  const endpoint = endpointByTab[activeTab.value]
  if (!endpoint) return
  sectionLoading.value = true
  error.value = ''
  try {
    const { data } = await getSiteAnalyticsSectionRequest(siteId.value, endpoint, sectionParams())
    sectionData.value = { ...sectionData.value, [activeTab.value]: data }
    if (activeTab.value !== 'sessions') sessionDetail.value = null
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить раздел аналитики.'
  } finally {
    sectionLoading.value = false
  }
}

async function refreshAll() {
  if (activeTab.value === 'overview') {
    await loadSummary()
    return
  }
  await Promise.all([loadSummary(), loadActiveTab()])
}

async function copyScript() {
  if (!trackerScript.value) return
  action.value = 'copy'
  error.value = ''
  success.value = ''
  try {
    await navigator.clipboard.writeText(trackerScript.value)
    success.value = 'Скрипт аналитики скопирован.'
  } catch {
    error.value = 'Не удалось скопировать скрипт. Выделите код вручную.'
  } finally {
    action.value = ''
  }
}

async function refreshKey() {
  action.value = 'key'
  error.value = ''
  success.value = ''
  try {
    const { data } = await refreshSiteTrackingKeyRequest(siteId.value)
    summary.value = {
      ...(summary.value || {}),
      tracker: {
        api_key: data.api_key,
        script_tag: data.tracker_script_tag,
      },
    }
    await siteStore.fetchSite(siteId.value)
    success.value = data?.detail || 'Ключ аналитики обновлён.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось обновить ключ аналитики.'
  } finally {
    action.value = ''
  }
}

async function openSession(sessionId) {
  if (!sessionId) return
  sessionLoading.value = true
  sessionDetail.value = null
  try {
    const { data } = await getSiteAnalyticsSessionRequest(siteId.value, sessionId, {
      days: days.value,
      include_bots: includeBots.value ? 'true' : undefined,
    })
    sessionDetail.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить сессию.'
  } finally {
    sessionLoading.value = false
  }
}

function setTab(tabKey) {
  activeTab.value = tabKey
}

watch(activeTab, () => {
  pageFilter.value = ''
  eventTypeFilter.value = ''
  sessionDetail.value = null
  loadActiveTab()
})

watch(siteId, () => {
  sectionData.value = {}
  sessionDetail.value = null
  loadSummary()
  if (activeTab.value !== 'overview') loadActiveTab()
})

onMounted(async () => {
  await loadSummary()
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Посетители сайта</p>
        <h1>Аналитика</h1>
        <p>Обзор, поведенческие события, страницы, пути и технические сигналы.</p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <div class="inline-flex rounded-lg border border-slate-300 bg-white p-1">
          <button
            type="button"
            class="rounded-md px-3 py-2 text-sm font-semibold transition"
            :class="!includeBots ? 'bg-cyan-600 text-white' : 'text-slate-600 hover:text-cyan-800'"
            @click="includeBots = false; refreshAll()"
          >
            Только реальные
          </button>
          <button
            type="button"
            class="rounded-md px-3 py-2 text-sm font-semibold transition"
            :class="includeBots ? 'bg-cyan-600 text-white' : 'text-slate-600 hover:text-cyan-800'"
            @click="includeBots = true; refreshAll()"
          >
            С ботами
          </button>
        </div>
        <select v-model.number="days" class="form-control w-36" @change="refreshAll">
          <option :value="7">7 дней</option>
          <option :value="14">14 дней</option>
          <option :value="30">30 дней</option>
          <option :value="90">90 дней</option>
        </select>
        <button type="button" class="icon-button" title="Обновить" aria-label="Обновить" @click="refreshAll">
          <RefreshCw :size="18" />
        </button>
      </div>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>

    <nav class="overflow-x-auto rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
      <div class="flex min-w-max gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="inline-flex min-h-10 items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold transition"
          :class="activeTab === tab.key ? 'bg-cyan-600 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'"
          @click="setTab(tab.key)"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.label }}
        </button>
      </div>
    </nav>

    <section v-if="(activeTab === 'overview' && loading) || (activeTab !== 'overview' && sectionLoading)" class="empty-state">
      <span class="loading-dot" />
      <p>Собираем статистику...</p>
    </section>

    <template v-else>
      <template v-if="activeTab === 'overview'">
        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Скрипт аналитики</h2>
              <p>Код трекера для публичного сайта.</p>
            </div>
            <KeyRound :size="21" class="text-cyan-700" />
          </div>
          <code class="block overflow-x-auto rounded-lg bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-50">{{ trackerScript || 'Ключ аналитики пока не создан.' }}</code>
          <div class="mt-3 flex flex-col gap-2 sm:flex-row">
            <button type="button" class="action-button-primary" :disabled="!trackerScript || Boolean(action)" @click="copyScript">
              <Copy :size="17" />
              Скопировать скрипт
            </button>
            <button type="button" class="action-button-secondary" :disabled="Boolean(action)" @click="refreshKey">
              <KeyRound :size="17" />
              {{ action === 'key' ? 'Обновляем...' : 'Обновить ключ' }}
            </button>
          </div>
        </section>

        <DashboardStats :items="stats" />

        <div class="grid gap-4 xl:grid-cols-2">
          <section class="surface">
            <div class="section-heading">
              <div>
                <h2>Популярные страницы</h2>
                <p>Что посетители смотрят чаще всего.</p>
              </div>
              <BarChart3 :size="21" class="text-cyan-700" />
            </div>
            <div v-if="(summary?.top_pages || []).length" class="space-y-2">
              <div v-for="page in summary.top_pages" :key="page.pathname" class="flex items-center justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
                <span class="min-w-0 truncate text-sm font-medium text-slate-800">{{ page.pathname || '/' }}</span>
                <span class="status-badge status-neutral">{{ page.count }} просмотров</span>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading">
              <div>
                <h2>Устройства</h2>
                <p>С чего заходят посетители.</p>
              </div>
              <MonitorSmartphone :size="21" class="text-cyan-700" />
            </div>
            <div v-if="deviceRows.length" class="space-y-2">
              <div v-for="item in deviceRows" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm font-medium">{{ deviceLabel(item.name) }}</span>
                <strong class="text-sm text-slate-950">{{ item.percent }}%</strong>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Браузеры</h2><p>Клиентские браузеры посетителей.</p></div></div>
            <div v-if="browserRows.length" class="space-y-2">
              <div v-for="item in browserRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span>
                <strong class="text-sm">{{ item.percent }}%</strong>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Операционные системы</h2><p>Системы на устройствах посетителей.</p></div></div>
            <div v-if="osRows.length" class="space-y-2">
              <div v-for="item in osRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span>
                <strong class="text-sm">{{ item.percent }}%</strong>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Источники переходов</h2><p>Откуда приходит трафик.</p></div></div>
            <div v-if="(summary?.sources || []).length" class="space-y-2">
              <div v-for="item in summary.sources.slice(0, 8)" :key="item.referrer || 'direct'" class="grid grid-cols-[1fr_auto] items-center gap-3 border-b border-slate-100 py-3 last:border-0">
                <span class="truncate text-sm font-medium">{{ item.referrer || 'Прямой переход' }}</span>
                <span class="text-xs text-slate-500">{{ item.count }} визитов</span>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Время на сайте</h2><p>Средняя длительность визита.</p></div></div>
            <p class="text-4xl font-semibold text-slate-950">{{ formatSeconds(summary?.avg_duration || 0) }}</p>
            <p class="mt-2 text-sm text-slate-500">Всего: {{ formatSeconds(summary?.total_time_on_site_seconds || 0) }}</p>
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'heatmap'">
        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Тепловая карта кликов</h2>
              <p>{{ activePayload.total_clicks || 0 }} кликов за период.</p>
            </div>
            <Filter :size="20" class="text-cyan-700" />
          </div>
          <div class="grid gap-3 md:grid-cols-[1fr_180px_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <select v-model="deviceFilter" class="form-control" @change="loadActiveTab">
              <option value="all">Все устройства</option>
              <option value="desktop">Компьютер</option>
              <option value="mobile">Телефон</option>
              <option value="tablet">Планшет</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.8fr)]">
          <section class="surface">
            <div class="section-heading"><div><h2>Карта</h2><p>{{ heatmapCanvas.width }} x {{ heatmapCanvas.height }}</p></div></div>
            <div v-if="heatmapPoints.length" class="relative h-[620px] overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
              <div class="absolute inset-x-0 top-0 h-px bg-slate-200" />
              <div
                v-for="point in heatmapPoints"
                :key="`${point.x}-${point.y}-${point.count}`"
                class="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/70"
                :style="heatPointStyle(point)"
                :title="`${point.count} кликов`"
              />
            </div>
            <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Кликабельные элементы</h2><p>Группировка по тексту и тегу.</p></div></div>
            <div v-if="(activePayload.top_elements || []).length" class="space-y-2">
              <div v-for="item in activePayload.top_elements" :key="`${item.element}-${item.path}`" class="border-b border-slate-100 py-3 last:border-0">
                <div class="flex items-center justify-between gap-3">
                  <span class="min-w-0 truncate text-sm font-semibold text-slate-800">{{ item.element || item.tag || 'Без подписи' }}</span>
                  <span class="status-badge status-neutral">{{ item.count }}</span>
                </div>
                <p class="mt-1 truncate text-xs text-slate-500">{{ item.path }}</p>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'scrollmap'">
        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Карта скроллинга</h2>
              <p>Средняя глубина: {{ activePayload.average_depth || 0 }}%.</p>
            </div>
          </div>
          <div class="grid gap-3 md:grid-cols-[1fr_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <section class="surface">
            <div class="section-heading"><div><h2>Глубина просмотра</h2><p>{{ activePayload.sessions || 0 }} сессий со скроллом.</p></div></div>
            <div class="space-y-3">
              <div v-for="threshold in ['25', '50', '75', '100']" :key="threshold">
                <div class="mb-1 flex items-center justify-between text-sm">
                  <span class="font-medium text-slate-700">{{ threshold }}%</span>
                  <span class="text-slate-500">{{ activePayload.thresholds?.[threshold]?.rate || 0 }}%</span>
                </div>
                <div class="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div class="h-full rounded-full bg-cyan-600" :style="{ width: `${activePayload.thresholds?.[threshold]?.rate || 0}%` }" />
                </div>
              </div>
            </div>
          </section>
          <section class="surface">
            <div class="section-heading"><div><h2>Страницы с худшей глубиной</h2><p>Сортировка по средней глубине.</p></div></div>
            <div v-if="(activePayload.worst_pages || []).length" class="overflow-x-auto">
              <table class="data-table">
                <thead><tr><th>Страница</th><th>Сессии</th><th>Глубина</th></tr></thead>
                <tbody>
                  <tr v-for="page in activePayload.worst_pages" :key="page.path">
                    <td>{{ page.path }}</td>
                    <td>{{ page.sessions }}</td>
                    <td>{{ page.avg_depth }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'sessions'">
        <section class="surface">
          <div class="section-heading"><div><h2>Записи сессий</h2><p>{{ activePayload.count || 0 }} сессий за период.</p></div></div>
          <div v-if="(activePayload.results || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Дата</th><th>Устройство</th><th>Браузер</th><th>Длительность</th><th>Клики</th><th>Страницы</th><th></th></tr></thead>
              <tbody>
                <tr v-for="session in activePayload.results" :key="session.session_id">
                  <td>{{ formatDate(session.started_at) }}</td>
                  <td>{{ deviceLabel(session.device_type) }}</td>
                  <td>{{ session.browser }}</td>
                  <td>{{ formatSeconds(session.duration) }}</td>
                  <td>{{ session.clicks }}</td>
                  <td class="max-w-sm truncate">{{ (session.pages || []).join(' -> ') || '—' }}</td>
                  <td>
                    <button type="button" class="action-button-secondary min-h-9 px-3 py-1.5" @click="openSession(session.session_id)">
                      <Play :size="15" />
                      Воспроизвести
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>

        <section v-if="sessionLoading" class="empty-state"><span class="loading-dot" /><p>Загружаем сессию...</p></section>
        <section v-else-if="sessionDetail" class="surface">
          <div class="section-heading">
            <div>
              <h2>Timeline сессии</h2>
              <p>{{ sessionDetail.session.session_id }}</p>
            </div>
          </div>
          <div class="space-y-3">
            <div v-for="event in sessionDetail.events" :key="event.id" class="grid gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-[150px_140px_1fr]">
              <span class="text-xs text-slate-500">{{ formatDate(event.timestamp) }}</span>
              <span class="status-badge status-neutral justify-center">{{ event.type }}</span>
              <span class="min-w-0 truncate text-sm text-slate-700">{{ event.path }} {{ event.element ? `- ${event.element}` : '' }}</span>
            </div>
          </div>
        </section>
      </template>

      <template v-else-if="activeTab === 'paths'">
        <section class="surface">
          <div class="section-heading"><div><h2>Пути пользователей</h2><p>Популярные цепочки страниц.</p></div></div>
          <div v-if="(activePayload.paths || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Путь</th><th>Сессии</th><th>Конверсия</th><th>Средняя длительность</th></tr></thead>
              <tbody>
                <tr v-for="path in activePayload.paths" :key="path.path">
                  <td class="min-w-[360px]">{{ path.path }}</td>
                  <td>{{ path.sessions }}</td>
                  <td>{{ path.conversion }}%</td>
                  <td>{{ formatSeconds(path.avg_duration) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>

      <template v-else-if="activeTab === 'funnels'">
        <section class="surface">
          <div class="section-heading"><div><h2>{{ activePayload.name || 'Базовая воронка' }}</h2><p>Переходы между ключевыми шагами.</p></div></div>
          <div v-if="(activePayload.steps || []).length" class="grid gap-3 lg:grid-cols-4">
            <article v-for="step in activePayload.steps" :key="step.key" class="rounded-lg border border-slate-200 p-4">
              <p class="text-sm font-semibold text-slate-950">{{ step.title }}</p>
              <p class="mt-3 text-3xl font-semibold text-cyan-700">{{ step.users }}</p>
              <p class="mt-2 text-xs text-slate-500">Переход: {{ step.rate }}%, потери: {{ step.lost }}</p>
            </article>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>

      <template v-else-if="activeTab === 'events'">
        <section class="surface">
          <div class="section-heading"><div><h2>События</h2><p>Агрегация по типу, странице и элементу.</p></div></div>
          <div class="grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <select v-model="eventTypeFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все события</option>
              <option v-for="item in activePayload.types || []" :key="item.type" :value="item.type">{{ item.type }}</option>
            </select>
            <select v-model="deviceFilter" class="form-control" @change="loadActiveTab">
              <option value="all">Все устройства</option>
              <option value="desktop">Компьютер</option>
              <option value="mobile">Телефон</option>
              <option value="tablet">Планшет</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>
        <section class="surface">
          <div v-if="(activePayload.events || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Тип</th><th>Страница</th><th>Элемент</th><th>Количество</th><th>Уникальные</th><th>Последнее</th></tr></thead>
              <tbody>
                <tr v-for="event in activePayload.events" :key="`${event.event_type}-${event.page}-${event.element}`">
                  <td>{{ event.event_type }}</td>
                  <td>{{ event.page || '—' }}</td>
                  <td>{{ event.element || '—' }}</td>
                  <td>{{ event.count }}</td>
                  <td>{{ event.unique_visitors }}</td>
                  <td>{{ formatDate(event.last_seen) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>

      <template v-else-if="activeTab === 'pages'">
        <section class="surface">
          <div class="section-heading"><div><h2>Страницы</h2><p>Детальная аналитика по URL.</p></div></div>
          <div v-if="(activePayload.pages || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Страница</th><th>Просмотры</th><th>Уникальные</th><th>Время</th><th>Скролл</th><th>Клики</th><th>Заявки</th><th>Конверсия</th><th>Выходы</th><th>Отказы</th></tr></thead>
              <tbody>
                <tr v-for="page in activePayload.pages" :key="page.path">
                  <td class="min-w-[220px]">{{ page.path }}</td>
                  <td>{{ page.views }}</td>
                  <td>{{ page.unique_visitors }}</td>
                  <td>{{ formatSeconds(page.avg_time) }}</td>
                  <td>{{ page.avg_scroll_depth }}%</td>
                  <td>{{ page.clicks }}</td>
                  <td>{{ page.leads }}</td>
                  <td>{{ page.conversion }}%</td>
                  <td>{{ page.exits }}</td>
                  <td>{{ page.bounce_rate }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>

      <template v-else-if="activeTab === 'errors'">
        <section class="surface">
          <div class="section-heading"><div><h2>Ошибки</h2><p>JS errors, unhandled rejection и failed fetch.</p></div></div>
          <div v-if="(activePayload.errors || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Сообщение</th><th>Страница</th><th>Браузер</th><th>Устройство</th><th>Количество</th><th>Последняя дата</th></tr></thead>
              <tbody>
                <tr v-for="item in activePayload.errors" :key="`${item.message}-${item.page}`">
                  <td class="min-w-[260px]">{{ item.message }}</td>
                  <td>{{ item.page || '—' }}</td>
                  <td>{{ item.browser }}</td>
                  <td>{{ deviceLabel(item.device) }}</td>
                  <td>{{ item.count }}</td>
                  <td>{{ formatDate(item.last_seen) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>

      <template v-else-if="activeTab === 'performance'">
        <DashboardStats
          :items="[
            { label: 'LCP', value: `${activePayload.averages?.lcp || 0} ms`, sub: 'Largest Contentful Paint' },
            { label: 'CLS', value: activePayload.averages?.cls || 0, sub: 'Layout shift' },
            { label: 'INP', value: `${activePayload.averages?.inp || activePayload.averages?.fid || 0} ms`, sub: 'Interaction latency' },
            { label: 'TTFB', value: `${activePayload.averages?.ttfb || 0} ms`, sub: 'Response start' },
          ]"
        />
        <div class="grid gap-4 xl:grid-cols-2">
          <section class="surface">
            <div class="section-heading"><div><h2>Плохие страницы</h2><p>Срабатывания порогов производительности.</p></div></div>
            <div v-if="(activePayload.bad_pages || []).length" class="space-y-2">
              <div v-for="page in activePayload.bad_pages" :key="page.path" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm font-medium">{{ page.path }}</span>
                <span class="status-badge status-warning">{{ page.count }}</span>
              </div>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>
          <section class="surface">
            <div class="section-heading"><div><h2>По устройствам</h2><p>Средние значения по типу устройства.</p></div></div>
            <div v-if="(activePayload.devices || []).length" class="overflow-x-auto">
              <table class="data-table">
                <thead><tr><th>Устройство</th><th>LCP</th><th>CLS</th><th>INP</th><th>Load</th></tr></thead>
                <tbody>
                  <tr v-for="item in activePayload.devices" :key="item.device">
                    <td>{{ deviceLabel(item.device) }}</td>
                    <td>{{ item.metrics?.lcp || 0 }}</td>
                    <td>{{ item.metrics?.cls || 0 }}</td>
                    <td>{{ item.metrics?.inp || 0 }}</td>
                    <td>{{ item.metrics?.page_load_time || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state min-h-32"><p>{{ emptyText }}</p></div>
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'recommendations'">
        <section class="surface">
          <div class="section-heading"><div><h2>AI-рекомендации</h2><p>Правила и локальные сигналы без внешнего AI API.</p></div></div>
          <div v-if="(activePayload.recommendations || []).length" class="grid gap-3 lg:grid-cols-2">
            <article v-for="item in activePayload.recommendations" :key="`${item.title}-${item.page}`" class="rounded-lg border border-slate-200 p-4">
              <div class="flex items-start justify-between gap-3">
                <h3 class="text-base font-semibold text-slate-950">{{ item.title }}</h3>
                <span class="status-badge" :class="importanceClass(item.importance)">{{ importanceLabel(item.importance) }}</span>
              </div>
              <p v-if="item.page" class="mt-2 text-sm font-medium text-cyan-700">{{ item.page }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.reason }}</p>
            </article>
          </div>
          <div v-else class="empty-state"><p>{{ emptyText }}</p></div>
        </section>
      </template>
    </template>
  </div>
</template>
