<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Download, SearchCheck } from '@lucide/vue'

import { miniSeoDetail, miniSeoExport, miniSeoIssues, miniSeoLatest, miniSeoStart } from '../../api/mini'
import { useSiteStore } from '../../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const domain = ref('')
const loadingLatest = ref(false)
const startingAudit = ref(false)
const downloading = ref(false)
const error = ref('')
const success = ref('')
const latest = ref(null)
const detail = ref(null)
const issues = ref([])
let timer = null

const siteId = computed(() => Number(route.params.siteId || 0))
const seoParams = computed(() => (siteId.value ? { site_id: siteId.value } : {}))
const auditId = computed(() => latest.value?.audit_id || detail.value?.audit_id)
const running = computed(() => ['pending', 'running'].includes(String(detail.value?.status || latest.value?.status || '').toLowerCase()))
const checking = computed(() => startingAudit.value || running.value)
const score = computed(() => Number(detail.value?.score ?? latest.value?.score ?? 0))

function auditStatus() {
  return String(detail.value?.status || latest.value?.status || '').toLowerCase()
}

function statusText() {
  const status = auditStatus()
  return { pending: 'Ждет запуска', running: 'Проверяем сайт', done: 'Проверка завершена', completed: 'Проверка завершена', failed: 'Не удалось проверить сайт', error: 'Не удалось проверить сайт' }[status] || 'Проверка не запускалась'
}

function severityInfo(value) {
  return {
    high: { label: 'Критично', class: 'status-danger' },
    medium: { label: 'Важно', class: 'status-warning' },
    low: { label: 'Рекомендация', class: 'status-neutral' },
  }[value] || { label: 'Рекомендация', class: 'status-neutral' }
}

function errorMessage(e, fallback) {
  const detail = e?.response?.data?.detail || ''
  if (String(detail).includes('Client dashboard access')) {
    return 'Нет доступа к SEO-аудиту выбранного сайта.'
  }
  return detail || fallback
}

function startAuditErrorMessage(e) {
  const detail = e?.response?.data?.detail || ''
  if (String(detail).includes('Client dashboard access')) {
    return 'Нет доступа к SEO-аудиту выбранного сайта.'
  }
  return 'Не удалось выполнить SEO-аудит. Попробуйте позже.'
}

async function loadAudit(id) {
  detail.value = await miniSeoDetail(id, seoParams.value)
  const result = await miniSeoIssues(id, seoParams.value)
  issues.value = result?.rows || []
}

function handleAuditCompletion(showMessage = false) {
  const status = auditStatus()
  if (!['done', 'completed', 'failed', 'error'].includes(status)) return

  stopPolling()
  if (['done', 'completed'].includes(status)) {
    if (showMessage) success.value = 'SEO-аудит завершен.'
    return
  }

  error.value = 'Не удалось выполнить SEO-аудит. Попробуйте позже.'
}

function stopPolling() {
  if (timer) clearInterval(timer)
  timer = null
}

function startPolling() {
  stopPolling()
  timer = setInterval(async () => {
    try {
      await loadAudit(auditId.value)
      handleAuditCompletion(true)
    } catch (e) {
      console.error('SEO audit polling failed', e)
      error.value = 'Не удалось выполнить SEO-аудит. Попробуйте позже.'
      stopPolling()
    }
  }, 4000)
}

async function findLatest() {
  if (!domain.value.trim()) { error.value = 'Введите домен сайта.'; return }
  loadingLatest.value = true; error.value = ''; success.value = ''
  try {
    latest.value = await miniSeoLatest(domain.value.trim(), seoParams.value)
    if (latest.value?.audit_id) {
      await loadAudit(latest.value.audit_id)
      if (running.value) startPolling()
    }
  } catch (e) { error.value = errorMessage(e, 'Для этого домена еще нет готовой проверки.') }
  finally { loadingLatest.value = false }
}

async function startAudit() {
  if (!domain.value.trim()) { error.value = 'Введите домен сайта.'; return }
  if (checking.value) return
  startingAudit.value = true; error.value = ''; success.value = ''; issues.value = []
  try {
    latest.value = await miniSeoStart(domain.value.trim(), seoParams.value)
    await loadAudit(latest.value.audit_id)
    if (running.value) startPolling()
    else handleAuditCompletion(true)
  } catch (e) {
    console.error('SEO audit start failed', e)
    error.value = startAuditErrorMessage(e)
  } finally { startingAudit.value = false }
}

