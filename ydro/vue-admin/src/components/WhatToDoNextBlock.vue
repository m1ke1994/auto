<script setup>
defineProps({
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
        <h2>Что сделать дальше</h2>
        <p>Практические действия, которые могут увеличить количество заявок.</p>
      </div>
    </div>
    <ol v-if="items.length" class="grid gap-3 lg:grid-cols-2">
      <li v-for="(item, index) in items" :key="item" class="flex gap-3 rounded-2xl border border-brand-100 bg-white/76 p-4 text-sm leading-6 text-slate-700">
        <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">{{ index + 1 }}</span>
        <span>{{ item }}</span>
      </li>
    </ol>
    <p v-else class="text-sm leading-6 text-slate-500">Дождитесь новых посещений сайта и вернитесь к разделу позже.</p>
  </section>
</template>
