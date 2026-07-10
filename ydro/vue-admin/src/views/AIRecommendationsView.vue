<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Clock3, History, RefreshCw, Trash2 } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import { createAIRecommendationJob, deleteAIRecommendationJob, listAIRecommendationJobs, retryAIRecommendationJob } from '../api/aiRecommendations'
import AiRecommendationCard from '../components/ai-recommendations/AiRecommendationCard.vue'
import AiRecommendationsEmptyState from '../components/ai-recommendations/AiRecommendationsEmptyState.vue'
import AiRecommendationsErrorState from '../components/ai-recommendations/AiRecommendationsErrorState.vue'
import AiRecommendationsFilters from '../components/ai-recommendations/AiRecommendationsFilters.vue'
import AiRecommendationsHero from '../components/ai-recommendations/AiRecommendationsHero.vue'
import AiRecommendationsLockedState from '../components/ai-recommendations/AiRecommendationsLockedState.vue'
import AiRecommendationsSkeleton from '../components/ai-recommendations/AiRecommendationsSkeleton.vue'
import AiRecommendationsSummary from '../components/ai-recommendations/AiRecommendationsSummary.vue'
import { formatDate, normalizeResult } from '../utils/aiRecommendations'
import { useAccessStore } from '../stores/access'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()
const accessStore = useAccessStore()
const jobs = ref([])
const loading = ref(true)
const creating = ref(false)
const requestFailed = ref(false)
const forbidden = ref(false)
const selectedId = ref(null)
const priority = ref('all')
const category = ref('all')
const type = ref('combined')
const today = new Date()
const monthAgo = new Date(Date.now() - 30 * 86400000)
const periodFrom = ref(monthAgo.toISOString().slice(0, 10))
const periodTo = ref(today.toISOString().slice(0, 10))
let pollingTimer

const isLocked = computed(() => forbidden.value || (accessStore.loaded && !accessStore.can('ai_recommendations')))
const selected = computed(() => jobs.value.find((job) => job.id === selectedId.value) || jobs.value[0] || null)
const normalized = computed(() => normalizeResult(selected.value?.result))
const hasActiveJob = computed(() => jobs.value.some((job) => ['queued', 'processing'].includes(job.status)))
const categories = computed(() => [...new Set(normalized.value.recommendations.map((item) => item.category))])
const filtered = computed(() => normalized.value.recommendations.filter((item) => (priority.value === 'all' || item.priority === priority.value) && (category.value === 'all' || item.category === category.value)))
const grouped = computed(() => {
  const result = new Map()
  for (const item of filtered.value) {
    if (!result.has(item.category)) result.set(item.category, [])
    result.get(item.category).push(item)
  }
  return [...result.entries()]
})
const highCount = computed(() => normalized.value.recommendations.filter((item) => item.priority === 'high').length)
const analysisTypeLabel = { combined: 'Комплексный анализ', seo: 'Заметность в поиске', conversion: 'Рост обращений' }
const heroState = computed(() => {
  if (isLocked.value) return { status: 'AI-рекомендации недоступны на текущем тарифе', tone: 'locked' }
  if (creating.value || ['queued', 'processing'].includes(selected.value?.status)) return { status: 'Анализируем данные', tone: 'loading' }
  if (requestFailed.value || selected.value?.status === 'failed') return { status: 'Произошла ошибка анализа', tone: 'error' }
  if (!normalized.value.recommendations.length) return { status: 'Недостаточно данных', tone: 'empty' }
  return { status: 'Рекомендации готовы', tone: 'ready' }
})
const summaryItems = computed(() => {
  if (!selected.value || !normalized.value.recommendations.length) return []
  return [
    { key: 'count', label: 'Найдено рекомендаций', value: normalized.value.recommendations.length },
    highCount.value ? { key: 'high', label: 'Высокий приоритет', value: highCount.value } : null,
    selected.value.completed_at || selected.value.created_at ? { key: 'date', label: 'Последний анализ', value: formatDate(selected.value.completed_at || selected.value.created_at) } : null,
    selected.value.period_from && selected.value.period_to ? { key: 'period', label: 'Период данных', value: `${selected.value.period_from} — ${selected.value.period_to}` } : null,
    normalized.value.potential !== null && normalized.value.potential !== undefined ? { key: 'potential', label: 'Потенциал улучшения', value: normalized.value.potential } : null,
  ].filter(Boolean)
})

