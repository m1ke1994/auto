<script setup>
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";

const page = {
  title: "Братство Лосей",
  subtitle:
    "Экскурсионный и клубный формат «Нового Конаково»: природа, маршрутные встречи и сообщество в спокойном ритме.",
  content: [
    {
      type: "text",
      heading: "О формате",
      value:
        "«Братство Лосей» — это программа для тех, кто хочет быть в живом контакте с природой и людьми, не теряя личный темп. Здесь нет гонки за количеством точек, но есть качество маршрута и наблюдения.",
    },
    {
      type: "image",
      src: "/images/service-moose-cover.jpg",
      alt: "Маршрут Братства Лосей",
    },
    {
      type: "text",
      value:
        "Каждая встреча строится как последовательность блоков: мягкий старт, маршрут, пауза у воды, разговор в круге. Такой сценарий помогает участникам не уставать от впечатлений, а проживать их глубже.",
    },
    {
      type: "text",
      heading: "Что происходит на маршруте",
      value:
        "Мы делаем остановки в ключевых точках, где можно посмотреть на ландшафт иначе: не «пройти и забыть», а заметить детали, ритм и смену состояния по ходу пути.",
    },
    {
      type: "video",
      src: "https://www.youtube.com/embed/jNQXAC9IVRw",
    },
    {
      type: "text",
      value:
        "После активной части всегда есть время на интеграцию. В этот момент появляются важные выводы и идеи, которые редко приходят в обычной повседневной спешке.",
    },
    {
      type: "image",
      src: "/images/service-moose-2.jpg",
      alt: "Пауза на маршруте у воды",
    },
    {
      type: "text",
      heading: "Кому подойдет",
      value:
        "Формат подходит и тем, кто приезжает впервые, и тем, кто уже в сообществе. Важно только одно: готовность быть в процессе, а не потреблять маршрут как быстрый аттракцион.",
    },
    {
      type: "text",
      value:
        "В долгую «Братство Лосей» становится не просто программой выходного дня, а опорным ритмом. Люди возвращаются за состоянием, а не за разовым событием.",
    },
  ],
};
</script>

<template>
  <AppHeader />

  <main class="content-page">
    <header class="content-page__hero">
      <h1 class="content-page__title">{{ page.title }}</h1>
      <p class="content-page__subtitle">{{ page.subtitle }}</p>
    </header>

    <section class="content-page__body">
      <article v-for="(block, index) in page.content" :key="`moose-${index}`" class="content-page__block">
        <template v-if="block.type === 'text'">
          <h2 v-if="block.heading" class="content-page__h2">{{ block.heading }}</h2>
          <p class="content-page__text">{{ block.value }}</p>
        </template>

        <img
          v-else-if="block.type === 'image'"
          class="content-page__image"
          :src="block.src"
          :alt="block.alt || page.title"
          loading="lazy"
          decoding="async"
        />

        <div v-else-if="block.type === 'video'" class="content-page__video-wrap">
          <iframe
            class="content-page__video"
            :src="block.src"
            title="Видео"
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen
          ></iframe>
        </div>
      </article>
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.content-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 20px 72px;
  display: grid;
  gap: 22px;
}

.content-page__hero {
  display: grid;
  gap: 10px;
}

.content-page__title {
  margin: 0;
  font-size: clamp(34px, 6vw, 52px);
  line-height: 1.05;
  color: var(--text-strong);
}

.content-page__subtitle {
  margin: 0;
  color: var(--muted);
  font-size: var(--font-size-base);
  line-height: 1.6;
}

.content-page__body {
  display: grid;
  gap: 18px;
}

.content-page__block {
  display: grid;
  gap: 10px;
}

.content-page__h2 {
  margin: 0;
  font-size: clamp(22px, 4vw, 30px);
  color: var(--text-strong);
}

.content-page__text {
  margin: 0;
  font-size: var(--font-size-base);
  line-height: 1.75;
  color: var(--text);
}

.content-page__image {
  width: 100%;
  border-radius: 18px;
  object-fit: cover;
  display: block;
}

.content-page__video-wrap {
  border-radius: 18px;
  overflow: hidden;
}

.content-page__video {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
  display: block;
}

@media (max-width: 720px) {
  .content-page {
    padding: 0 14px 58px;
  }

  .content-page__text {
    font-size: var(--font-size-base);
  }
}
</style>
