<script setup>
import RichText from "./ui/RichText.vue";

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  showDescription: {
    type: Boolean,
    default: true,
  },
});
</script>

<template>
  <article class="article-card glass-card">
    <div class="article-card__media">
      <img class="article-card__image" :src="item.preview_image" :alt="item.title" loading="lazy" decoding="async" />
      <span v-if="item.content_type === 'video'" class="article-card__video-badge" aria-hidden="true">▶</span>
    </div>
    <div class="article-card__content">
      <h3 class="article-card__title">{{ item.title }}</h3>
      <RichText v-if="showDescription" :content="item.preview_description" class="article-card__description" />
      <router-link class="article-card__action btn-outline" :to="`/articles/${item.slug}`">Читать дальше</router-link>
    </div>
  </article>
</template>

<style scoped>
.article-card {
  overflow: hidden;
  border-radius: 20px;
}

.article-card__media {
  position: relative;
}

.article-card__image {
  width: 100%;
  height: 210px;
  object-fit: cover;
  display: block;
}

.article-card__video-badge {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-dark-deep) 78%, transparent);
  color: var(--color-background-light);
  font-size: 15px;
}

.article-card__content {
  padding: 16px;
  display: grid;
  gap: 12px;
}

.article-card__title {
  margin: 0;
  font-size: 20px;
  line-height: 1.25;
  color: var(--text-strong);
}

.article-card__description {
  margin: 0;
  font-size: var(--font-size-small);
  line-height: var(--line-height-body);
  color: var(--muted);
  max-height: calc(3 * var(--line-height-body) * 1em);
  overflow: hidden;
}

.article-card__action {
  justify-self: start;
}

@media (max-width: 768px) {
  .article-card__image {
    height: 190px;
  }

  .article-card__title {
    font-size: 18px;
  }
}
</style>
