<script setup>
import { onMounted, reactive, ref } from 'vue'

import { miniSaveSettings, miniSettings } from '../../api/mini'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const data = ref(null)
const form = reactive({
  send_to_telegram: false,
  daily_pdf_enabled: false,
})

async function loadSettings() {
  loading.value = true
  error.value = ''
  try {
    data.value = await miniSettings()
    form.send_to_telegram = Boolean(data.value?.send_to_telegram)
    form.daily_pdf_enabled = Boolean(data.value?.daily_pdf_enabled)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить настройки.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  error.value = ''
  try {
    data.value = await miniSaveSettings({
      send_to_telegram: form.send_to_telegram,
      daily_pdf_enabled: form.daily_pdf_enabled,
    })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось сохранить настройки.'
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <section class="surface space-y-4">
    <h2 class="text-base font-semibold text-[#17223B]">Настройки уведомлений</h2>

    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>
    <p v-if="loading" class="text-sm text-slate-500">Загрузка...</p>

    <label class="flex items-center gap-2 text-sm">
      <input v-model="form.send_to_telegram" type="checkbox" class="h-4 w-4 accent-brand-600">
      Отправлять заявки в Telegram
    </label>

    <label class="flex items-center gap-2 text-sm">
      <input v-model="form.daily_pdf_enabled" type="checkbox" class="h-4 w-4 accent-brand-600">
      Ежедневный PDF-отчёт
    </label>

    <button
      class="action-button-primary"
      :disabled="saving"
      @click="saveSettings"
    >
      {{ saving ? 'Сохраняем...' : 'Сохранить' }}
    </button>

    <div class="rounded-2xl border border-brand-100 bg-brand-50/50 p-3 text-sm">
      <p><strong>Telegram:</strong> {{ data?.telegram_status === 'connected' ? 'подключен' : 'не подключен' }}</p>
      <p class="mt-1 text-slate-500">Технические параметры подключения скрыты и управляются автоматически.</p>
    </div>
  </section>
</template>
