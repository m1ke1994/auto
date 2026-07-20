<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Blocks, ExternalLink } from '@lucide/vue'
import SectionList from '../components/SectionList.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()
const siteId = computed(() => Number(route.params.siteId))
const previewUrl = computed(() => siteStore.currentSite?.preview_url || '')
const previewLoading = ref(true)
const previewError = ref('')
const previewRevision = ref(0)

function handlePreviewLoad() {
  previewLoading.value = false
  previewError.value = ''
}

function handlePreviewError() {
  previewLoading.value = false
  previewError.value = 'Не удалось загрузить предпросмотр сайта.'
}

function reloadPreview() {
  previewLoading.value = true
  previewError.value = ''
  previewRevision.value += 1
}

onMounted(async () => {
  siteStore.selectSite(siteId.value)
  if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
  await sectionsStore.fetchSections(siteId.value)
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">Содержимое сайта</p>
      <h1>Редактирование сайта</h1>
      <p>Выберите раздел, чтобы изменить текст, изображения, кнопки и ссылки.</p>
    </header>
    <section class="editor-preview">
      <div class="editor-preview__heading">
        <h2>Предпросмотр</h2>
        <div class="editor-preview__actions">
          <button type="button" @click="reloadPreview">Повторить</button>
          <a v-if="previewUrl" :href="previewUrl" target="_blank" rel="noopener"><ExternalLink :size="17" />Открыть в новой вкладке</a>
        </div>
      </div>
      <div v-if="!previewUrl" class="editor-preview__state" role="alert">URL предпросмотра отсутствует.</div>
      <div v-else class="editor-preview__frame-wrap">
        <div v-if="previewLoading" class="editor-preview__state">Загрузка предпросмотра...</div>
        <div v-if="previewError" class="editor-preview__state editor-preview__state--error" role="alert">{{ previewError }}</div>
        <iframe :key="previewRevision" :src="previewUrl" title="Предпросмотр сайта" class="site-preview-frame" @load="handlePreviewLoad" @error="handlePreviewError" />
      </div>
    </section>
    <section v-if="sectionsStore.loading" class="empty-state"><span class="loading-dot" /><p>Загружаем разделы...</p></section>
    <section v-else-if="sectionsStore.sections.length === 0" class="empty-state"><Blocks :size="30" /><h2>Разделов пока нет</h2><p>Обратитесь к администратору, чтобы добавить первый раздел сайта.</p></section>
    <SectionList v-else :site-id="siteId" :sections="sectionsStore.sections" />
  </div>
</template>

<style scoped>
.editor-preview{overflow:hidden;border:1px solid #dbe2ea;border-radius:8px;background:#fff}.editor-preview__heading,.editor-preview__actions{display:flex;align-items:center;gap:12px}.editor-preview__heading{justify-content:space-between;padding:12px 16px;border-bottom:1px solid #e7ebf0}.editor-preview__heading h2{margin:0;font-size:1rem}.editor-preview__heading a,.editor-preview__heading button{display:inline-flex;align-items:center;gap:6px;border:0;background:none;color:#4f46e5;text-decoration:none;font:inherit;font-weight:700}.editor-preview__frame-wrap{position:relative;min-height:720px}.editor-preview__state{display:grid;min-height:96px;place-items:center;padding:20px;color:#64748b}.editor-preview__frame-wrap>.editor-preview__state{position:absolute;inset:0 0 auto;z-index:1;background:#fff}.editor-preview__state--error{color:#b91c1c}.site-preview-frame{display:block;width:100%;min-height:720px;border:0;background:#fff}@media(max-width:700px){.editor-preview__heading{align-items:flex-start;flex-direction:column}.editor-preview__actions{flex-wrap:wrap}}
</style>
