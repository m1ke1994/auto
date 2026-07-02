<script setup>
import { onBeforeUnmount, onErrorCaptured, onMounted, ref } from 'vue'
import { CircleAlert, RefreshCw } from '@lucide/vue'

const fatalError = ref(false)

function showFatalError() {
  fatalError.value = true
}

function reloadApplication() {
  window.location.reload()
}

onErrorCaptured((error) => {
  console.error('TrackNode render error.', error)
  showFatalError()
  return false
})

onMounted(() => window.addEventListener('tracknode:fatal-error', showFatalError))
onBeforeUnmount(() => window.removeEventListener('tracknode:fatal-error', showFatalError))
</script>

<template>
  <main v-if="fatalError" class="app-viewport grid place-content-center bg-[#FAFBFF] p-6 text-center" role="alert">
    <div class="surface mx-auto max-w-lg">
      <CircleAlert :size="34" class="mx-auto text-amber-600" />
      <h1 class="mt-4 text-xl font-bold text-[#17223B]">Не удалось открыть TrackNode</h1>
      <p class="mt-2 text-sm leading-6 text-slate-600">
        Обновите приложение. Если проблема повторится, проверьте подключение к интернету.
      </p>
      <div class="mt-5 flex flex-wrap justify-center gap-3">
        <button type="button" class="action-button-primary" @click="reloadApplication">
          <RefreshCw :size="17" />
          Обновить
        </button>
        <a class="action-button-secondary" href="/">На главную</a>
      </div>
    </div>
  </main>
  <RouterView v-else />
</template>
