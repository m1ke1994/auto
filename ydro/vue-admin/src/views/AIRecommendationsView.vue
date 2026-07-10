<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, RefreshCw, Sparkles, Trash2 } from '@lucide/vue'
import { createAIRecommendationJob, deleteAIRecommendationJob, listAIRecommendationJobs, retryAIRecommendationJob } from '../api/aiRecommendations'
import { useSiteStore } from '../stores/site'

const route = useRoute(), router = useRouter(), siteStore = useSiteStore()
const jobs = ref([]), loading = ref(true), creating = ref(false), error = ref('')
const priority = ref('all'), type = ref('combined')
const today = new Date(), from = new Date(Date.now() - 30 * 86400000)
const periodFrom = ref(from.toISOString().slice(0, 10)), periodTo = ref(today.toISOString().slice(0, 10))
const selectedId = ref(null)
let timer
const selected = computed(() => jobs.value.find((job) => job.id === selectedId.value) || jobs.value[0] || null)
const resultIsBusinessFriendly = computed(() => {
  const items = selected.value?.result?.recommendations
  return Array.isArray(items) && items.every((item) => item.why_important && Array.isArray(item.actions) && item.benefit)
})
const recommendations = computed(() => (selected.value?.result?.recommendations || []).filter((item) => priority.value === 'all' || item.priority === priority.value))
const active = computed(() => jobs.value.some((job) => ['queued', 'processing'].includes(job.status)))

