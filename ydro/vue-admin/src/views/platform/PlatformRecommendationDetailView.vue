<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { actOnPlatformRecommendation, getPlatformRecommendation } from '../../api/platform'

const route = useRoute()
const router = useRouter()
const job = ref(null)
const error = ref('')
const busy = ref(false)

async function load() {
  try {
    job.value = (await getPlatformRecommendation(route.params.jobId)).data
    error.value = ''
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Нет разрешения на технические данные.'
  }
}

async function act(action) {
  busy.value = true
  try {
    await actOnPlatformRecommendation(route.params.jobId, action)
    if (action === 'hide') router.push('/platform/recommendations')
    else await load()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Действие не выполнено.'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-4">
    <div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div>
    <template v-if="job">
      <header class="rounded-3xl bg-slate-950 p-6 text-white">
        <p class="text-xs font-bold uppercase tracking-wider text-violet-300">Технический контроль качества · только platform_owner</p>
        <h2 class="mt-2 text-xl font-bold">{{ job.site.name }}</h2>
        <p class="mt-1 text-sm text-slate-300">{{ job.site.owner }} · {{ job.status }} · {{ job.period.date_from }} — {{ job.period.date_to }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-900" :disabled="busy" @click="act('reviewed')">Отметить просмотренной</button>
          <button class="rounded-xl bg-amber-400 px-3 py-2 text-xs font-semibold text-slate-900" :disabled="busy" @click="act('retry')">Повторить</button>
          <button class="rounded-xl bg-red-500 px-3 py-2 text-xs font-semibold" :disabled="busy" @click="act('hide')">Скрыть</button>
        </div>
      </header>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="item in [
          ['Версия промпта', job.prompt_version], ['Модель', job.model || 'Не сохранена'],
          ['Входные токены', job.input_tokens ?? 'Не сохранены'], ['Выходные токены', job.output_tokens ?? 'Не сохранены'],
          ['Есть аналитика', job.has_analytics ? 'Да' : 'Нет'], ['Есть SEO', job.has_seo ? 'Да' : 'Нет'],
          ['Начало', job.started_at || '—'], ['Завершение', job.completed_at || '—'],
          ['Попытки опроса', job.poll_attempts], ['Просмотрено', job.reviewed_at || 'Нет'],
          ['Скрыто', job.hidden_at || 'Нет'], ['Ошибка', job.error || 'Нет'],
        ]" :key="item[0]" class="rounded-2xl bg-white p-4 shadow-soft">
          <p class="text-xs text-slate-500">{{ item[0] }}</p><strong class="mt-2 block break-words text-sm">{{ item[1] }}</strong>
        </article>
      </div>
      <details class="rounded-3xl bg-white p-5 shadow-soft"><summary class="cursor-pointer font-semibold">Входные данные генерации</summary><pre class="mt-4 max-h-[32rem] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-emerald-300">{{ JSON.stringify(job.input_snapshot, null, 2) }}</pre></details>
      <details class="rounded-3xl bg-white p-5 shadow-soft"><summary class="cursor-pointer font-semibold">Технический результат AI</summary><pre class="mt-4 max-h-[32rem] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-sky-300">{{ JSON.stringify(job.technical_result, null, 2) }}</pre></details>
    </template>
  </section>
</template>