async function load({ silent = false } = {}) {
  if (isLocked.value) { loading.value = false; return }
  if (!silent) loading.value = true
  try {
    const { data } = await listAIRecommendationJobs()
    jobs.value = (Array.isArray(data) ? data : data?.results || []).filter((job) => Number(job.site) === Number(route.params.siteId))
    if (!jobs.value.some((job) => job.id === selectedId.value)) selectedId.value = jobs.value[0]?.id || null
    requestFailed.value = false
  } catch (error) {
    if (error.response?.status === 403) forbidden.value = true
    requestFailed.value = true
  } finally {
    loading.value = false
  }
}

async function createJob() {
  if (creating.value || isLocked.value) return
  creating.value = true
  requestFailed.value = false
  try {
    const { data } = await createAIRecommendationJob({ site_id: Number(route.params.siteId), recommendation_type: type.value, period_from: periodFrom.value, period_to: periodTo.value })
    jobs.value = [data, ...jobs.value.filter((job) => job.id !== data.id)]
    selectedId.value = data.id
  } catch {
    requestFailed.value = true
  } finally {
    creating.value = false
  }
}

async function retry() {
  if (!selected.value || creating.value) return
  creating.value = true
  try { await retryAIRecommendationJob(selected.value.id); await load({ silent: true }); requestFailed.value = false } catch { requestFailed.value = true } finally { creating.value = false }
}

async function remove(job) {
  if (creating.value) return
  await deleteAIRecommendationJob(job.id)
  jobs.value = jobs.value.filter((item) => item.id !== job.id)
  selectedId.value = jobs.value[0]?.id || null
}

function selectSite(event) { router.push(`/sites/${event.target.value}/ai-recommendations`) }

watch(() => route.params.siteId, async () => { selectedId.value = null; priority.value = 'all'; category.value = 'all'; await siteStore.fetchSite(route.params.siteId); await load() })
watch(selectedId, () => { priority.value = 'all'; category.value = 'all' })

onMounted(async () => {
  if (!accessStore.loaded) { try { await accessStore.fetchAccess() } catch { /* Backend remains authoritative. */ } }
  if (isLocked.value) { loading.value = false; return }
  if (!siteStore.sites.length) await siteStore.fetchSites()
  await siteStore.fetchSite(route.params.siteId)
  await load()
  pollingTimer = window.setInterval(() => { if (hasActiveJob.value) load({ silent: true }) }, 10000)
})
onBeforeUnmount(() => window.clearInterval(pollingTimer))
</script>

