<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TrackNodeIcon from '../components/TrackNodeIcon.vue'

import { useAuthStore } from '../stores/auth'
import { intendedRouteAfterAuth } from '../router/authRedirects'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: '',
})

const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login({
      email: form.email,
      password: form.password,
    })

    await router.push(intendedRouteAfterAuth(route.query.redirect))
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось войти. Проверьте email и пароль.'
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
      <h1 id="auth-title">Вход</h1>
      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label for="auth-email" class="mb-2 block text-sm font-semibold text-slate-100">Электронная почта</label>
          <input
            id="auth-email" v-model="form.email"
            type="email"
            autocomplete="email"
            class="form-control min-h-12"
          >
        </div>

        <div>
          <label for="auth-password" class="mb-2 block text-sm font-semibold text-slate-100">Пароль</label>
          <input
            id="auth-password" v-model="form.password"
            type="password"
            autocomplete="current-password"
            class="form-control min-h-12"
            placeholder="••••••••"
          >
        </div>

        <p role="alert" v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ errorMessage }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="action-button-primary w-full"
        >
          <TrackNodeIcon v-if="loading" animated class="h-5 w-5" />
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>

        <p class="text-center text-sm text-slate-400">
          Нет аккаунта?
          <RouterLink to="/register" class="font-semibold text-brand-300 hover:text-brand-200">
            Зарегистрироваться
          </RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>
