<script setup>
import MetricStatusBadge from './MetricStatusBadge.vue'

defineProps({
  item: {
    type: Object,
    required: true,
  },
})

function importanceStatus(value) {
  if (value === 'high') return 'Критично'
  if (value === 'medium') return 'Требует внимания'
  return 'Нормально'
}
</script>

<template>
  <article class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-start justify-between gap-3">
      <h3 class="text-base font-semibold leading-6 text-slate-950">{{ item.title }}</h3>
      <MetricStatusBadge :status="importanceStatus(item.importance)" />
    </div>
    <p v-if="item.description" class="mt-3 text-sm leading-6 text-slate-700">{{ item.description }}</p>
    <p v-if="item.page" class="mt-2 text-sm font-medium text-cyan-700">{{ item.page }}</p>
    <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.reason }}</p>
    <div v-if="item.what_to_do" class="mt-4 rounded-lg border border-cyan-100 bg-cyan-50 p-3">
      <p class="text-xs font-semibold uppercase text-cyan-700">Что сделать</p>
      <p class="mt-1 text-sm leading-6 text-slate-700">{{ item.what_to_do }}</p>
    </div>
    <p v-if="(item.related_sections || []).length" class="mt-3 text-xs leading-5 text-slate-500">
      Посмотреть: {{ item.related_sections.join(', ') }}
    </p>
  </article>
</template>
