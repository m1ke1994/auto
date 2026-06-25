<script setup>
defineProps({
  status: {
    type: String,
    default: 'Недостаточно данных',
  },
})

const classes = {
  'Хорошо': 'status-success',
  'Нормально': 'status-neutral',
  'Требует внимания': 'status-warning',
  'Критично': 'status-danger',
  'Недостаточно данных': 'status-neutral',
}
</script>

<template>
  <span class="status-badge" :class="classes[status] || classes['Недостаточно данных']">{{ status }}</span>
</template>
