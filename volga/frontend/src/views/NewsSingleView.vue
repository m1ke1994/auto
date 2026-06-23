<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import { getNewsBySlug } from "../api/news";
import RichText from "../components/ui/RichText.vue";

const route = useRoute();

const loading = ref(false);
const newsItem = ref(null);

const formattedDate = computed(() => {
  if (!newsItem.value?.published_date) return "";
  return new Date(newsItem.value.published_date).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
});

const loadNews = async () => {
  loading.value = true;

  try {
    newsItem.value = await getNewsBySlug(route.params.slug);
  } catch (err) {
    console.error("[news] failed to load detail", err);
    newsItem.value = null;
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

  <main class="news-single">
    <section v-if="loading" class="news-single__not-found glass-card">
      <h1>Загрузка...</h1>
    </section>

    <section v-else-if="newsItem" class="news-single__content">
      <router-link class="news-single__back" to="/news">Назад к новостям</router-link>
      <p class="news-single__date">{{ formattedDate }}</p>
      <h1 class="news-single__title">{{ newsItem.title }}</h1>
      <img class="news-single__cover" :src="newsItem.image" :alt="newsItem.title" />

      <RichText :content="newsItem.content" class="news-single__text" />
    </section>

    <section v-else class="news-single__not-found glass-card">
      <h1>Новость не найдена</h1>
      <router-link class="news-single__back" to="/news">Назад к новостям</router-link>
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.news-single {
  max-width: 920px;
  margin: 0 auto;
  padding: 0 20px 72px;
}

.news-single__content {
  display: grid;
  gap: 14px;
}

.news-single__back {
  justify-self: start;
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--primary-soft);
  color: var(--text-strong);
  font-size: var(--font-size-base);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.news-single__back:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px var(--shadow);
}

.news-single__date {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--muted);
}

.news-single__title {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(30px, 5vw, 46px);
  line-height: 1.1;
}

.news-single__cover {
  width: 100%;
  border-radius: 20px;
  max-height: 460px;
  object-fit: cover;
}

.news-single__text {
  color: var(--text);
  font-size: var(--font-size-base);
  line-height: 1.72;
}

.news-single__text :deep(p + p) {
  margin-top: 14px;
}

.news-single__not-found {
  margin-top: 24px;
  padding: 22px;
  display: grid;
  gap: 12px;
}

.news-single__not-found h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 28px;
}

@media (max-width: 720px) {
  .news-single {
    padding: 0 14px 58px;
  }

  .news-single__text {
    font-size: var(--font-size-base);
  }
}
</style>
