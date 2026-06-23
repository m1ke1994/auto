<template>
  <button class="theme-toggle" :class="{ 'theme-toggle--icon': iconOnly }" type="button" @click="toggleTheme" :aria-label="label">
    <span class="theme-toggle__icon">{{ isDark ? "☀" : "☾" }}</span>
    <span v-if="!iconOnly" class="theme-toggle__text">{{ isDark ? "Тёмная" : "Светлая" }}</span>
  </button>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  iconOnly: { type: Boolean, default: false },
})

const isDark = ref(false)

const applyTheme = (theme) => {
  document.documentElement.dataset.theme = theme
  localStorage.setItem("theme", theme)
  isDark.value = theme === "dark"
}

const toggleTheme = () => {
  applyTheme(isDark.value ? "light" : "dark")
}

const label = computed(() => (isDark.value ? "Переключить на светлую тему" : "Переключить на тёмную тему"))

onMounted(() => {
  const stored = localStorage.getItem("theme")
  if (stored === "light" || stored === "dark") {
    applyTheme(stored)
  } else {
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
    applyTheme(prefersDark ? "dark" : "light")
  }
})
</script>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.theme-toggle:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px var(--shadow);
}

.theme-toggle__icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-base);
  background: color-mix(in srgb, var(--card) 70%, transparent);
}

.theme-toggle--icon {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
}

.theme-toggle--icon .theme-toggle__icon {
  width: 100%;
  height: 100%;
  background: transparent;
}
</style>
