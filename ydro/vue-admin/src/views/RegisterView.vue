<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import TrackNodeIcon from '../components/TrackNodeIcon.vue'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  name: '',
  email: '',
  password: '',
  passwordConfirm: '',
  companyName: '',
  contact: '',
  acceptedTerms: false,
})

const fieldErrors = reactive({
  name: '',
  email: '',
  password: '',
  passwordConfirm: '',
  companyName: '',
  contact: '',
  acceptedTerms: '',
})

const loading = ref(false)
const errorMessage = ref('')

function resetErrors() {
  Object.keys(fieldErrors).forEach((key) => {
    fieldErrors[key] = ''
  })
  errorMessage.value = ''
}

function validateForm() {
  resetErrors()

  if (!form.name.trim()) fieldErrors.name = 'Укажите имя.'
  if (!form.email.trim()) {
    fieldErrors.email = 'Укажите email.'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    fieldErrors.email = 'Введите корректный email.'
  }
  if (!form.password) fieldErrors.password = 'Укажите пароль.'
  if (!form.passwordConfirm) {
    fieldErrors.passwordConfirm = 'Повторите пароль.'
  } else if (form.password !== form.passwordConfirm) {
    fieldErrors.passwordConfirm = 'Пароли не совпадают.'
  }
  if (!form.companyName.trim()) fieldErrors.companyName = 'Укажите название компании или проекта.'
  if (!form.acceptedTerms) {
    fieldErrors.acceptedTerms = 'Необходимо принять пользовательское соглашение.'
  }

  return !Object.values(fieldErrors).some(Boolean)
}

function firstMessage(value) {
  if (Array.isArray(value)) return firstMessage(value[0])
  if (typeof value === 'string') return value
  return ''
}

function applyBackendErrors(data) {
  const fieldMap = {
    name: 'name',
    email: 'email',
    password: 'password',
    password_confirm: 'passwordConfirm',
    company_name: 'companyName',
    contact: 'contact',
    accepted_terms: 'acceptedTerms',
  }

  Object.entries(fieldMap).forEach(([backendKey, frontendKey]) => {
    const message = firstMessage(data?.[backendKey])
    if (message) fieldErrors[frontendKey] = message
  })

  errorMessage.value =
    firstMessage(data?.non_field_errors) ||
    firstMessage(data?.detail) ||
    (Object.values(fieldErrors).some(Boolean) ? '' : 'Не удалось создать аккаунт. Попробуйте ещё раз.')
}

async function submit() {
  if (!validateForm()) return

  loading.value = true

  try {
    await authStore.register({
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
      password_confirm: form.passwordConfirm,
      company_name: form.companyName.trim(),
      contact: form.contact.trim(),
      accepted_terms: form.acceptedTerms,
    })
    await router.push({ name: 'dashboard', query: { registered: '1' } })
  } catch (error) {
    applyBackendErrors(error?.response?.data)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="tn-auth app-viewport pwa-safe-screen">
    <section class="tn-auth-card" aria-labelledby="auth-title">
      <RouterLink to="/" class="tn-auth-logo" aria-label="TrackNode — на главную">
        <TrackNodeIcon class="h-14 w-14" />
      </RouterLink>
      <h1 id="auth-title">Регистрация</h1>
      <form class="mt-7 grid gap-4" novalidate @submit.prevent="submit">
          <div>
            <label for="auth-name" class="mb-2 block text-sm font-semibold text-slate-100">Имя</label>
            <input id="auth-name" v-model="form.name" type="text" autocomplete="name" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.name)">
            <p role="alert" v-if="fieldErrors.name" class="mt-1 text-xs text-rose-700">{{ fieldErrors.name }}</p>
          </div>

          <div>
            <label for="auth-email" class="mb-2 block text-sm font-semibold text-slate-100">Электронная почта</label>
            <input id="auth-email" v-model="form.email" type="email" autocomplete="email" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.email)">
            <p role="alert" v-if="fieldErrors.email" class="mt-1 text-xs text-rose-700">{{ fieldErrors.email }}</p>
          </div>

          <div>
            <label for="auth-password" class="mb-2 block text-sm font-semibold text-slate-100">Пароль</label>
            <input id="auth-password" v-model="form.password" type="password" autocomplete="new-password" class="form-control min-h-12" placeholder="Не менее 8 символов" :aria-invalid="Boolean(fieldErrors.password)">
            <p role="alert" v-if="fieldErrors.password" class="mt-1 text-xs text-rose-700">{{ fieldErrors.password }}</p>
          </div>

          <div>
            <label for="auth-passwordConfirm" class="mb-2 block text-sm font-semibold text-slate-100">Повтор пароля</label>
            <input id="auth-passwordConfirm" v-model="form.passwordConfirm" type="password" autocomplete="new-password" class="form-control min-h-12" placeholder="Повторите пароль" :aria-invalid="Boolean(fieldErrors.passwordConfirm)">
            <p role="alert" v-if="fieldErrors.passwordConfirm" class="mt-1 text-xs text-rose-700">{{ fieldErrors.passwordConfirm }}</p>
          </div>

          <div>
            <label for="auth-companyName" class="mb-2 block text-sm font-semibold text-slate-100">Компания или проект</label>
            <input id="auth-companyName" v-model="form.companyName" type="text" autocomplete="organization" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.companyName)">
            <p role="alert" v-if="fieldErrors.companyName" class="mt-1 text-xs text-rose-700">{{ fieldErrors.companyName }}</p>
          </div>

          <div>
            <label for="auth-contact" class="mb-2 block text-sm font-semibold text-slate-100">Контактный телефон <span class="font-normal text-slate-400">(необязательно)</span></label>
            <input id="auth-contact" v-model="form.contact" type="text" autocomplete="tel" class="form-control min-h-12" placeholder="+7 (900) 000-00-00" :aria-invalid="Boolean(fieldErrors.contact)">
            <p role="alert" v-if="fieldErrors.contact" class="mt-1 text-xs text-rose-700">{{ fieldErrors.contact }}</p>
          </div>

          <div class="">
            <label class="flex cursor-pointer items-start gap-3 rounded-xl border border-brand-100 bg-brand-50/45 p-3 text-sm leading-6 text-slate-300">
              <input v-model="form.acceptedTerms" type="checkbox" class="mt-1 h-4 w-4 shrink-0 accent-brand-600">
              <span>
                Я принимаю
                <RouterLink to="/terms" target="_blank" class="font-semibold text-brand-300 hover:text-brand-200">пользовательское соглашение</RouterLink>.
              </span>
            </label>
            <p v-if="fieldErrors.acceptedTerms" class="mt-1 text-xs text-rose-700">{{ fieldErrors.acceptedTerms }}</p>
          </div>

          <p class="text-xs leading-5 text-slate-400 ">Данные регистрации используются для создания аккаунта и исполнения соглашения. Подробности — в <RouterLink to="/privacy" target="_blank" class="font-semibold text-brand-300">политике обработки персональных данных</RouterLink>. Согласие на рекламные рассылки не запрашивается.</p>
          <p role="alert" v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 ">
            {{ errorMessage }}
          </p>

          <button type="submit" :disabled="loading" class="action-button-primary w-full ">
            <TrackNodeIcon v-if="loading" animated class="h-5 w-5" />
            {{ loading ? 'Создаём аккаунт...' : 'Зарегистрироваться' }}
          </button>

          <p class="text-center text-sm text-slate-400 ">
            Уже есть аккаунт?
            <RouterLink to="/login" class="font-semibold text-brand-300 hover:text-brand-200">Войти</RouterLink>
          </p>
        </form>
    </section>
  </main>
</template>
