<script setup>
defineProps({
  message: {
    type: String,
    default: 'Данных пока нет. Они появятся после новых посещений сайта.',
  },
})

const checks = [
  'код трекера установлен на публичном сайте',
  'сайт открыт для посетителей',
  'были реальные посещения за выбранный период',
  'выбран правильный период',
  'боты не включены в основную статистику',
]
</script>

<template>
  <div class="empty-state">
    <h2>{{ message }}</h2>
    <p>Что проверить:</p>
    <ul class="mt-2 max-w-md space-y-1 text-left text-sm leading-6">
      <li v-for="item in checks" :key="item">- {{ item }}</li>
    </ul>
  </div>
</template>
