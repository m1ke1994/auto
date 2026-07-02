<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  ArrowRight,
  CalendarDays,
  Check,
  CircleAlert,
  Clock3,
  CreditCard,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  WalletCards,
} from '@lucide/vue'

import {
  miniSubscriptionCreatePayment,
  miniSubscriptionPlans,
  miniSubscriptionStatus,
} from '../api/mini'

const subscription = ref(null)
const plans = ref([])
const subscriptionLoading = ref(true)
const plansLoading = ref(true)
const subscriptionError = ref('')
const plansError = ref('')
const paymentError = ref('')
const payingPlanId = ref(null)
const activePeriod = ref(1)

const periodTabs = [
  { months: 1, label: '1 месяц' },
  { months: 6, label: '6 месяцев' },
  { months: 12, label: '12 месяцев' },
]

const currentPlan = computed(() => subscription.value?.plan || null)
const billingEnabled = computed(() => subscription.value?.billing_enabled !== false)
const visiblePlans = computed(() => (
  plans.value
    .filter((plan) => Number(plan?.period_months) === activePeriod.value)
    .sort((left, right) => Number(left?.sort_order || 0) - Number(right?.sort_order || 0))
))

const subscriptionPresentation = computed(() => {
  const data = subscription.value
  const paidUntil = data?.paid_until ? new Date(data.paid_until) : null
  const hasCurrentPeriod = paidUntil && !Number.isNaN(paidUntil.getTime()) && paidUntil > new Date()

  if (data?.is_trial && hasCurrentPeriod) {
    return {
      label: 'Пробный период',
      badgeClass: 'border-sky-200 bg-sky-50 text-sky-700',
      message: 'Пробный доступ к панели управления активен.',
    }
  }
  if (data?.status === 'active' && hasCurrentPeriod) {
    return {
      label: 'Активна',
      badgeClass: 'border-emerald-200 bg-emerald-50 text-emerald-700',
      message: 'Доступ к панели управления активен.',
    }
  }
  if (data?.status === 'expired' || (paidUntil && paidUntil <= new Date())) {
    return {
      label: 'Истекла',
      badgeClass: 'border-amber-200 bg-amber-50 text-amber-800',
      message: 'Для доступа к панели управления необходимо оплатить тариф.',
    }
  }
  return {
    label: 'Не оплачено',
    badgeClass: 'border-slate-200 bg-slate-100 text-slate-700',
    message: 'Для доступа к панели управления необходимо оплатить тариф.',
  }
})

function requestErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  return typeof detail === 'string' && detail.trim() ? detail : fallback
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

function formatPrice(value, currency = 'RUB') {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return '—'
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB',
    maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
  }).format(amount)
}

function periodLabel(days) {
  const months = Number(days?.period_months)
  if (months === 1) return '1 месяц'
  if (months === 6) return '6 месяцев'
  if (months === 12) return '12 месяцев'

  const duration = Number(days?.duration_days ?? days)
  if (!Number.isFinite(duration) || duration <= 0) return 'Срок не указан'
  if (duration === 30 || duration === 31) return '1 месяц'
  if ([180, 181, 182, 183].includes(duration)) return '6 месяцев'
  if (duration === 365 || duration === 366) return '12 месяцев'
  return `${duration} дней`
}

function discountPercent(plan) {
  const configuredDiscount = Number(plan?.discount_percent)
  if (Number.isFinite(configuredDiscount) && configuredDiscount > 0) return configuredDiscount

  const price = Number(plan?.price)
  const oldPrice = Number(plan?.old_price)
  if (!Number.isFinite(price) || !Number.isFinite(oldPrice) || oldPrice <= price || oldPrice <= 0) return 0
  return Math.round((1 - price / oldPrice) * 100)
}

function tabSaving(months) {
  const discount = plans.value
    .filter((plan) => Number(plan?.period_months) === months)
    .reduce((maximum, plan) => Math.max(maximum, discountPercent(plan)), 0)
  return discount ? `Скидка ${discount}%` : 'Без скидки'
}

function isCurrentPlan(plan) {
  return Number(currentPlan.value?.id) === Number(plan?.id)
}

async function loadSubscription() {
  subscriptionLoading.value = true
  subscriptionError.value = ''
  try {
    subscription.value = await miniSubscriptionStatus()
  } catch (error) {
    subscriptionError.value = requestErrorMessage(error, 'Не удалось загрузить статус подписки.')
  } finally {
    subscriptionLoading.value = false
  }
}

async function loadPlans() {
  plansLoading.value = true
  plansError.value = ''
  try {
    const data = await miniSubscriptionPlans()
    plans.value = Array.isArray(data) ? data : []
  } catch (error) {
    plansError.value = requestErrorMessage(error, 'Не удалось загрузить доступные тарифы.')
  } finally {
    plansLoading.value = false
  }
}

