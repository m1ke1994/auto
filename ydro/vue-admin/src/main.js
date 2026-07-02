import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { registerServiceWorker } from './pwa'
import './style.css'

const CHUNK_RELOAD_KEY = 'tracknode:chunk-reload-at'

function showBootstrapError(error) {
  console.error('TrackNode bootstrap error.', error)
  document.querySelector('.app-boot')?.classList.add('is-error')
  window.dispatchEvent(new CustomEvent('tracknode:fatal-error'))
}

function recoverFromChunkError(event) {
  event.preventDefault()
  const lastReload = Number(sessionStorage.getItem(CHUNK_RELOAD_KEY) || 0)
  if (Date.now() - lastReload > 30_000) {
    sessionStorage.setItem(CHUNK_RELOAD_KEY, String(Date.now()))
    window.location.reload()
    return
  }
  showBootstrapError(event.payload || new Error('Frontend chunk could not be loaded.'))
}

window.addEventListener('vite:preloadError', recoverFromChunkError)
registerServiceWorker()

async function bootstrap() {
  const app = createApp(App)
  app.config.errorHandler = (error) => {
    console.error('TrackNode application error.', error)
    window.dispatchEvent(new CustomEvent('tracknode:fatal-error'))
  }

  app.use(createPinia())
  app.use(router)
  router.onError(showBootstrapError)

  await router.isReady()
  app.mount('#app')
  sessionStorage.removeItem(CHUNK_RELOAD_KEY)
}

bootstrap().catch(showBootstrapError)
