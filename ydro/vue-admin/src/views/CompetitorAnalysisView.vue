<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Download, FileSearch, Play, RefreshCw, StopCircle } from '@lucide/vue'

import {
  cancelCompetitorAnalysis,
  createCompetitorAnalysis,
  downloadCompetitorAnalysisPdf,
  getCompetitorAnalyses,
  getCompetitorAnalysis,
} from '../api/competitors'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const form = ref({
  user_domain: '',
  competitor_domain: '',
})
const analyses = ref([])
const loading = ref(false)
const starting = ref(false)
const cancelingId = ref(null)
const downloadingId = ref(null)
const error = ref('')
const success = ref('')
let timer = null

const siteId = computed(() => Number(route.params.siteId || 0))
const latestAnalysis = computed(() => analyses.value[0] || null)
const activeStatuses = new Set(['pending', 'running', 'processing'])
const running = computed(() => activeStatuses.has(String(latestAnalysis.value?.status || '').toLowerCase()))

function statusText(status) {
  return {
    pending: 'Ожидает запуска',
    running: 'Выполняется',
    processing: 'Выполняется',
    completed: 'Готово',
    done: 'Готово',
    failed: 'Ошибка',
    error: 'Ошибка',
    canceled: 'Остановлен',
    cancelled: 'Остановлен',
    stopped: 'Остановлен',
  }[String(status || '').toLowerCase()] || 'Не запускался'
}

function statusClass(status) {
  return {
    pending: 'status-neutral',
    running: 'status-warning',
    processing: 'status-warning',
    completed: 'status-success',
    done: 'status-success',
    failed: 'status-danger',
    error: 'status-danger',
    canceled: 'status-neutral',
    cancelled: 'status-neutral',
    stopped: 'status-neutral',
  }[String(status || '').toLowerCase()] || 'status-neutral'
}

function formatDate(value) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return '—'
  }
}

function syncUserDomainFromSite() {
  if (!form.value.user_domain && siteStore.currentSite?.domain) {
    form.value.user_domain = siteStore.currentSite.domain
  }
}

function cleanDomain(value) {
  return String(value || '').trim()
}

function extractApiError(e, fallback) {
  const data = e?.response?.data || {}
  const detail = data.detail
  if (Array.isArray(detail)) return detail[0] || fallback
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object') return Object.values(detail).flat()[0] || fallback
  return data.user_domain?.[0] || data.competitor_domain?.[0] || data.competitors?.[0] || fallback
}

function updateAnalysisInList(nextAnalysis) {
  if (!nextAnalysis?.id) return
  const index = analyses.value.findIndex((item) => item.id === nextAnalysis.id)
  if (index >= 0) {
    analyses.value[index] = nextAnalysis
  } else {
    analyses.value.unshift(nextAnalysis)
  }
  analyses.value = [...analyses.value].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
}

function stopPolling() {
  if (timer) clearInterval(timer)
  timer = null
}

function startPolling(analysisId) {
  stopPolling()
  if (!analysisId || !siteId.value) return
  timer = setInterval(async () => {
    try {
      const data = await getCompetitorAnalysis(siteId.value, analysisId)
      updateAnalysisInList(data)
      if (!activeStatuses.has(String(data.status || '').toLowerCase())) {
        stopPolling()
        if (['completed', 'done'].includes(String(data.status || '').toLowerCase())) success.value = 'PDF-отчёт сформирован.'
      }
    } catch (e) {
      console.error('Competitor analysis polling failed', e)
      error.value = 'Не удалось обновить статус анализа.'
      stopPolling()
    }
  }, 4000)
}

async function loadAnalyses() {
  if (!siteId.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await getCompetitorAnalyses(siteId.value)
    analyses.value = Array.isArray(data?.rows) ? data.rows : []
    syncUserDomainFromSite()
    if (running.value) startPolling(latestAnalysis.value.id)
  } catch (e) {
    console.error('Competitor analyses load failed', e)
    error.value = e?.response?.data?.detail || 'Не удалось загрузить историю анализа.'
  } finally {
    loading.value = false
  }
}

