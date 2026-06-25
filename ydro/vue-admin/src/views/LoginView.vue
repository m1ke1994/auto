<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BarChart3, ShieldCheck, Zap } from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()

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

    const sites = await siteStore.fetchSites()

    if (sites.length === 1) {
      router.push(`/sites/${sites[0].id}/sections`)
    } else {
      router.push('/dashboard')
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось войти. Проверьте email и пароль.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_72%_18%,rgba(109,93,246,0.16),transparent_34%),radial-gradient(circle_at_18%_74%,rgba(124,99,255,0.12),transparent_30%),linear-gradient(180deg,#ffffff_0%,#FAFBFF_48%,#F5F7FD_100%)] px-4 py-10">
    <div class="pointer-events-none absolute left-[-10rem] top-20 h-80 w-80 rounded-full bg-brand-200/40 blur-3xl" />
    <div class="pointer-events-none absolute bottom-[-9rem] right-[-8rem] h-96 w-96 rounded-full bg-brand-300/28 blur-3xl" />

    <div class="relative grid w-full max-w-5xl gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
      <section class="hidden lg:block">
        <div class="flex items-center gap-3">
          <span class="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_18px_42px_rgba(109,93,246,0.28)]">
            <Zap :size="25" fill="currentColor" />
          </span>
          <span class="text-2xl font-bold text-[#17223B]">TrackNode</span>
        </div>
        <h2 class="mt-10 max-w-xl text-5xl font-bold leading-tight text-[#17223B]">
          Единый кабинет для аналитики, заявок и роста сайта
        </h2>
        <p class="mt-5 max-w-xl text-lg leading-8 text-slate-600">
          Входите в ту же премиальную платформу, которую видит пользователь на лендинге: светлая система, понятные данные и аккуратные рабочие сценарии.
        </p>
        <div class="mt-8 grid max-w-xl gap-3 sm:grid-cols-2">
          <div class="rounded-2xl border border-brand-100 bg-white/78 p-4 shadow-soft backdrop-blur">
            <BarChart3 :size="22" class="text-brand-700" />
            <p class="mt-3 text-sm font-semibold text-[#17223B]">Данные в одном месте</p>
            <p class="mt-1 text-sm leading-6 text-slate-500">Сайты, заявки, SEO и отчёты остаются рядом.</p>
          </div>
          <div class="rounded-2xl border border-brand-100 bg-white/78 p-4 shadow-soft backdrop-blur">
            <ShieldCheck :size="22" class="text-brand-700" />
            <p class="mt-3 text-sm font-semibold text-[#17223B]">Безопасный доступ</p>
            <p class="mt-1 text-sm leading-6 text-slate-500">Авторизация и права работают как раньше.</p>
          </div>
        </div>
      </section>

      <section class="w-full rounded-[24px] border border-brand-100 bg-white/82 p-6 shadow-[0_24px_70px_rgba(32,40,70,0.12)] backdrop-blur-xl sm:p-8">
        <div class="flex items-center gap-3 lg:hidden">
          <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_16px_36px_rgba(109,93,246,0.28)]">
            <Zap :size="23" fill="currentColor" />
          </span>
          <span class="text-xl font-bold text-[#17223B]">TrackNode</span>
        </div>

        <p class="mt-8 inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 lg:mt-0">Личный кабинет</p>
        <h1 class="mt-4 text-3xl font-bold text-[#17223B]">Вход в TrackNode</h1>
        <p class="mt-2 text-sm leading-6 text-slate-500">Управляйте сайтами, заявками, SEO и аналитикой из единой платформы.</p>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-2 block text-sm font-semibold text-[#17223B]">Электронная почта</label>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            class="form-control min-h-12"
          >
        </div>

        <div>
          <label class="mb-2 block text-sm font-semibold text-[#17223B]">Пароль</label>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            class="form-control min-h-12"
            placeholder="••••••••"
          >
        </div>

        <p v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ errorMessage }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="action-button-primary w-full"
        >
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>
      </section>
    </div>
  </div>
</template>