const priorityClass = { very_important: 'bg-red-100 text-red-800', recommended: 'bg-orange-100 text-orange-800', later: 'bg-emerald-100 text-emerald-800' }
const priorityLabel = { very_important: '🔴 Очень важно', recommended: '🟠 Желательно', later: '🟢 Можно улучшить позже' }
const statusLabel = { queued: 'В очереди', processing: 'Формируется', completed: 'Готово', failed: 'Ошибка', cancelled: 'Отменено' }
const analysisTypeLabel = { combined: 'Полный анализ', seo: 'Заметность в поиске', conversion: 'Обращения клиентов' }

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
        <div><p class="text-sm font-semibold text-brand-600">Помощник для бизнеса</p><h1 class="mt-1 text-2xl font-bold text-slate-900">AI-рекомендации</h1><p class="mt-2 text-sm text-slate-500">Мы изучим работу сайта и подскажем, как привлечь больше клиентов. Результат появится автоматически.</p></div>
        <Sparkles class="text-brand-600" :size="34" />
      </div>
      <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label class="text-xs text-slate-500">Сайт<select class="input mt-1 w-full" :value="route.params.siteId" @change="selectSite"><option v-for="site in siteStore.sites" :key="site.id" :value="site.id">{{ site.name }}</option></select></label>
        <label class="text-xs text-slate-500">С даты<input v-model="periodFrom" type="date" class="input mt-1 w-full" /></label>
        <label class="text-xs text-slate-500">По дату<input v-model="periodTo" type="date" class="input mt-1 w-full" /></label>
        <label class="text-xs text-slate-500">Что проверить<select v-model="type" class="input mt-1 w-full"><option value="combined">Весь сайт</option><option value="seo">Заметность в поиске</option><option value="conversion">Обращения клиентов</option></select></label>
        <button class="btn-primary self-end" :disabled="creating" @click="createJob"><RefreshCw :size="17" :class="creating && 'animate-spin'" /> {{ creating ? 'Запускаем…' : 'Сформировать' }}</button>
      </div>
    </header>

    <div v-if="error" class="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><AlertTriangle class="mr-2 inline" :size="18" />{{ error }}</div>
    <div v-if="loading" class="rounded-3xl border border-brand-100 bg-white p-12 text-center text-slate-500">Загрузка рекомендаций…</div>
    <div v-else-if="!jobs.length" class="rounded-3xl border border-dashed border-brand-200 bg-white p-12 text-center"><Sparkles class="mx-auto text-brand-400" :size="40" /><h2 class="mt-3 font-semibold text-slate-800">Рекомендаций пока нет</h2><p class="mt-2 text-sm text-slate-500">Выберите период и запустите первый анализ.</p></div>
    <template v-else>
      <section class="grid gap-4 lg:grid-cols-[280px_1fr]">
        <aside class="space-y-2 rounded-3xl border border-brand-100 bg-white p-3 shadow-soft">
          <button v-for="job in jobs" :key="job.id" class="w-full rounded-2xl p-3 text-left text-sm" :class="selected?.id === job.id ? 'bg-brand-50 ring-1 ring-brand-200' : 'hover:bg-slate-50'" @click="selectedId = job.id"><span class="font-semibold text-slate-800">{{ statusLabel[job.status] }}</span><span class="mt-1 block text-xs text-slate-500">{{ new Date(job.created_at).toLocaleString('ru-RU') }} · {{ analysisTypeLabel[job.recommendation_type] }}</span></button>
        </aside>
        <main class="space-y-4">
          <div class="rounded-3xl border border-brand-100 bg-white p-6 shadow-soft">
            <div class="flex flex-wrap justify-between gap-3"><div><span class="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">{{ statusLabel[selected.status] }}</span><p class="mt-3 text-sm text-slate-500">Создано {{ new Date(selected.created_at).toLocaleString('ru-RU') }}</p></div><div class="flex gap-2"><button v-if="selected.status === 'failed'" class="btn-secondary" @click="retry(selected)">Повторить</button><button class="icon-button" title="Удалить" @click="remove(selected)"><Trash2 :size="18" /></button></div></div>
            <div v-if="['queued','processing'].includes(selected.status)" class="mt-6 rounded-2xl bg-brand-50 p-5 text-brand-800"><RefreshCw class="mr-2 inline animate-spin" :size="18" />Идёт анализ. Страницу можно закрыть — задача выполняется в фоне.</div>
            <div v-else-if="selected.status === 'failed'" class="mt-6 rounded-2xl bg-red-50 p-5 text-red-800">{{ selected.error_message || 'Не удалось сформировать рекомендации.' }}</div>
            <template v-else-if="selected.result && resultIsBusinessFriendly"><div class="mt-6 rounded-2xl bg-brand-50 p-5"><h2 class="font-semibold text-brand-950">Главное о вашем сайте</h2><p class="mt-2 whitespace-pre-line text-sm leading-6 text-brand-900">{{ selected.result.summary }}</p></div></template>
            <div v-else-if="selected.result" class="mt-6 rounded-2xl bg-brand-50 p-5 text-sm leading-6 text-brand-900">Эти рекомендации были созданы в старом формате. Запустите новый анализ — результат будет короче и понятнее для владельца бизнеса.</div>
          </div>
          <template v-if="selected.result && resultIsBusinessFriendly">
            <div class="flex flex-wrap gap-3"><select v-model="priority" class="input"><option value="all">Все рекомендации</option><option value="very_important">🔴 Очень важно</option><option value="recommended">🟠 Желательно</option><option value="later">🟢 Можно улучшить позже</option></select></div>
            <article v-for="item in recommendations" :key="item.id" class="rounded-3xl border border-brand-100 bg-white p-6 shadow-soft">
              <span class="inline-flex rounded-full px-3 py-1.5 text-xs font-bold" :class="priorityClass[item.priority]">{{ priorityLabel[item.priority] }}</span>
              <h3 class="mt-4 text-xl font-semibold text-slate-900">{{ item.title }}</h3>
              <section class="mt-5"><h4 class="text-sm font-semibold text-slate-900">Почему это важно</h4><p class="mt-2 text-sm leading-6 text-slate-600">{{ item.why_important }}</p></section>
              <section class="mt-5"><h4 class="text-sm font-semibold text-slate-900">Что мы рекомендуем</h4><ul class="mt-2 space-y-2 text-sm text-slate-600"><li v-for="action in item.actions" :key="action" class="flex gap-2"><span class="text-brand-500">•</span><span>{{ action }}</span></li></ul></section>
              <section class="mt-5 rounded-2xl bg-brand-50 p-4"><h4 class="text-sm font-semibold text-brand-900">Что это даст вашему бизнесу</h4><p class="mt-2 text-sm leading-6 text-brand-800">{{ item.benefit }}</p></section>
            </article>
          </template>
        </main>
      </section>
    </template>
  </div>
</template>