async function startAnalysis() {
  const userDomain = cleanDomain(form.value.user_domain)
  const competitorDomain = cleanDomain(form.value.competitor_domain)
  if (!userDomain) {
    error.value = 'Укажите домен вашего сайта.'
    return
  }
  if (!competitorDomain) {
    error.value = 'Укажите домен конкурента.'
    return
  }
  if (starting.value || running.value) return

  starting.value = true
  error.value = ''
  success.value = ''
  try {
    const data = await createCompetitorAnalysis(siteId.value, {
      user_domain: userDomain,
      competitor_domain: competitorDomain,
    })
    updateAnalysisInList(data)
    startPolling(data.id)
    success.value = data.queued ? 'Анализ поставлен в очередь.' : 'Анализ создан, но очередь задач недоступна.'
  } catch (e) {
    console.error('Competitor analysis start failed', e)
    error.value = extractApiError(e, 'Не удалось запустить анализ конкурентов.')
  } finally {
    starting.value = false
  }
}

async function cancelAnalysis(analysis) {
  if (!analysis?.id || !activeStatuses.has(String(analysis.status || '').toLowerCase())) return
  if (!window.confirm('Остановить анализ конкурентов?')) return

  cancelingId.value = analysis.id
  error.value = ''
  success.value = ''
  try {
    const data = await cancelCompetitorAnalysis(siteId.value, analysis.id)
    updateAnalysisInList(data)
    stopPolling()
    success.value = data?.detail || 'Анализ остановлен.'
  } catch (e) {
    console.error('Competitor analysis cancel failed', e)
    error.value = e?.response?.data?.detail || 'Не удалось остановить анализ.'
  } finally {
    cancelingId.value = null
  }
}

async function downloadPdf(analysis) {
  if (!analysis?.id || !analysis.pdf_available) return
  downloadingId.value = analysis.id
  error.value = ''
  try {
    const blob = await downloadCompetitorAnalysisPdf(siteId.value, analysis.id)
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `competitor-analysis-${siteStore.currentSite?.slug || siteId.value}.pdf`
    link.click()
    URL.revokeObjectURL(href)
  } catch (e) {
    console.error('Competitor analysis PDF download failed', e)
    error.value = e?.response?.data?.detail || 'Не удалось скачать PDF-отчёт.'
  } finally {
    downloadingId.value = null
  }
}

onMounted(async () => {
  if (siteId.value) {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    syncUserDomainFromSite()
  }
  await loadAnalyses()
})

