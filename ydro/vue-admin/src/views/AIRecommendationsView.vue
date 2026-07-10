<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, RefreshCw, Sparkles, Trash2 } from '@lucide/vue'
import { createAIRecommendationJob, deleteAIRecommendationJob, listAIRecommendationJobs, retryAIRecommendationJob } from '../api/aiRecommendations'
import { useSiteStore } from '../stores/site'

const route = useRoute(), router = useRouter(), siteStore = useSiteStore()
const jobs = ref([]), loading = ref(true), creating = ref(false), error = ref('')
const priority = ref('all'), category = ref('all'), type = ref('combined')
const today = new Date(), from = new Date(Date.now() - 30 * 86400000)
const periodFrom = ref(from.toISOString().slice(0, 10)), periodTo = ref(today.toISOString().slice(0, 10))
const selectedId = ref(null)
let timer
const selected = computed(() => jobs.value.find((job) => job.id === selectedId.value) || jobs.value[0] || null)
const recommendations = computed(() => (selected.value?.result?.recommendations || []).filter((item) => (priority.value === 'all' || item.priority === priority.value) && (category.value === 'all' || item.category === category.value)))
const categories = computed(() => [...new Set((selected.value?.result?.recommendations || []).map((item) => item.category))])
const quickWins = computed(() => (selected.value?.result?.recommendations || []).filter((item) => item.quick_win))
const active = computed(() => jobs.value.some((job) => ['queued', 'processing'].includes(job.status)))

const priorityClass = { critical: 'bg-red-100 text-red-800', high: 'bg-orange-100 text-orange-800', medium: 'bg-amber-100 text-amber-800', low: 'bg-emerald-100 text-emerald-800' }
const statusLabel = { queued: 'В очереди', processing: 'Формируется', completed: 'Готово', failed: 'Ошибка', cancelled: 'Отменено' }