<template>
  <div class="ai-page min-w-0 space-y-5 overflow-x-clip">
    <AiRecommendationsLockedState v-if="isLocked" />
    <AiRecommendationsSkeleton v-else-if="loading" />
    <template v-else>
      <AiRecommendationsHero :status="heroState.status" :tone="heroState.tone" :busy="creating || hasActiveJob" :updated-at="formatDate(selected?.completed_at || selected?.updated_at)" @refresh="createJob" />

      <section class="grid min-w-0 gap-3 rounded-2xl border border-brand-100 bg-white/85 p-3 shadow-soft sm:grid-cols-2 lg:grid-cols-5">
        <label class="min-w-0 text-xs font-medium text-slate-500">Сайт<select class="input mt-1 w-full min-w-0" :value="route.params.siteId" @change="selectSite"><option v-for="site in siteStore.sites" :key="site.id" :value="site.id">{{ site.name }}</option></select></label>
        <label class="min-w-0 text-xs font-medium text-slate-500">Начало периода<input v-model="periodFrom" type="date" class="input mt-1 w-full min-w-0" /></label>
        <label class="min-w-0 text-xs font-medium text-slate-500">Конец периода<input v-model="periodTo" type="date" class="input mt-1 w-full min-w-0" /></label>
        <label class="min-w-0 text-xs font-medium text-slate-500">Направление<select v-model="type" class="input mt-1 w-full min-w-0"><option value="combined">Комплексный анализ</option><option value="seo">Заметность в поиске</option><option value="conversion">Рост обращений</option></select></label>
        <div class="flex items-end"><button class="btn-secondary w-full" :disabled="creating || hasActiveJob" @click="createJob"><RefreshCw :size="17" :class="creating && 'animate-spin'" />{{ creating ? 'Подготавливаем…' : 'Запустить анализ' }}</button></div>
      </section>

      <div v-if="creating || ['queued','processing'].includes(selected?.status)" class="flex items-center gap-3 rounded-2xl border border-brand-100 bg-brand-50 p-4 text-sm font-medium text-brand-900"><RefreshCw class="shrink-0 animate-spin" :size="19" />Анализируем данные сайта и подготавливаем рекомендации…</div>
      <AiRecommendationsErrorState v-if="requestFailed || selected?.status === 'failed'" :busy="creating" @retry="selected?.status === 'failed' ? retry() : load()" />

      <template v-else-if="!creating && !['queued','processing'].includes(selected?.status)">
        <AiRecommendationsEmptyState v-if="!normalized.recommendations.length" @create="createJob" />
        <template v-else>
          <AiRecommendationsSummary :items="summaryItems" />
          <section v-if="normalized.summary" class="rounded-2xl border border-brand-100 bg-gradient-to-r from-brand-50 to-white p-5"><p class="text-xs font-bold uppercase tracking-wide text-brand-600">Краткий вывод</p><p class="mt-2 whitespace-pre-line break-words text-sm leading-6 text-slate-700">{{ normalized.summary }}</p></section>
          <AiRecommendationsFilters v-model:priorities="priority" v-model:category="category" :categories="categories" />
          <div class="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_15rem]">
            <main class="min-w-0 space-y-7"><section v-for="group in grouped" :key="group[0]" class="min-w-0"><div class="mb-3 flex items-center gap-3"><h2 class="text-lg font-bold text-slate-900">{{ group[0] }}</h2><span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">{{ group[1].length }}</span></div><div class="grid min-w-0 gap-4 2xl:grid-cols-2"><AiRecommendationCard v-for="(item, index) in group[1]" :key="item.id" :item="item" :index="index" /></div></section><div v-if="!filtered.length" class="rounded-2xl border border-dashed border-brand-200 bg-white p-8 text-center text-sm text-slate-500">По выбранным фильтрам рекомендаций нет.</div></main>
            <aside class="min-w-0 rounded-2xl border border-brand-100 bg-white p-3 shadow-soft xl:sticky xl:top-24 xl:h-fit"><h2 class="flex items-center gap-2 px-2 text-sm font-bold text-slate-900"><History :size="17" />История анализов</h2><div class="mt-3 max-h-80 space-y-1 overflow-y-auto"><div v-for="job in jobs" :key="job.id" role="button" tabindex="0" class="group flex w-full min-w-0 cursor-pointer items-center gap-2 rounded-xl p-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500" :class="selected?.id === job.id ? 'bg-brand-50' : 'hover:bg-slate-50'" @click="selectedId = job.id" @keydown.enter="selectedId = job.id" @keydown.space.prevent="selectedId = job.id"><Clock3 :size="15" class="shrink-0 text-brand-500" /><span class="min-w-0 flex-1"><strong class="block truncate text-xs text-slate-800">{{ analysisTypeLabel[job.recommendation_type] || 'Анализ сайта' }}</strong><small class="block truncate text-[11px] text-slate-500">{{ formatDate(job.created_at) }}</small></span><button type="button" class="rounded-lg p-1 text-slate-400 opacity-100 hover:bg-red-50 hover:text-red-600 xl:opacity-0 xl:group-hover:opacity-100" aria-label="Удалить анализ" title="Удалить" @click.stop="remove(job)"><Trash2 :size="14" /></button></div></div></aside>
          </div>
        </template>
      </template>
    </template>
  </div>
</template>

<style scoped>
.ai-card { animation: ai-card-in .38s ease both; animation-delay: var(--delay); }
@keyframes ai-card-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { .ai-card { animation: none; transition: none; } :deep(.animate-spin), :deep(.animate-pulse) { animation: none; } }
@media (max-width: 390px) { .ai-page { margin-inline: -0.15rem; } }
</style>
