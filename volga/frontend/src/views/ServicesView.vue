<script setup>
import AppFooter from "../components/AppFooter.vue";
import AppHeader from "../components/AppHeader.vue";
import ProductGrid from "../components/Profile/ProductGrid.vue";
</script>

<template>
  <AppHeader />

  <main class="services-view">
    <section class="services-view__hero">
      <h1 class="services-view__title">Услуги и форматы отдыха</h1>
      <p class="services-view__subtitle">
        На этой странице собраны основные форматы отдыха в «Новом Конаково»: от
        спокойных программ восстановления до активных маршрутов и групповых встреч.
      </p>
    </section>

    <section class="services-view__grid">
      <ProductGrid />
    </section>

    <section class="services-view__details">
      <article class="services-view__card glass-card">
        <h2 class="services-view__h2">Как выбрать подходящий формат</h2>
        <p class="services-view__text">
          Если вы планируете день заранее, начните с описания услуги и времени программы.
          Для первого визита удобно выбрать спокойный формат, чтобы познакомиться с
          пространством и ритмом площадки.
        </p>
      </article>

      <article class="services-view__card glass-card">
        <h2 class="services-view__h2">Что входит в программы</h2>
        <p class="services-view__text">
          В карточках услуг указаны ключевые детали: длительность, описание, доступные
          тарифы и варианты участия. Это помогает заранее понять, какой сценарий отдыха
          подойдет вам по целям, нагрузке и настроению.
        </p>
      </article>

      <article class="services-view__card glass-card">
        <h2 class="services-view__h2">Индивидуальный сценарий дня</h2>
        <p class="services-view__text">
          Если нужен персональный вариант, можно сочетать несколько активностей в одном
          посещении. Такой подход позволяет собрать комфортный маршрут без перегруза и
          сделать отдых более осмысленным.
        </p>
      </article>

      <article class="services-view__card glass-card">
        <h2 class="services-view__h2">Практический подход к выбору услуг</h2>
        <p class="services-view__text">
          Чтобы выбрать услугу без лишних сомнений, полезно отталкиваться от цели визита:
          восстановление, активность, групповая практика или знакомство с пространством.
          Когда задача определена заранее, легче подобрать оптимальную длительность и нагрузку.
          Такой подход помогает избежать перегруза и делает участие более комфортным.
        </p>
        <p class="services-view__text">
          Мы рекомендуем сначала изучить описание формата и затем уточнить детали через заявку,
          если у вас есть индивидуальные пожелания. Это особенно актуально для тех, кто впервые
          приезжает в Новое Конаково и хочет спланировать визит максимально понятно.
        </p>
      </article>

      <article class="services-view__card glass-card">
        <h2 class="services-view__h2">Почему страница услуг важна</h2>
        <p class="services-view__text">
          Этот раздел — точка принятия решения для большинства посетителей сайта. Чем понятнее
          здесь структура, тексты и переходы к записи, тем выше шанс, что пользователь выберет
          подходящий формат и оставит заявку. Поэтому мы регулярно улучшаем карточки услуг,
          проверяем их актуальность и поддерживаем связку с расписанием и формой обращения.
        </p>
        <p class="services-view__text">
          Такая работа полезна и для SEO: поисковые системы лучше индексируют страницы, где есть
          четкие заголовки, логичная семантика и содержательные текстовые блоки по теме.
        </p>
      </article>
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.services-view {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: calc(var(--header-h, 72px) + 22px) 24px 80px;
  display: grid;
  gap: 24px;
}

.services-view__hero {
  display: grid;
  gap: 10px;
}

.services-view__title {
  margin: 0;
  font-size: clamp(32px, 5vw, 46px);
  color: var(--text-strong);
}

.services-view__subtitle {
  margin: 0;
  max-width: 780px;
  color: var(--muted);
  line-height: 1.6;
}

.services-view__details {
  display: grid;
  gap: 14px;
}

.services-view__card {
  padding: 18px 20px;
}

.services-view__h2 {
  margin: 0 0 8px;
  font-size: 20px;
  color: var(--text-strong);
}

.services-view__text {
  margin: 0;
  color: var(--text);
  line-height: 1.7;
}

@media (max-width: 720px) {
  .services-view {
    padding: calc(var(--header-h, 72px) + 16px) 16px 64px;
    gap: 20px;
  }
}
</style>
