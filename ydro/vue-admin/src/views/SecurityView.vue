<script setup>
import { reactive, ref } from 'vue'
import { KeyRound, ShieldCheck } from '@lucide/vue'

import { changePasswordRequest } from '../api/auth'

const form = reactive({
  current_password: '',
  new_password: '',
  new_password_confirm: '',
})

const saving = ref(false)
const error = ref('')
const success = ref('')

function responseErrorMessage(requestError) {
  const data = requestError?.response?.data
  if (typeof data?.detail === 'string') return data.detail

  for (const field of ['current_password', 'new_password', 'new_password_confirm']) {
    const fieldErrors = data?.[field]
    if (Array.isArray(fieldErrors) && fieldErrors.length) return String(fieldErrors[0])
    if (typeof fieldErrors === 'string') return fieldErrors
  }

  return 'Не удалось изменить пароль. Попробуйте ещё раз.'
}

async function submit() {
  error.value = ''
  success.value = ''

  if (!form.current_password || !form.new_password || !form.new_password_confirm) {
    error.value = 'Все поля обязательны.'
    return
  }

  if (form.new_password !== form.new_password_confirm) {
    error.value = 'Новые пароли не совпадают.'
    return
  }

  saving.value = true
  try {
    const { data } = await changePasswordRequest({ ...form })
    success.value = data?.detail || 'Пароль успешно изменён.'
    form.current_password = ''
    form.new_password = ''
    form.new_password_confirm = ''
  } catch (requestError) {
    error.value = responseErrorMessage(requestError)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page-stack max-w-5xl">
    <header class="page-heading">
      <p class="eyebrow">Профиль</p>
      <h1>Безопасность</h1>
      <p>Измените пароль для входа в личный кабинет.</p>
    </header>

    <section class="surface max-w-2xl">
      <div class="section-heading">
        <div>
          <h2 class="flex items-center gap-2">
            <ShieldCheck :size="21" class="text-brand-600" />
            Смена пароля
          </h2>
          <p>После изменения пароля текущий сеанс останется активным.</p>
        </div>
      </div>

      <p v-if="error" class="notice-error mb-4" role="alert">{{ error }}</p>
      <p v-if="success" class="notice-success mb-4" role="status">{{ success }}</p>

      <form class="space-y-4" @submit.prevent="submit">
        <label class="block text-sm font-medium text-slate-700">
          Текущий пароль
          <input
            v-model="form.current_password"
            class="form-control mt-2"
            type="password"
            autocomplete="current-password"
            required
          >
        </label>

        <label class="block text-sm font-medium text-slate-700">
          Новый пароль
          <input
            v-model="form.new_password"
            class="form-control mt-2"
            type="password"
            autocomplete="new-password"
            required
          >
        </label>

        <label class="block text-sm font-medium text-slate-700">
          Повторите новый пароль
          <input
            v-model="form.new_password_confirm"
            class="form-control mt-2"
            type="password"
            autocomplete="new-password"
            required
          >
        </label>

        <p class="text-xs leading-5 text-slate-500">
          Используйте не менее 8 символов. Пароль не должен быть распространённым или состоять только из цифр.
        </p>

        <button class="action-button-primary" type="submit" :disabled="saving">
          <span v-if="saving" class="button-spinner" aria-hidden="true" />
          <KeyRound v-else :size="18" />
          {{ saving ? 'Сохраняем...' : 'Сменить пароль' }}
        </button>
      </form>
    </section>
  </div>
</template>
