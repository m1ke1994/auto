<script setup>
import AppHeader from '../components/AppHeader.vue';
import AppFooter from '../components/AppFooter.vue';
import ScheduleSection from '../components/ScheduleSection.vue';
</script>

<template>
    <AppHeader />
    <main class="schedule-view">
        <div class="schedule-view__inner">
            <header class="schedule-view__head">
                <h1 class="schedule-view__title">Расписание занятий</h1>
                <p class="schedule-view__subtitle">
                    Выберите удобный день и посмотрите доступные программы с деталями.
                </p>
            </header>
            <ScheduleSection />
        </div>
    </main>
    <AppFooter />
</template>

<style scoped>
.schedule-view {
  padding: 12px 0 80px;
}

.schedule-view__inner {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 24px;
}

.schedule-view__head {
  display: grid;
  gap: 8px;
}

.schedule-view__title {
  margin: 0;
  font-size: clamp(30px, 5vw, 44px);
  color: var(--text-strong);
}

.schedule-view__subtitle {
  margin: 0;
  max-width: 720px;
  color: var(--muted);
}

@media (max-width: 720px) {
  .schedule-view {
    padding: 8px 0 64px;
  }

  .schedule-view__inner {
    padding: 0 16px;
  }
}
</style>