async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const { data } = await listAIRecommendationJobs()
    jobs.value = data.filter((job) => Number(job.site) === Number(route.params.siteId))
    if (!selectedId.value && jobs.value.length) selectedId.value = jobs.value[0].id
    error.value = ''
  } catch (e) { error.value = e.response?.data?.detail || 'Не удалось загрузить AI-рекомендации.' }
  finally { loading.value = false }
}
async function createJob() {
  creating.value = true; error.value = ''
  try {
    const { data } = await createAIRecommendationJob({ site_id: Number(route.params.siteId), recommendation_type: type.value, period_from: periodFrom.value, period_to: periodTo.value })
    jobs.value.unshift(data); selectedId.value = data.id
  } catch (e) { error.value = e.response?.data?.detail || 'Не удалось запустить анализ.' }
  finally { creating.value = false }
}
async function retry(job) { await retryAIRecommendationJob(job.id); await load(true) }
async function remove(job) { await deleteAIRecommendationJob(job.id); selectedId.value = null; await load(true) }
function selectSite(event) { router.push(`/sites/${event.target.value}/ai-recommendations`) }
watch(() => route.params.siteId, () => { selectedId.value = null; load() })
onMounted(async () => { if (!siteStore.sites.length) await siteStore.fetchSites(); await siteStore.fetchSite(route.params.siteId); await load(); timer = setInterval(() => { if (active.value) load(true) }, 10000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="space-y-6">
    <header class="rounded-3xl border border-brand-100 bg-white p-6 shadow-soft">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div><p class="text-sm font-semibold text-brand-600">Бизнес-аналитика</p><h1 class="mt-1 text-2xl font-bold text-slate-900">AI-рекомендации</h1><p class="mt-2 text-sm text-slate-500">Обезличенные данные анализируются в защищённом сервисе. Результат появится автоматически.</p></div>
        <Sparkles class="text-brand-600" :size="34" />
      </div>
      <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label class="text-xs text-slate-500">Сайт<select class="input mt-1 w-full" :value="route.params.siteId" @change="selectSite"><option v-for="site in siteStore.sites" :key="site.id" :value="site.id">{{ site.name }}</option></select></label>
        <label class="text-xs text-slate-500">С даты<input v-model="periodFrom" type="date" class="input mt-1 w-full" /></label>
        <label class="text-xs text-slate-500">По дату<input v-model="periodTo" type="date" class="input mt-1 w-full" /></label>
        <label class="text-xs text-slate-500">Тип анализа<select v-model="type" class="input mt-1 w-full"><option value="combined">SEO + конверсия</option><option value="seo">SEO</option><option value="conversion">Конверсия</option></select></label>
        <button class="btn-primary self-end" :disabled="creating" @click="createJob"><RefreshCw :size="17" :class="creating && 'animate-spin'" /> {{ creating ? 'Запускаем…' : 'Сформировать' }}</button>
      </div>
    </header>

    <div v-if="error" class="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><AlertTriangle class="mr-2 inline" :size="18" />{{ error }}</div>
    <div v-if="loading" class="rounded-3xl border border-brand-100 bg-white p-12 text-center text-slate-500">Загрузка рекомендаций…</div>
    <div v-else-if="!jobs.length" class="rounded-3xl border border-dashed border-brand-200 bg-white p-12 text-center"><Sparkles class="mx-auto text-brand-400" :size="40" /><h2 class="mt-3 font-semibold text-slate-800">Рекомендаций пока нет</h2><p class="mt-2 text-sm text-slate-500">Выберите период и запустите первый анализ.</p></div>
    <template v-else>
      <section class="grid gap-4 lg:grid-cols-[280px_1fr]">
        <aside class="space-y-2 rounded-3xl border border-brand-100 bg-white p-3 shadow-soft">
          <button v-for="job in jobs" :key="job.id" class="w-full rounded-2xl p-3 text-left text-sm" :class="selected?.id === job.id ? 'bg-brand-50 ring-1 ring-brand-200' : 'hover:bg-slate-50'" @click="selectedId = job.id"><span class="font-semibold text-slate-800">{{ statusLabel[job.status] }}</span><span class="mt-1 block text-xs text-slate-500">{{ new Date(job.created_at).toLocaleString('ru-RU') }} · {{ job.recommendation_type }}</span></button>
        </aside>
        <main class="space-y-4">
          <div class="rounded-3xl border border-brand-100 bg-white p-6 shadow-soft">
            <div class="flex flex-wrap justify-between gap-3"><div><span class="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">{{ statusLabel[selected.status] }}</span><p class="mt-3 text-sm text-slate-500">Создано {{ new Date(selected.created_at).toLocaleString('ru-RU') }}</p></div><div class="flex gap-2"><button v-if="selected.status === 'failed'" class="btn-secondary" @click="retry(selected)">Повторить</button><button class="icon-button" title="Удалить" @click="remove(selected)"><Trash2 :size="18" /></button></div></div>
            <div v-if="['queued','processing'].includes(selected.status)" class="mt-6 rounded-2xl bg-brand-50 p-5 text-brand-800"><RefreshCw class="mr-2 inline animate-spin" :size="18" />Идёт анализ. Страницу можно закрыть — задача выполняется в фоне.</div>
            <div v-else-if="selected.status === 'failed'" class="mt-6 rounded-2xl bg-red-50 p-5 text-red-800">{{ selected.error_message || 'Не удалось сформировать рекомендации.' }}</div>
            <template v-else-if="selected.result"><div class="mt-6 grid gap-4 md:grid-cols-[120px_1fr]"><div class="grid h-28 place-items-center rounded-3xl bg-gradient-to-br from-brand-600 to-violet-500 text-4xl font-black text-white">{{ selected.result.score }}</div><div><h2 class="font-semibold text-slate-900">Общее резюме</h2><p class="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{{ selected.result.summary }}</p></div></div></template>
          </div>
          <template v-if="selected.result">
            <div v-if="quickWins.length" class="rounded-3xl border border-emerald-200 bg-emerald-50 p-5"><h2 class="font-semibold text-emerald-900">Быстрые улучшения</h2><ul class="mt-2 space-y-1 text-sm text-emerald-800"><li v-for="item in quickWins" :key="item.id">• {{ item.title }}</li></ul></div>
            <div class="flex flex-wrap gap-3"><select v-model="priority" class="input"><option value="all">Все приоритеты</option><option v-for="p in ['critical','high','medium','low']" :key="p" :value="p">{{ p }}</option></select><select v-model="category" class="input"><option value="all">Все категории</option><option v-for="item in categories" :key="item" :value="item">{{ item }}</option></select></div>
            <article v-for="item in recommendations" :key="item.id" class="rounded-3xl border border-brand-100 bg-white p-6 shadow-soft"><div class="flex flex-wrap gap-2"><span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="priorityClass[item.priority]">{{ item.priority }}</span><span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{{ item.category }}</span><span v-if="item.quick_win" class="rounded-full bg-emerald-100 px-2.5 py-1 text-xs text-emerald-800">quick win</span></div><h3 class="mt-4 text-lg font-semibold text-slate-900">{{ item.title }}</h3><p class="mt-2 text-sm text-slate-600">{{ item.problem }}</p><h4 class="mt-4 text-sm font-semibold">Основания</h4><ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600"><li v-for="evidence in item.evidence" :key="evidence">{{ evidence }}</li></ul><h4 class="mt-4 text-sm font-semibold">Что сделать</h4><p class="mt-2 whitespace-pre-line text-sm text-slate-600">{{ item.action }}</p><div class="mt-4 grid gap-3 rounded-2xl bg-slate-50 p-4 text-sm md:grid-cols-3"><span><b>Эффект:</b> {{ item.expected_impact }}</span><span><b>Сложность:</b> {{ item.effort }}</span><span><b>Уверенность:</b> {{ Math.round(item.confidence * 100) }}%</span></div><div v-if="item.limitations?.length" class="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><b>Ограничения и риски:</b><ul class="mt-1 list-disc pl-5"><li v-for="limit in item.limitations" :key="limit">{{ limit }}</li></ul></div></article>
          </template>
        </main>
      </section>
    </template>
  </div>
</template>
