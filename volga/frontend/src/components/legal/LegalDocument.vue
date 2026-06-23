<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  updatedAt: { type: String, default: '' },
  sections: { type: Array, default: () => [] },
})
</script>

<template>
  <section class="legal">
    <div class="legal__hero">
      <h1 class="legal__title">{{ title }}</h1>
      <p v-if="subtitle" class="legal__subtitle">{{ subtitle }}</p>
      <p v-if="updatedAt" class="legal__updated">Дата обновления: {{ updatedAt }}</p>
    </div>

    <div class="legal__sections">
      <article v-for="section in sections" :key="section.title" class="legal__section glass-card">
        <h2 class="legal__section-title">{{ section.title }}</h2>
        <p v-for="(paragraph, index) in section.paragraphs" :key="`${section.title}-${index}`" class="legal__section-text">
          {{ paragraph }}
        </p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.legal {
  min-height: 100vh;
  padding: calc(var(--header-h, 72px) + 28px) 24px 80px;
  max-width: var(--container-max);
  margin: 0 auto;
  color: var(--text);
}

.legal__hero {
  margin-bottom: 24px;
}

.legal__title {
  margin: 0 0 10px;
  color: var(--text-strong);
  font-size: 34px;
  line-height: 1.2;
}

.legal__subtitle {
  margin: 0;
  color: var(--muted);
  font-size: var(--font-size-base);
  max-width: 880px;
}

.legal__updated {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: var(--font-size-base);
}

.legal__sections {
  display: grid;
  gap: 18px;
}

.legal__section {
  padding: 20px;
}

.legal__section-title {
  margin: 0 0 10px;
  color: var(--text-strong);
  font-size: 20px;
}

.legal__section-text {
  margin: 0;
  color: var(--text);
  line-height: 1.7;
}

.legal__section-text + .legal__section-text {
  margin-top: 10px;
}

@media (max-width: 768px) {
  .legal {
    padding: calc(var(--header-h, 72px) + 20px) 16px 56px;
  }

  .legal__title {
    font-size: 28px;
  }
}
</style>
