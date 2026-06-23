import { createApp } from 'vue'
import './assets/css/main.css'
import App from './App.vue'
import router from './router'
import { revealDirective } from './composables/useRevealOnScroll'

if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual'
}

if (typeof document !== 'undefined') {
  document.documentElement.dataset.theme = 'light'
}

createApp(App).use(router).directive('reveal', revealDirective).mount('#app')
