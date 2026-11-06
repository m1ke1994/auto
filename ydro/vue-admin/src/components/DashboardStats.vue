<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="item in items"
      :key="item.label"
      class="rounded-2xl border border-brand-100 bg-white/92 p-4 shadow-soft sm:p-5"
    >
      <p class="text-xs font-medium text-slate-500">{{ item.label }}</p>
      <p class="mt-2 text-2xl font-bold text-[#17223B] sm:text-3xl">{{ item.value }}</p>
      <p v-if="item.sub" class="mt-1 text-xs leading-5 text-slate-500">{{ item.sub }}</p>
    </article>
  </div>
</template>
