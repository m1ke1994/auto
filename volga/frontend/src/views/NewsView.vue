<script setup>
import { computed, onMounted, ref } from "vue";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import NewsCard from "../components/NewsCard.vue";
import { getNewsList } from "../api/news";

const loading = ref(false);
const newsItems = ref([]);

const sortedNews = computed(() =>
  [...newsItems.value].sort((a, b) => new Date(b.published_date).getTime() - new Date(a.published_date).getTime())
);

const loadNews = async () => {
  loading.value = true;

  try {
    newsItems.value = await getNewsList();
  } catch (err) {
    console.error("[news] failed to load", err);
    newsItems.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadNews();
});
</script>

<template>
  <AppHeader />

  <main class="news-page">
    <section class="news-page__hero">
      <h1 class="news-page__title">Новости</h1>
      <p class="news-page__subtitle">
        Актуальные обновления «Нового Конаково»: события, форматы, изменения расписания и важные анонсы.
      </p>
    </section>

    <section class="news-page__grid">
      <p v-if="loading">Загрузка...</p>
      <NewsCard v-for="item in sortedNews" :key="item.slug" :item="item" />
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.news-page {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 24px 80px;
  display: grid;
  gap: 22px;
}

.news-page__hero {
  display: grid;
  gap: 10px;
  padding-top: 12px;
}

.news-page__title {
  margin: 0;
  font-size: clamp(32px, 5vw, 46px);
  color: var(--text-strong);
}

.news-page__subtitle {
  margin: 0;
  max-width: 780px;
  font-size: var(--font-size-small);
  line-height: var(--line-height-body);
  color: var(--muted);
}

.news-page__grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
}

@media (max-width: 1024px) {
  .news-page__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .news-page {
    padding: 0 16px 64px;
  }

  .news-page__grid {
    grid-template-columns: 1fr;
  }
}
</style>
