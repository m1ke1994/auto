<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Blocks, ExternalLink } from '@lucide/vue'
import SectionList from '../components/SectionList.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()
const siteId = computed(() => Number(route.params.siteId))
const previewUrl = computed(() => siteStore.currentSite?.slug ? `/api/public/sites/${siteStore.currentSite.slug}/html/?preview=1` : '')

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
    <section v-if="previewUrl" class="editor-preview">
      <div class="editor-preview__heading"><h2>Предпросмотр</h2><a :href="previewUrl" target="_blank" rel="noopener"><ExternalLink :size="17" />Открыть</a></div>
      <iframe :src="previewUrl" title="Предпросмотр редактируемого сайта" />
    </section>
    <section v-if="sectionsStore.loading" class="empty-state"><span class="loading-dot" /><p>Загружаем разделы...</p></section>
    <section v-else-if="sectionsStore.sections.length === 0" class="empty-state"><Blocks :size="30" /><h2>Разделов пока нет</h2><p>Обратитесь к администратору, чтобы добавить первый раздел сайта.</p></section>
    <SectionList v-else :site-id="siteId" :sections="sectionsStore.sections" />
  </div>
</template>

<style scoped>
.editor-preview{overflow:hidden;border:1px solid #dbe2ea;border-radius:8px;background:#fff}.editor-preview__heading{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #e7ebf0}.editor-preview__heading h2{margin:0;font-size:1rem}.editor-preview__heading a{display:inline-flex;align-items:center;gap:6px;color:#4f46e5;text-decoration:none;font-weight:700}.editor-preview iframe{display:block;width:100%;height:560px;border:0;background:#fff}
</style>
