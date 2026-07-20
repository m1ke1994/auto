<script setup>
import { computed } from 'vue'
import { usePublicSiteContent } from './composables/usePublicSiteContent'
import { resolveTemplateComponent } from './templates/templateRegistry'

const { site, sections, loading, error } = usePublicSiteContent()
const templateComponent = computed(() => resolveTemplateComponent(site.value?.builder_template_key, site.value?.slug))
</script>

<template>
  <div v-if="loading" class="template-status">Загрузка сайта...</div>
  <div v-else-if="error" class="template-status template-status--error">{{ error }}</div>
  <div v-else-if="!templateComponent" class="template-status template-status--error">
    Неизвестный шаблон: {{ site?.builder_template_key || 'ключ не задан' }}
  </div>
  <component :is="templateComponent" v-else :site="site" :sections="sections" />
</template>

<style scoped>
.template-status { display: grid; min-height: 100vh; place-items: center; padding: 2rem; font: 600 1rem/1.5 system-ui, sans-serif; color: #334155; }
.template-status--error { color: #b91c1c; }
</style>
