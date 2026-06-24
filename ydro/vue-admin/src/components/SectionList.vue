<script setup>
import { computed, ref } from 'vue'
import { ChevronDown, ChevronRight, ChevronUp, Image, LayoutTemplate, MessageSquareText, Pencil, Rows3 } from '@lucide/vue'
import { getSectionLabel } from '../utils/sectionLabels'
import { countRepeaterItems, elementCountLabel, sectionTypeLabel } from '../utils/formPresentation'

const icons = { hero: Image, about: MessageSquareText, services: Rows3, reviews: MessageSquareText, gallery: Image }
function sectionIcon(section) { return icons[section.section_type || section.key] || LayoutTemplate }

const props = defineProps({ siteId: { type: Number, required: true }, sections: { type: Array, default: () => [] } })
const expandedSectionIds = ref(new Set())
const sortedSections = computed(() => [...props.sections].sort((a, b) => Number(a.order || 0) - Number(b.order || 0)))

function sectionMeta(section) {
  const items = countRepeaterItems(section?.content)
  if (items > 0) return elementCountLabel(items)
  return 'без элементов'
}

function isExpanded(sectionId) {
  return expandedSectionIds.value.has(sectionId)
}

function toggleSection(sectionId) {
  const next = new Set(expandedSectionIds.value)
  if (next.has(sectionId)) next.delete(sectionId)
  else next.add(sectionId)
  expandedSectionIds.value = next
}
</script>

<template>
  <div v-if="sections.length" class="grid gap-3">
    <article
      v-for="section in sortedSections"
      :key="section.id"
      class="surface overflow-hidden p-0"
      :class="section.is_active ? 'border-slate-200' : 'border-slate-200 bg-slate-50'"
    >
      <div class="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        <div class="flex min-w-0 items-start gap-3">
          <span class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
            <component :is="sectionIcon(section)" :size="21" />
          </span>
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <p class="truncate font-semibold text-slate-950">{{ getSectionLabel(section) }}</p>
              <span class="status-badge" :class="section.is_active ? 'status-success' : 'status-neutral'">
                {{ section.is_active ? 'Активна' : 'Неактивна' }}
              </span>
              <span class="status-badge status-neutral">{{ sectionMeta(section) }}</span>
            </div>
            <p class="mt-1 break-words text-sm text-slate-500">
              {{ sectionTypeLabel(section) }} · slug {{ section.key || '—' }} · id {{ section.id }} · порядок {{ section.order ?? '—' }}
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button type="button" class="action-button-secondary" @click="toggleSection(section.id)">
            <component :is="isExpanded(section.id) ? ChevronUp : ChevronDown" :size="16" />
            {{ isExpanded(section.id) ? 'Свернуть' : 'Детали' }}
          </button>
          <RouterLink :to="`/sites/${siteId}/sections/${section.id}`" class="action-button-primary flex-1 sm:flex-none">
            <Pencil :size="16" /> Изменить <ChevronRight :size="16" />
          </RouterLink>
        </div>
      </div>

      <div v-if="isExpanded(section.id)" class="grid gap-3 border-t border-slate-100 bg-slate-50/80 p-4 text-sm sm:grid-cols-4 sm:p-5">
        <div>
          <p class="text-xs font-semibold uppercase text-slate-400">Название</p>
          <p class="mt-1 font-medium text-slate-800">{{ section.title || getSectionLabel(section) }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase text-slate-400">Тип</p>
          <p class="mt-1 font-medium text-slate-800">{{ section.section_type || 'не указан' }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase text-slate-400">Компонент</p>
          <p class="mt-1 font-medium text-slate-800">{{ section.component_key || 'не указан' }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase text-slate-400">Статус</p>
          <p class="mt-1 font-medium text-slate-800">
            {{ section.is_active ? 'Показывается на публичном сайте' : 'Сейчас скрыт от посетителей' }}
          </p>
        </div>
      </div>
    </article>
  </div>
</template>
