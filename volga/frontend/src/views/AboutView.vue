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
    const data = await getPage("about");
    page.value = data;
  } catch (e) {
    console.error(e);
    error.value = "Не удалось загрузить страницу";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppHeader />

  <main class="about-page-state">
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
.about-page-state {
  min-height: 40vh;
}
</style>
