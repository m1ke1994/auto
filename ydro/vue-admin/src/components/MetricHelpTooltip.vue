<script setup>
import { CircleHelp } from '@lucide/vue'

defineProps({
  text: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <span v-if="text" class="group relative inline-flex">
    <CircleHelp :size="15" class="text-slate-400" />
    <span
      class="pointer-events-none absolute left-1/2 top-6 z-20 hidden w-64 -translate-x-1/2 rounded-lg border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-600 shadow-lg group-hover:block"
      role="tooltip"
    >
      {{ text }}
    </span>
  </span>
</template>
