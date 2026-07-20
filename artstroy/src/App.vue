<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import RequestModal from './components/modals/RequestModal.vue'

const route = useRoute()

const contentOffsetClass = computed(() => {
  if (route.path === '/' || route.path === '/projects') {
    return 'pt-0'
  }

  return 'pt-[6.25rem] sm:pt-[6.5rem] lg:pt-[8rem]'
})
</script>

<template>
  <AppHeader />

  <div :class="contentOffsetClass">
    <RouterView />
  </div>

  <RequestModal />
</template>
