<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BarChart3, ShieldCheck, UserPlus, Zap } from '@lucide/vue'

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
    fieldErrors.acceptedTerms = 'Необходимо принять пользовательское соглашение и политику конфиденциальности.'
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
  <div class="app-viewport pwa-safe-screen relative flex items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_72%_18%,rgba(109,93,246,0.16),transparent_34%),radial-gradient(circle_at_18%_74%,rgba(124,99,255,0.12),transparent_30%),linear-gradient(180deg,#ffffff_0%,#FAFBFF_48%,#F5F7FD_100%)]">
    <div class="pointer-events-none absolute left-[-10rem] top-20 h-80 w-80 rounded-full bg-brand-200/40 blur-3xl" />
    <div class="pointer-events-none absolute bottom-[-9rem] right-[-8rem] h-96 w-96 rounded-full bg-brand-300/28 blur-3xl" />

    <div class="relative grid w-full max-w-6xl gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
      <section class="hidden lg:block">
        <RouterLink to="/" class="flex items-center gap-3">
          <span class="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_18px_42px_rgba(109,93,246,0.28)]">
            <Zap :size="25" fill="currentColor" />
          </span>
          <span class="text-2xl font-bold text-[#17223B]">TrackNode</span>
        </RouterLink>
        <h2 class="mt-10 max-w-xl text-5xl font-bold leading-tight text-[#17223B]">
          Создайте единый кабинет для данных вашего проекта
        </h2>
        <p class="mt-5 max-w-xl text-lg leading-8 text-slate-600">
          После регистрации аккаунт будет готов к работе. Первый сайт можно подключить отдельно, когда будут готовы домен и код аналитики.
        </p>
        <div class="mt-8 grid max-w-xl gap-3 sm:grid-cols-2">
          <div class="rounded-2xl border border-brand-100 bg-white/78 p-4 shadow-soft backdrop-blur">
            <BarChart3 :size="22" class="text-brand-700" />
            <p class="mt-3 text-sm font-semibold text-[#17223B]">Всё в одном кабинете</p>
            <p class="mt-1 text-sm leading-6 text-slate-500">Аналитика, заявки, SEO и отчёты.</p>
          </div>
          <div class="rounded-2xl border border-brand-100 bg-white/78 p-4 shadow-soft backdrop-blur">
            <ShieldCheck :size="22" class="text-brand-700" />
            <p class="mt-3 text-sm font-semibold text-[#17223B]">Безопасный доступ</p>
            <p class="mt-1 text-sm leading-6 text-slate-500">Пароль хранится только в защищённом виде.</p>
          </div>
        </div>
      </section>

      <section class="w-full rounded-[24px] border border-brand-100 bg-white/82 p-6 shadow-[0_24px_70px_rgba(32,40,70,0.12)] backdrop-blur-xl sm:p-8">
        <RouterLink to="/" class="flex items-center gap-3 lg:hidden">
          <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_16px_36px_rgba(109,93,246,0.28)]">
            <Zap :size="23" fill="currentColor" />
          </span>
          <span class="text-xl font-bold text-[#17223B]">TrackNode</span>
        </RouterLink>

        <p class="mt-8 inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 lg:mt-0">
          Новый аккаунт
        </p>
        <h1 class="mt-4 text-3xl font-bold text-[#17223B]">Регистрация в TrackNode</h1>
        <p class="mt-2 text-sm leading-6 text-slate-500">Заполните данные — после регистрации вы сразу попадёте в личный кабинет.</p>

        <form class="mt-6 grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Имя</label>
            <input v-model="form.name" type="text" autocomplete="name" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.name)">
            <p v-if="fieldErrors.name" class="mt-1 text-xs text-rose-700">{{ fieldErrors.name }}</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Электронная почта</label>
            <input v-model="form.email" type="email" autocomplete="email" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.email)">
            <p v-if="fieldErrors.email" class="mt-1 text-xs text-rose-700">{{ fieldErrors.email }}</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Пароль</label>
            <input v-model="form.password" type="password" autocomplete="new-password" class="form-control min-h-12" placeholder="Не менее 8 символов" :aria-invalid="Boolean(fieldErrors.password)">
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-rose-700">{{ fieldErrors.password }}</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Повтор пароля</label>
            <input v-model="form.passwordConfirm" type="password" autocomplete="new-password" class="form-control min-h-12" placeholder="Повторите пароль" :aria-invalid="Boolean(fieldErrors.passwordConfirm)">
            <p v-if="fieldErrors.passwordConfirm" class="mt-1 text-xs text-rose-700">{{ fieldErrors.passwordConfirm }}</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Компания или проект</label>
            <input v-model="form.companyName" type="text" autocomplete="organization" class="form-control min-h-12" :aria-invalid="Boolean(fieldErrors.companyName)">
            <p v-if="fieldErrors.companyName" class="mt-1 text-xs text-rose-700">{{ fieldErrors.companyName }}</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#17223B]">Телефон или Telegram <span class="font-normal text-slate-400">(необязательно)</span></label>
            <input v-model="form.contact" type="text" autocomplete="tel" class="form-control min-h-12" placeholder="+7… или @username" :aria-invalid="Boolean(fieldErrors.contact)">
            <p v-if="fieldErrors.contact" class="mt-1 text-xs text-rose-700">{{ fieldErrors.contact }}</p>
          </div>

          <div class="sm:col-span-2">
            <label class="flex cursor-pointer items-start gap-3 rounded-xl border border-brand-100 bg-brand-50/45 p-3 text-sm leading-6 text-slate-600">
              <input v-model="form.acceptedTerms" type="checkbox" class="mt-1 h-4 w-4 shrink-0 accent-brand-600">
              <span>
                Я принимаю
                <a href="/#footer" target="_blank" rel="noopener noreferrer" class="font-semibold text-brand-700 hover:text-brand-800">пользовательское соглашение</a>
                и
                <a href="/#footer" target="_blank" rel="noopener noreferrer" class="font-semibold text-brand-700 hover:text-brand-800">политику конфиденциальности</a>.
              </span>
            </label>
            <p v-if="fieldErrors.acceptedTerms" class="mt-1 text-xs text-rose-700">{{ fieldErrors.acceptedTerms }}</p>
          </div>

          <p v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 sm:col-span-2">
            {{ errorMessage }}
          </p>

          <button type="submit" :disabled="loading" class="action-button-primary w-full sm:col-span-2">
            <UserPlus :size="18" />
            {{ loading ? 'Создаём аккаунт...' : 'Зарегистрироваться' }}
          </button>

          <p class="text-center text-sm text-slate-500 sm:col-span-2">
            Уже есть аккаунт?
            <RouterLink to="/login" class="font-semibold text-brand-700 hover:text-brand-800">Войти</RouterLink>
          </p>
        </form>
      </section>
    </div>
  </div>
</template>
