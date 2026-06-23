<script setup>
import { computed, onMounted, ref } from "vue";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import ArticleCard from "../components/ArticleCard.vue";
import { getArticles } from "../api/articles";

const activeTab = ref("article");
const loading = ref(false);
const error = ref("");
const materials = ref([]);

const tabs = [
  { id: "article", label: "Статьи" },
  { id: "video", label: "Видео" },
];

const filteredMaterials = computed(() =>
  materials.value.filter((item) => item.content_type === activeTab.value)
);

const loadArticles = async () => {
  loading.value = true;
  error.value = "";

  try {
    materials.value = await getArticles();
  } catch (err) {
    console.error("[articles] failed to load", err);
    materials.value = [];
    error.value = "Не удалось загрузить материалы.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadArticles();
});
</script>

<template>
  <AppHeader />

  <main class="articles-page">
    <section class="articles-page__hero">
      <h1 class="articles-page__title">Статьи / Видео</h1>
      <p class="articles-page__subtitle">
        Статьи и видео о жизни в «Новом Конаково»: маршруты, практики, события и вдохновение для спокойного и активного отдыха.
      </p>
    </section>

    <section class="articles-page__tabs" aria-label="Фильтр материалов">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="articles-page__tab"
        :class="{ 'articles-page__tab--active': activeTab === tab.id }"
        type="button"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </section>

    <section class="articles-page__grid">
      <p v-if="loading">Загрузка...</p>
      <ArticleCard v-for="item in filteredMaterials" :key="item.slug" :item="item" />
    </section>

    <p v-if="error">{{ error }}</p>
  </main>

  <AppFooter />
</template>

<style scoped>
.articles-page {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 24px 80px;
  display: grid;
  gap: 22px;
}

.articles-page__hero {
  display: grid;
  gap: 10px;
  padding-top: 12px;
}

.articles-page__title {
  margin: 0;
  font-size: clamp(32px, 5vw, 46px);
  color: var(--text-strong);
}

.articles-page__subtitle {
  margin: 0;
  max-width: 780px;
  font-size: var(--font-size-small);
  line-height: var(--line-height-body);
  color: var(--muted);
}

.articles-page__tabs {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--bg-elevated) 74%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  width: fit-content;
  max-width: 100%;
}

.articles-page__tab {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: transparent;
  color: var(--muted);
  font-size: var(--font-size-menu);
  cursor: pointer;
  transition: color 180ms ease, background 180ms ease, transform 180ms ease;
}

.articles-page__tab:hover {
  transform: translateY(-1px);
  color: var(--text-strong);
}

.articles-page__tab--active {
  background: color-mix(in srgb, var(--color-sand) 90%, var(--color-warm-yellow));
  color: var(--color-dark-deep);
  box-shadow: 0 10px 20px var(--shadow);
}

.articles-page__grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
}

@media (max-width: 1024px) {
  .articles-page__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .articles-page {
    padding: 0 16px 64px;
  }

  .articles-page__tabs {
    width: 100%;
    justify-content: space-between;
  }

  .articles-page__tab {
    flex: 1 1 auto;
  }

  .articles-page__grid {
    grid-template-columns: 1fr;
  }
}
</style>
