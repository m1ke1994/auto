<script setup>
import { onMounted } from 'vue'
import CookieBanner from './components/CookieBanner.vue'

const forceScrollTop = () => {
  if (typeof window === 'undefined') return
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  document.documentElement.scrollTop = 0
  document.body.scrollTop = 0
}

onMounted(() => {
  if (typeof window === 'undefined') return
  if (window.location.hash) {
    history.replaceState(null, '', window.location.pathname + window.location.search)
  }
  forceScrollTop()
  requestAnimationFrame(forceScrollTop)
  setTimeout(forceScrollTop, 0)
})
</script>

<template>
  <router-view />
  <CookieBanner />
</template>

