<script setup>
defineProps({
  title: {
    type: String,
    default: 'Что это означает',
  },
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="surface">
    <div class="section-heading">
      <div>
        <h2>{{ title }}</h2>
        <p>Короткая интерпретация без сложных терминов.</p>
      </div>
    </div>
    <div v-if="items.length" class="grid gap-3 lg:grid-cols-3">
      <article v-for="item in items" :key="item" class="rounded-2xl border border-brand-100 bg-[#F5F7FD] p-4 text-sm leading-6 text-slate-700">
        {{ item }}
      </article>
    </div>
    <p v-else class="text-sm leading-6 text-slate-500">Пока данных недостаточно для точной оценки.</p>
  </section>
</template>
