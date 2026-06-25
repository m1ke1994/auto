<script setup>
defineProps({
  title: {
    type: String,
    default: 'Итоги за период',
  },
  text: {
    type: String,
    default: '',
  },
  attentionItems: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="surface border-cyan-200 bg-cyan-50/50">
    <div class="grid gap-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]">
      <div>
        <p class="eyebrow">{{ title }}</p>
        <p class="mt-3 text-lg leading-8 text-slate-900">{{ text }}</p>
      </div>
      <div class="rounded-lg border border-cyan-200 bg-white p-4">
        <h2 class="text-base font-semibold text-slate-950">На что обратить внимание</h2>
        <ul v-if="attentionItems.length" class="mt-3 space-y-2 text-sm leading-6 text-slate-700">
          <li v-for="item in attentionItems" :key="item" class="flex gap-2">
            <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-600" />
            <span>{{ item }}</span>
          </li>
        </ul>
        <p v-else class="mt-3 text-sm leading-6 text-slate-500">Пока нет явных проблем. Продолжайте смотреть заявки, тепловую карту и скорость страниц.</p>
      </div>
    </div>
  </section>
</template>
