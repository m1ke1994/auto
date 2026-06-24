<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ExternalLink, RotateCcw, Save } from '@lucide/vue'

import DynamicForm from '../components/DynamicForm.vue'
import SectionSidebar from '../components/SectionSidebar.vue'
import { BACKEND_URL, toPublicUrl } from '../config/env'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'
import { countRepeaterItems, elementCountLabel, sectionTypeLabel } from '../utils/formPresentation'
import { getSectionLabel } from '../utils/sectionLabels'

const route = useRoute()
const sectionsStore = useSectionsStore()
const siteStore = useSiteStore()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const content = ref({})
const originalContent = ref({})
const siteId = computed(() => Number(route.params.siteId))
const sectionId = computed(() => Number(route.params.sectionId))
const section = computed(() => sectionsStore.currentSection)
const sectionTitle = computed(() => getSectionLabel(section.value))
const schema = computed(() => section.value?.schema || section.value?.schema_template?.schema || { fields: [] })
const hasSchema = computed(() => Array.isArray(schema.value?.fields) && schema.value.fields.length > 0)
const hasUnsavedChanges = computed(() => JSON.stringify(content.value || {}) !== JSON.stringify(originalContent.value || {}))
const sectionItemsCount = computed(() => countRepeaterItems(content.value))
const sectionMeta = computed(() => {
  if (!section.value) return []
  return [
    sectionTypeLabel(section.value),
    `slug ${section.value.key || '—'}`,
    `id ${section.value.id || '—'}`,
    `порядок ${section.value.order ?? '—'}`,
  ]
})
const uploadContext = computed(() => ({
  siteId: siteId.value,
  siteSlug: siteStore.currentSite?.slug || '',
  sectionKey: section.value?.key || '',
  apiBaseUrl: BACKEND_URL,
}))
const previewUrl = computed(() => {
  const domain = String(siteStore.currentSite?.domain || '').trim().replace(/\/+$/, '')
  return toPublicUrl(domain)
})

function clone(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

async function load() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    if (!sectionsStore.sections.length) await sectionsStore.fetchSections(siteId.value)
    const data = await sectionsStore.fetchSection(siteId.value, sectionId.value)
    content.value = clone(data?.content)
    originalContent.value = clone(data?.content)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить раздел.'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!hasSchema.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await sectionsStore.patchSection(siteId.value, sectionId.value, { content: content.value })
    originalContent.value = clone(content.value)
    success.value = 'Изменения сохранены'
  } catch (e) {
    const details = e?.response?.data?.content
    error.value = Array.isArray(details)
      ? details.join(' ')
      : 'Не удалось сохранить изменения. Проверьте поля и попробуйте снова.'
  } finally {
    saving.value = false
  }
}

function cancelChanges() {
  content.value = clone(originalContent.value)
  error.value = ''
  success.value = ''
}

function openPreview() {
  if (previewUrl.value) {
    window.open(previewUrl.value, '_blank', 'noopener,noreferrer')
  }
}

onMounted(load)
watch(sectionId, load)
watch(content, () => {
  if (hasUnsavedChanges.value) {
    success.value = ''
  }
}, { deep: true })
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="inline-flex items-center gap-2 text-sm font-medium text-cyan-800">
          <ArrowLeft :size="16" />К разделам
        </RouterLink>
        <h1>{{ sectionTitle }}</h1>
        <p>Измените нужные тексты, изображения и повторяемые карточки. Сохранение применяется ко всему текущему разделу.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-if="previewUrl" type="button" class="action-button-secondary" @click="openPreview">
          <ExternalLink :size="17" />Предпросмотр
        </button>
      </div>
    </header>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <p v-if="success" class="notice-success" role="status">{{ success }}</p>

    <section v-if="loading" class="empty-state">
      <span class="loading-dot" />
      <p>Загружаем содержимое...</p>
    </section>
    <section v-else-if="!hasSchema" class="empty-state">
      <h2>Этот раздел пока нельзя изменить здесь</h2>
      <p>Обратитесь к администратору, чтобы настроить удобную форму редактирования.</p>
    </section>
    <div v-else class="grid items-start gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
      <SectionSidebar :site-id="siteId" :sections="sectionsStore.sections" />
      <section class="surface overflow-visible p-0">
        <header class="sticky top-20 z-10 rounded-t-lg border-b border-slate-200 bg-white/95 p-4 backdrop-blur sm:p-5">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="break-words text-lg font-semibold text-slate-950">{{ sectionTitle }}</h2>
                <span class="status-badge" :class="hasUnsavedChanges ? 'status-warning' : 'status-success'">
                  {{ hasUnsavedChanges ? 'Есть несохраненные изменения' : 'Сохранено' }}
                </span>
                <span class="status-badge" :class="section?.is_active ? 'status-success' : 'status-neutral'">
                  {{ section?.is_active ? 'Активна' : 'Неактивна' }}
                </span>
              </div>
              <div class="mt-2 flex flex-wrap gap-1.5 text-xs text-slate-500">
                <span v-for="meta in sectionMeta" :key="meta" class="rounded-full bg-slate-100 px-2.5 py-1">{{ meta }}</span>
                <span class="rounded-full bg-slate-100 px-2.5 py-1">
                  {{ sectionItemsCount ? elementCountLabel(sectionItemsCount) : 'без элементов' }}
                </span>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <button type="button" class="action-button-secondary" :disabled="saving || loading || !hasUnsavedChanges" @click="cancelChanges">
                <RotateCcw :size="17" />Отменить
              </button>
              <button type="button" class="action-button-primary" :disabled="saving || loading || !hasSchema || !hasUnsavedChanges" @click="save">
                <Save :size="17" />{{ saving ? 'Сохраняем...' : 'Сохранить раздел' }}
              </button>
            </div>
          </div>
        </header>

        <div class="p-4 sm:p-5">
          <DynamicForm v-model="content" :schema="schema" :upload-context="uploadContext" />
        </div>
      </section>
    </div>
  </div>
</template>
