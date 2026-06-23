<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import { getArticleBySlug } from "../api/articles";
import RichText from "../components/ui/RichText.vue";

const route = useRoute();

const article = ref(null);
const loading = ref(false);
const error = ref("");

const formattedDate = computed(() => {
  if (!article.value?.created_at) return "";
  return new Date(article.value.created_at).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
});

const loadArticle = async () => {
  loading.value = true;
  error.value = "";

  try {
    article.value = await getArticleBySlug(route.params.slug);
  } catch (err) {
    console.error("[article] failed to load", err);
    article.value = null;
    error.value = "Материал не найден";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadArticle();
});
</script>

<template>
  <AppHeader />

  <main class="single-article">
    <section v-if="loading" class="single-article__not-found glass-card">
      <h1>Загрузка...</h1>
    </section>

    <section v-else-if="article" class="single-article__content">
      <router-link class="single-article__back" to="/articles">Назад</router-link>
      <p class="single-article__date">{{ formattedDate }}</p>
      <h1 class="single-article__title">{{ article.title }}</h1>
      <img class="single-article__cover" :src="article.preview_image" :alt="article.title" />

      <div v-if="article.content_type === 'video' && article.video_url" class="single-article__video">
        <iframe
          :src="article.video_url"
          title="Видео в статье"
          loading="lazy"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerpolicy="strict-origin-when-cross-origin"
          allowfullscreen
        ></iframe>
      </div>

      <RichText :content="article.content" class="single-article__text" />
    </section>

    <section v-else class="single-article__not-found glass-card">
      <h1>{{ error || "Материал не найден" }}</h1>
      <router-link class="single-article__back" to="/articles">Назад</router-link>
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.single-article {
  max-width: 920px;
  margin: 0 auto;
  padding: 0 20px 72px;
}

.single-article__content {
  display: grid;
  gap: 16px;
}

.single-article__back {
  justify-self: start;
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--primary-soft);
  color: var(--text-strong);
  font-size: var(--font-size-base);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.single-article__back:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px var(--shadow);
}

.single-article__date {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--muted);
}

.single-article__title {
  margin: 0;
  font-size: clamp(30px, 5vw, 46px);
  line-height: 1.1;
  color: var(--text-strong);
}

.single-article__cover {
  width: 100%;
  border-radius: 20px;
  max-height: 460px;
  object-fit: cover;
}

.single-article__video {
  border-radius: 18px;
  overflow: hidden;
}

.single-article__video iframe {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
  display: block;
}

.single-article__text {
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--text);
}

.single-article__text :deep(p) {
  margin: 0 0 14px;
}

.single-article__not-found {
  margin-top: 24px;
  padding: 22px;
  display: grid;
  gap: 12px;
}

.single-article__not-found h1 {
  margin: 0;
  font-size: 28px;
  color: var(--text-strong);
}

@media (max-width: 720px) {
  .single-article {
    padding: 0 14px 58px;
  }

  .single-article__text {
    font-size: var(--font-size-base);
  }
}
</style>
