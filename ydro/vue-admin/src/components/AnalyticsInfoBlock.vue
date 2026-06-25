<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  usage: {
    type: String,
    default: '',
  },
  insight: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="surface">
    <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.7fr)]">
      <div>
        <p class="eyebrow">Что показывает раздел</p>
        <h2 class="mt-1 text-xl font-semibold text-[#17223B]">{{ title }}</h2>
        <p v-if="description" class="mt-2 text-sm leading-6 text-slate-600">{{ description }}</p>
        <p v-if="usage" class="mt-3 rounded-2xl border border-brand-100 bg-[#F5F7FD] p-3 text-sm leading-6 text-slate-600">{{ usage }}</p>
      </div>
      <div class="rounded-2xl border border-brand-100 bg-brand-50 p-4 shadow-sm">
        <p class="text-xs font-semibold uppercase text-brand-700">Что происходит сейчас</p>
        <p class="mt-2 text-sm leading-6 text-slate-800">{{ insight || 'Данных пока недостаточно для точной оценки.' }}</p>
      </div>
    </div>
  </section>
</template>