async function downloadPdf() {
  if (!auditId.value) return
  downloading.value = true; error.value = ''
  try {
    const blob = await miniSeoExport(auditId.value, seoParams.value)
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href; link.download = `seo-audit-${domain.value}.pdf`; link.click()
    URL.revokeObjectURL(href)
  } catch (e) { error.value = errorMessage(e, 'Не удалось скачать PDF-отчет.') }
  finally { downloading.value = false }
}

onMounted(async () => {
  if (siteId.value) {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    domain.value = siteStore.currentSite?.domain || ''
  }
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">Проверка сайта</p>
      <h1>SEO-аудит</h1>
      <p>Найдите проблемы, которые мешают сайту быть заметнее в поиске.</p>
    </header>

    <section class="surface">
      <label class="text-sm font-semibold text-slate-800" for="seo-domain">Домен сайта</label>
      <div class="mt-2 flex flex-col gap-2 sm:flex-row">
        <input id="seo-domain" v-model="domain" class="form-control flex-1" placeholder="example.com" :disabled="checking">
        <button type="button" class="action-button-primary" :disabled="checking" @click="startAudit">
          <span v-if="checking" class="button-spinner" aria-hidden="true" />
          <SearchCheck v-else :size="18" />
          {{ checking ? 'Проверяем сайт...' : 'Проверить сайт' }}
        </button>
        <button type="button" class="action-button-secondary" :disabled="checking || loadingLatest" @click="findLatest">
          {{ loadingLatest ? 'Загружаем...' : 'Показать прошлую проверку' }}
        </button>
      </div>
    </section>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <p v-if="success" class="notice-success" role="status">{{ success }}</p>
    <section v-if="checking" class="notice-info flex items-start gap-3" aria-live="polite" aria-busy="true">
      <span class="button-spinner mt-0.5 text-brand-700" aria-hidden="true" />
      <span>Идет SEO-аудит сайта. Это может занять до 30–60 секунд. Не закрывайте страницу.</span>
    </section>

    <template v-if="detail || latest">
      <section class="grid gap-4 sm:grid-cols-[220px_1fr]">
        <article class="surface flex min-h-44 flex-col items-center justify-center text-center">
          <p class="text-sm text-slate-500">Оценка SEO</p>
          <p class="mt-2 text-5xl font-semibold" :class="score >= 80 ? 'text-emerald-600' : score >= 50 ? 'text-amber-600' : 'text-rose-600'">{{ score }}</p>
          <p class="mt-2 text-sm text-slate-600">{{ statusText() }}</p>
        </article>
        <article class="surface">
          <div class="section-heading">
            <div><h2>Результат проверки</h2><p>Исправляйте проблемы сверху вниз.</p></div>
            <button type="button" class="action-button-secondary" :disabled="!auditId || downloading" @click="downloadPdf"><Download :size="17" />{{ downloading ? 'Готовим...' : 'Скачать PDF' }}</button>
          </div>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div class="rounded-lg bg-slate-50 p-3"><p class="text-xs text-slate-500">Проверено страниц</p><strong class="mt-1 block text-xl">{{ detail?.pages_count || 0 }}</strong></div>
            <div class="rounded-lg bg-rose-50 p-3"><p class="text-xs text-rose-600">Критичных проблем</p><strong class="mt-1 block text-xl text-rose-700">{{ detail?.breakdown?.high_issues || 0 }}</strong></div>
            <div class="rounded-lg bg-amber-50 p-3"><p class="text-xs text-amber-700">Важных проблем</p><strong class="mt-1 block text-xl text-amber-800">{{ detail?.breakdown?.medium_issues || 0 }}</strong></div>
          </div>
        </article>
      </section>

      <section>
        <div class="section-heading"><div><h2>Найденные проблемы</h2><p>Простые объяснения и рекомендации по исправлению.</p></div></div>
        <div v-if="issues.length" class="grid gap-3">
          <article v-for="issue in issues" :key="issue.id" class="surface">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <span class="status-badge" :class="severityInfo(issue.severity).class">{{ severityInfo(issue.severity).label }}</span>
                <h3 class="mt-3 font-semibold text-slate-950">{{ issue.issue_title || 'Проблема на странице' }}</h3>
                <p class="mt-2 break-words text-sm text-slate-500">{{ issue.page_url || domain }}</p>
                <p class="mt-3 text-sm leading-6 text-slate-700">{{ issue.recommendation || 'Проверьте страницу и исправьте найденную проблему.' }}</p>
              </div>
            </div>
          </article>
        </div>
        <div v-else class="empty-state"><SearchCheck :size="30" /><h2>Проблем не найдено</h2><p>Или проверка еще выполняется.</p></div>
      </section>
    </template>
  </div>
</template>
