<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Download, FileSearch, Play, RefreshCw } from '@lucide/vue'

import {
  createCompetitorAnalysis,
  downloadCompetitorAnalysisPdf,
  getCompetitorAnalyses,
  getCompetitorAnalysis,
} from '../api/competitors'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const competitors = ref(['', '', ''])
const analyses = ref([])
const loading = ref(false)
const starting = ref(false)
const downloadingId = ref(null)
const error = ref('')
const success = ref('')
let timer = null

const siteId = computed(() => Number(route.params.siteId || 0))
const latestAnalysis = computed(() => analyses.value[0] || null)
const running = computed(() => ['pending', 'running'].includes(String(latestAnalysis.value?.status || '').toLowerCase()))

function statusText(status) {
  return {
    pending: 'Ожидает запуска',
    running: 'Выполняется',
    done: 'Готово',
    error: 'Ошибка',
  }[String(status || '').toLowerCase()] || 'Не запускался'
}

function statusClass(status) {
  return {
    pending: 'status-neutral',
    running: 'status-warning',
    done: 'status-success',
    error: 'status-danger',
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

function cleanCompetitors() {
  return competitors.value.map((item) => item.trim()).filter(Boolean)
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
      if (!['pending', 'running'].includes(String(data.status || '').toLowerCase())) {
        stopPolling()
        if (data.status === 'done') success.value = 'PDF-отчёт сформирован.'
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
    if (running.value) startPolling(latestAnalysis.value.id)
  } catch (e) {
    console.error('Competitor analyses load failed', e)
    error.value = e?.response?.data?.detail || 'Не удалось загрузить историю анализа.'
  } finally {
    loading.value = false
  }
}

async function startAnalysis() {
  const domains = cleanCompetitors()
  if (!domains.length) {
    error.value = 'Укажите хотя бы один домен конкурента.'
    return
  }
  if (domains.length > 3 || starting.value || running.value) return

  starting.value = true
  error.value = ''
  success.value = ''
  try {
    const data = await createCompetitorAnalysis(siteId.value, domains)
    updateAnalysisInList(data)
    startPolling(data.id)
    success.value = data.queued ? 'Анализ поставлен в очередь.' : 'Анализ создан, но очередь задач недоступна.'
  } catch (e) {
    console.error('Competitor analysis start failed', e)
    const detail = e?.response?.data?.detail || e?.response?.data?.competitors?.[0] || ''
    error.value = detail || 'Не удалось запустить анализ конкурентов.'
  } finally {
    starting.value = false
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
      <p>Сравните ваш сайт с конкурентами и получите PDF-отчёт.</p>
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

      <div class="grid gap-3 md:grid-cols-3">
        <label v-for="(_, index) in competitors" :key="index" class="block">
          <span class="text-sm font-semibold text-slate-800">Конкурент №{{ index + 1 }}</span>
          <input
            v-model="competitors[index]"
            class="form-control mt-2"
            type="text"
            inputmode="url"
            placeholder="competitor.ru"
            :disabled="starting || running"
          >
        </label>
      </div>

      <div class="mt-4 flex flex-col gap-2 sm:flex-row">
        <button type="button" class="action-button-primary" :disabled="starting || running" @click="startAnalysis">
          <span v-if="starting || running" class="button-spinner" aria-hidden="true" />
          <Play v-else :size="17" />
          {{ starting || running ? 'Анализ выполняется...' : 'Запустить анализ' }}
        </button>
        <button
          type="button"
          class="action-button-secondary"
          :disabled="!latestAnalysis?.pdf_available || downloadingId === latestAnalysis?.id"
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
        <div>
          <p class="text-sm font-semibold text-slate-800">Домены конкурентов</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <span
              v-for="domain in latestAnalysis.competitors"
              :key="domain"
              class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm text-slate-700"
            >
              {{ domain }}
            </span>
          </div>
        </div>
        <button
          type="button"
          class="action-button-secondary"
          :disabled="!latestAnalysis.pdf_available || downloadingId === latestAnalysis.id"
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
              <th>Домены</th>
              <th class="text-right">PDF</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="analysis in analyses" :key="analysis.id">
              <td>{{ formatDate(analysis.finished_at || analysis.updated_at || analysis.created_at) }}</td>
              <td>
                <span class="status-badge" :class="statusClass(analysis.status)">{{ statusText(analysis.status) }}</span>
              </td>
              <td>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="domain in analysis.competitors"
                    :key="`${analysis.id}-${domain}`"
                    class="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-700"
                  >
                    {{ domain }}
                  </span>
                </div>
              </td>
              <td class="text-right">
                <button
                  type="button"
                  class="action-button-secondary min-h-10 px-3 py-2"
                  :disabled="!analysis.pdf_available || downloadingId === analysis.id"
                  @click="downloadPdf(analysis)"
                >
                  <Download :size="16" />
                  Скачать
                </button>
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