onUnmounted(stopPolling)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">SEO</p>
      <h1>Анализ конкурентов</h1>
      <p>Сравните ваш сайт с сайтом конкурента и получите PDF-отчёт с ошибками и рекомендациями.</p>
    </header>

    <section class="surface">
      <div class="section-heading">
        <div>
          <h2>Новый анализ</h2>
          <p>{{ siteStore.currentSite?.domain || siteStore.currentSite?.name || 'Выбранный сайт' }}</p>
        </div>
        <button type="button" class="action-button-secondary" :disabled="loading" @click="loadAnalyses">
          <RefreshCw :size="17" :class="loading ? 'animate-spin' : ''" />
          Обновить
        </button>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-800">Ваш сайт</span>
          <input
            v-model="form.user_domain"
            class="form-control mt-2"
            type="text"
            inputmode="url"
            placeholder="novoe-konakovo.ru"
            :disabled="starting || running || Boolean(cancelingId)"
          >
        </label>
        <label class="block">
          <span class="text-sm font-semibold text-slate-800">Сайт конкурента</span>
          <input
            v-model="form.competitor_domain"
            class="form-control mt-2"
            type="text"
            inputmode="url"
            placeholder="leelabird.ru"
            :disabled="starting || running || Boolean(cancelingId)"
          >
        </label>
      </div>

      <div class="mt-4 flex flex-col gap-2 sm:flex-row">
        <button type="button" class="action-button-primary" :disabled="starting || running || Boolean(cancelingId)" @click="startAnalysis">
          <span v-if="starting || running" class="button-spinner" aria-hidden="true" />
          <Play v-else :size="17" />
          {{ starting || running ? 'Анализ выполняется...' : 'Запустить анализ' }}
        </button>
        <button
          v-if="latestAnalysis && running"
          type="button"
          class="action-button-danger"
          :disabled="cancelingId === latestAnalysis.id"
          @click="cancelAnalysis(latestAnalysis)"
        >
          <span v-if="cancelingId === latestAnalysis.id" class="button-spinner" aria-hidden="true" />
          <StopCircle v-else :size="17" />
          {{ cancelingId === latestAnalysis.id ? 'Останавливаем...' : 'Остановить анализ' }}
        </button>
        <button
          v-if="latestAnalysis?.pdf_available"
          type="button"
          class="action-button-secondary"
          :disabled="downloadingId === latestAnalysis?.id"
          @click="downloadPdf(latestAnalysis)"
        >
          <Download :size="17" />
          {{ downloadingId === latestAnalysis?.id ? 'Готовим...' : 'Скачать PDF' }}
        </button>
      </div>
    </section>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <p v-if="success" class="notice-success" role="status">{{ success }}</p>

    <section class="surface">
      <div class="section-heading">
        <div>
          <h2>Текущий статус</h2>
          <p>{{ latestAnalysis ? formatDate(latestAnalysis.finished_at || latestAnalysis.updated_at || latestAnalysis.created_at) : '—' }}</p>
        </div>
        <span class="status-badge" :class="statusClass(latestAnalysis?.status)">
          {{ statusText(latestAnalysis?.status) }}
        </span>
      </div>

      <div v-if="latestAnalysis" class="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <p class="text-sm font-semibold text-slate-800">Ваш домен</p>
            <p class="mt-1 text-sm text-slate-700">{{ latestAnalysis.user_domain || '—' }}</p>
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-800">Домен конкурента</p>
            <p class="mt-1 text-sm text-slate-700">{{ latestAnalysis.competitor_domain || '—' }}</p>
          </div>
        </div>
        <button
          v-if="latestAnalysis.pdf_available"
          type="button"
          class="action-button-secondary"
          :disabled="downloadingId === latestAnalysis.id"
          @click="downloadPdf(latestAnalysis)"
        >
          <Download :size="17" />
          Скачать PDF
        </button>
      </div>

      <div v-else class="empty-state">
        <FileSearch :size="30" />
        <h2>Анализ ещё не запускался</h2>
        <p>После запуска здесь появятся статус, дата и список доменов.</p>
      </div>
    </section>

    <section class="surface">
      <div class="section-heading">
        <div>
          <h2>История запусков</h2>
          <p>Последние анализы выбранного сайта.</p>
        </div>
      </div>

      <div v-if="analyses.length" class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Статус</th>
              <th>Ваш сайт</th>
              <th>Конкурент</th>
              <th class="text-right">PDF</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="analysis in analyses" :key="analysis.id">
              <td>{{ formatDate(analysis.finished_at || analysis.updated_at || analysis.created_at) }}</td>
              <td>
                <span class="status-badge" :class="statusClass(analysis.status)">{{ statusText(analysis.status) }}</span>
              </td>
              <td>{{ analysis.user_domain || '—' }}</td>
              <td>{{ analysis.competitor_domain || analysis.competitors?.[0] || '—' }}</td>
              <td class="text-right">
                <button
                  v-if="analysis.pdf_available"
                  type="button"
                  class="action-button-secondary min-h-10 px-3 py-2"
                  :disabled="downloadingId === analysis.id"
                  @click="downloadPdf(analysis)"
                >
                  <Download :size="16" />
                  Скачать
                </button>
                <span v-else class="text-sm text-slate-400">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-state">
        <FileSearch :size="30" />
        <h2>История пуста</h2>
        <p>Запустите первый анализ для выбранного сайта.</p>
      </div>
    </section>
  </div>
</template>
