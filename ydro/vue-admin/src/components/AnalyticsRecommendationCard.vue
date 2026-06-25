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
  <article class="rounded-2xl border border-brand-100 bg-white/92 p-4 shadow-soft transition hover:-translate-y-0.5 hover:shadow-[0_18px_48px_rgba(32,40,70,0.12)]">
    <div class="flex items-start justify-between gap-3">
      <h3 class="text-base font-semibold leading-6 text-[#17223B]">{{ item.title }}</h3>
      <MetricStatusBadge :status="importanceStatus(item.importance)" />
    </div>
    <p v-if="item.description" class="mt-3 text-sm leading-6 text-slate-700">{{ item.description }}</p>
    <p v-if="item.page" class="mt-2 text-sm font-medium text-brand-700">{{ item.page }}</p>
    <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.reason }}</p>
    <div v-if="item.what_to_do" class="mt-4 rounded-2xl border border-brand-100 bg-brand-50 p-3">
      <p class="text-xs font-semibold uppercase text-brand-700">Что сделать</p>
      <p class="mt-1 text-sm leading-6 text-slate-700">{{ item.what_to_do }}</p>
    </div>
    <p v-if="(item.related_sections || []).length" class="mt-3 text-xs leading-5 text-slate-500">
      Посмотреть: {{ item.related_sections.join(', ') }}
    </p>
  </article>
</template>
