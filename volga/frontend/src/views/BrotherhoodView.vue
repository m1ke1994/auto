<script setup>
import { onMounted, ref } from "vue";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import PageTemplate from "../components/PageTemplate.vue";
import { getPage } from "@/api/pages";

const page = ref(null);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const data = await getPage("brotherhood");
    page.value = data;
  } catch (e) {
    console.error(e);
    error.value = e?.response?.status === 404 ? "Страница не найдена" : "Не удалось загрузить страницу";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppHeader />
  <main class="page-state">
    <p v-if="loading">Загрузка…</p>
    <p v-else-if="error">{{ error }}</p>
    <PageTemplate
      v-if="page"
      :title="page.title"
      :subtitle="page.subtitle"
      :heroImage="page.hero_image"
      :sections="page.sections"
      :gallery="page.gallery"
    />
  </main>
  <AppFooter />
</template>

<style scoped>
.page-state {
  min-height: 40vh;
}
</style>
