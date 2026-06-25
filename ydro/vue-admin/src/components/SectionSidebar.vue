<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Circle, LayoutTemplate } from '@lucide/vue'

import { getSectionLabel } from '../utils/sectionLabels'
import { countRepeaterItems, sectionTypeLabel } from '../utils/formPresentation'

const props = defineProps({
  siteId: {
    type: Number,
    required: true,
  },
  sections: {
    type: Array,
    default: () => [],
  },
})

const route = useRoute()
const currentSectionId = computed(() => Number(route.params.sectionId))
const sortedSections = computed(() => [...props.sections].sort((a, b) => Number(a.order || 0) - Number(b.order || 0)))

function itemCount(section) {
  return countRepeaterItems(section?.content)
}
</script>

<template>
  <aside class="surface h-fit p-3 lg:sticky lg:top-24">
    <p class="px-3 pb-2 text-xs font-semibold uppercase text-slate-500">Разделы сайта</p>
    <nav class="space-y-1">
      <RouterLink
        v-for="item in sortedSections"
        :key="item.id"
        :to="`/sites/${siteId}/sections/${item.id}`"
        class="flex min-w-0 items-start gap-2 rounded-2xl px-3 py-2.5 text-sm transition duration-300"
        :class="currentSectionId === item.id ? 'bg-brand-50 text-brand-950 ring-1 ring-brand-100' : 'text-slate-700 hover:bg-brand-50/70 hover:text-brand-800'"
      >
        <LayoutTemplate :size="17" class="mt-0.5 shrink-0" />
        <span class="min-w-0 flex-1">
          <span class="block truncate font-semibold">{{ getSectionLabel(item) }}</span>
          <span class="mt-0.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
            <span class="truncate">{{ sectionTypeLabel(item) }}</span>
            <span v-if="itemCount(item)">{{ itemCount(item) }} эл.</span>
            <span class="inline-flex items-center gap-1">
              <Circle :size="7" :fill="item.is_active ? 'currentColor' : 'none'" />
              {{ item.is_active ? 'активна' : 'скрыта' }}
            </span>
          </span>
        </span>
      </RouterLink>
    </nav>
  </aside>
</template>