async function createPayment(plan) {
  if (!plan?.id || payingPlanId.value !== null) return
  paymentError.value = ''
  payingPlanId.value = plan.id
  try {
    const payment = await miniSubscriptionCreatePayment(plan.id)
    const redirectUrl = payment?.confirmation_url || payment?.checkout_url
    if (!redirectUrl) throw new Error('missing_confirmation_url')

    const target = new URL(redirectUrl, window.location.origin)
    if (!['http:', 'https:'].includes(target.protocol)) throw new Error('invalid_confirmation_url')
    window.location.assign(target.href)
  } catch (error) {
    if (error?.response?.status === 503) {
      paymentError.value = 'Оплата временно недоступна. Попробуйте позже или свяжитесь с администратором.'
    } else {
      paymentError.value = requestErrorMessage(error, 'Не удалось создать платёж. Попробуйте ещё раз.')
    }
  } finally {
    payingPlanId.value = null
  }
}

onMounted(() => {
  loadSubscription()
  loadPlans()
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Тариф и оплата</p>
        <h1>Оплата</h1>
        <p>Управляйте доступом к TrackNode и выберите подходящий период подписки.</p>
      </div>
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_16px_36px_rgba(109,93,246,0.28)]">
        <WalletCards :size="27" />
      </div>
    </header>

    <p v-if="!subscriptionLoading && subscription && !billingEnabled" class="notice-info" role="status">
      Оплата временно отключена. Доступные тарифы можно посмотреть, но создать платёж сейчас нельзя.
    </p>

    <section v-if="subscriptionLoading" class="surface" aria-busy="true">
      <div class="flex items-center gap-3 text-sm text-slate-500">
        <span class="button-spinner text-brand-600" aria-hidden="true" />
        Загружаем информацию о подписке…
      </div>
    </section>

    <section v-else-if="subscriptionError" class="notice-error" role="alert">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>{{ subscriptionError }}</span>
        <button type="button" class="action-button-secondary shrink-0" @click="loadSubscription">
          <RefreshCw :size="17" />
          Повторить
        </button>
      </div>
    </section>

    <section v-else class="surface overflow-hidden p-0 sm:p-0">
      <div class="grid lg:grid-cols-[1.35fr_1fr]">
        <div class="p-5 sm:p-7">
          <div class="flex flex-wrap items-center gap-3">
            <span class="status-badge" :class="subscriptionPresentation.badgeClass">
              {{ subscriptionPresentation.label }}
            </span>
            <span v-if="subscription?.access_allowed" class="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
              <ShieldCheck :size="15" />
              Доступ разрешён
            </span>
          </div>

          <h2 class="mt-5 text-2xl font-bold text-[#17223B]">{{ currentPlan?.name || 'Тариф не выбран' }}</h2>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{{ subscriptionPresentation.message }}</p>

          <div class="mt-6 grid gap-3 sm:grid-cols-3">
            <div class="rounded-2xl bg-slate-50 p-4">
              <div class="flex items-center gap-2 text-xs font-medium text-slate-500">
                <CalendarDays :size="16" /> Начало периода
              </div>
              <p class="mt-2 text-sm font-semibold text-slate-900">{{ formatDate(subscription?.started_at) }}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-4">
              <div class="flex items-center gap-2 text-xs font-medium text-slate-500">
                <CalendarDays :size="16" /> Доступ до
              </div>
              <p class="mt-2 text-sm font-semibold text-slate-900">{{ formatDate(subscription?.paid_until) }}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-4">
              <div class="flex items-center gap-2 text-xs font-medium text-slate-500">
                <Clock3 :size="16" /> Осталось
              </div>
              <p class="mt-2 text-sm font-semibold text-slate-900">
                {{ subscription?.days_remaining ? `${subscription.days_remaining} дн.` : '0 дней' }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex flex-col justify-center border-t border-brand-100 bg-gradient-to-br from-brand-50/90 to-white p-5 sm:p-7 lg:border-l lg:border-t-0">
          <CreditCard :size="28" class="text-brand-600" />
          <p class="mt-4 text-sm font-medium text-slate-500">Состояние оплаты</p>
          <p class="mt-1 text-xl font-bold text-[#17223B]">
            {{ subscription?.is_paid ? 'Тариф оплачен' : 'Оплата не подтверждена' }}
          </p>
          <p class="mt-2 text-sm leading-6 text-slate-600">После успешной оплаты доступ активируется автоматически.</p>
        </div>
      </div>
    </section>

    <p v-if="paymentError" class="notice-error" role="alert">{{ paymentError }}</p>

    <section>
      <div class="section-heading">
        <div>
          <h2>Доступные тарифы</h2>
          <p class="max-w-3xl">Выберите тариф под задачу вашего сайта. Можно начать с базового обслуживания или подключить расширенную аналитику, SEO и AI-рекомендации для роста.</p>
        </div>
      </div>

      <div class="mb-6 inline-grid w-full grid-cols-3 gap-1 rounded-2xl border border-brand-100 bg-white/85 p-1.5 shadow-soft sm:w-auto" role="tablist" aria-label="Период тарифа">
        <button
          v-for="tab in periodTabs"
          :id="`billing-period-tab-${tab.months}`"
          :key="tab.months"
          type="button"
          role="tab"
          class="min-w-0 rounded-xl px-3 py-2.5 text-center transition sm:min-w-36 sm:px-5"
          :class="activePeriod === tab.months ? 'bg-brand-600 text-white shadow-[0_10px_24px_rgba(109,93,246,0.25)]' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-800'"
          :aria-selected="activePeriod === tab.months"
          aria-controls="billing-period-panel"
          @click="activePeriod = tab.months"
        >
          <span class="block text-sm font-semibold">{{ tab.label }}</span>
          <span class="mt-0.5 block truncate text-[10px] font-medium opacity-75 sm:text-xs">{{ tabSaving(tab.months) }}</span>
        </button>
      </div>

      <div v-if="plansLoading" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3" aria-busy="true">
        <div v-for="index in 3" :key="index" class="surface h-72 animate-pulse bg-white/70" />
      </div>

      <div v-else-if="plansError" class="notice-error" role="alert">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>{{ plansError }}</span>
          <button type="button" class="action-button-secondary shrink-0" @click="loadPlans">
            <RefreshCw :size="17" /> Повторить
          </button>
        </div>
      </div>

      <div v-else-if="!visiblePlans.length" class="empty-state">
        <CircleAlert :size="28" class="text-brand-500" />
        <h2>Для выбранного периода тарифы не опубликованы</h2>
        <p>Когда администратор добавит активные тарифы, они появятся на этой вкладке.</p>
      </div>

      <div
        v-else
        id="billing-period-panel"
        class="grid items-stretch gap-5 lg:grid-cols-2"
        role="tabpanel"
        :aria-labelledby="`billing-period-tab-${activePeriod}`"
      >
        <article
          v-for="plan in visiblePlans"
          :key="plan.id"
          class="relative flex min-h-full flex-col overflow-hidden rounded-3xl border bg-white/92 p-5 shadow-soft transition hover:-translate-y-1 hover:shadow-[0_20px_52px_rgba(32,40,70,0.13)] sm:p-6"
          :class="plan.recommended ? 'border-brand-300 ring-1 ring-brand-200' : 'border-brand-100'"
        >
          <div v-if="plan.recommended" class="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-brand-600 px-2.5 py-1 text-xs font-semibold text-white">
            <Sparkles :size="13" /> Рекомендуем
          </div>
          <div class="pr-24">
            <p class="text-xs font-semibold uppercase tracking-wide text-brand-600">{{ periodLabel(plan) }}</p>
            <h3 class="mt-2 text-xl font-bold text-[#17223B]">{{ plan.name }}</h3>
          </div>
          <p v-if="plan.short_description || plan.description" class="mt-3 text-sm leading-6 text-slate-600">{{ plan.short_description || plan.description }}</p>

          <div class="mt-5 flex flex-wrap items-end gap-x-3 gap-y-1">
            <span class="text-3xl font-bold tracking-tight text-[#17223B]">{{ formatPrice(plan.price, plan.currency) }}</span>
            <span v-if="plan.old_price && discountPercent(plan)" class="pb-1 text-sm text-slate-400 line-through">{{ formatPrice(plan.old_price, plan.currency) }}</span>
            <span v-if="discountPercent(plan)" class="mb-1 rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
              Скидка {{ discountPercent(plan) }}%
            </span>
          </div>

          <ul v-if="Array.isArray(plan.features) && plan.features.length" class="mt-5 space-y-3">
            <li v-for="feature in plan.features" :key="feature" class="flex gap-2.5 text-sm leading-5 text-slate-700">
              <span class="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700">
                <Check :size="13" stroke-width="2.5" />
              </span>
              {{ feature }}
            </li>
          </ul>

          <button
            type="button"
            class="action-button-primary mt-6 w-full md:mt-auto"
            :disabled="!billingEnabled || payingPlanId !== null"
            @click="createPayment(plan)"
          >
            <span v-if="payingPlanId === plan.id" class="button-spinner" aria-hidden="true" />
            <CreditCard v-else :size="18" />
            <span v-if="payingPlanId === plan.id">Создаём платёж…</span>
            <span v-else-if="!billingEnabled">Оплата недоступна</span>
            <span v-else>{{ isCurrentPlan(plan) ? 'Продлить доступ' : 'Выбрать тариф' }}</span>
            <ArrowRight v-if="payingPlanId !== plan.id && billingEnabled" :size="17" />
          </button>
        </article>
      </div>
    </section>
  </div>
</template>
