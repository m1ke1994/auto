<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, Plus, RefreshCw } from '@lucide/vue'

import { createSiteFromTemplateRequest, getSiteTemplateCatalogRequest } from '../api/site'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const siteStore = useSiteStore()

const loading = ref(false)
const creating = ref(false)
const error = ref('')
const categories = ref([])
const templates = ref([])
const activeCategory = ref('')
const selectedTemplate = ref(null)
const companyName = ref('')
const siteName = ref('')
const idempotencyKey = ref('')
const success = ref('')

const visibleTemplates = computed(() => templates.value)

async function loadCatalog(category = '') {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await getSiteTemplateCatalogRequest(category)
    categories.value = Array.isArray(data.categories) ? data.categories : []
    templates.value = Array.isArray(data.templates) ? data.templates : []
  } catch (requestError) {
    error.value = requestError?.response?.data?.detail || 'Не удалось загрузить каталог шаблонов.'
  } finally {
    loading.value = false
  }
}

function selectCategory(slug) {
  activeCategory.value = slug
  loadCatalog(slug)
}

function chooseTemplate(template) {
  selectedTemplate.value = template
  companyName.value = ''
  siteName.value = ''
  idempotencyKey.value = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  error.value = ''
  success.value = ''
}

async function createSite() {
  if (!selectedTemplate.value || creating.value || !companyName.value || !siteName.value) return
  creating.value = true
  error.value = ''
  success.value = ''
  idempotencyKey.value = idempotencyKey.value || `${Date.now()}-${Math.random().toString(16).slice(2)}`
  try {
    const { data } = await createSiteFromTemplateRequest(
      {
        template_slug: selectedTemplate.value.slug,
        company_name: companyName.value,
        site_name: siteName.value,
        idempotency_key: idempotencyKey.value,
      },
      { headers: { 'Idempotency-Key': idempotencyKey.value } },
    )
    siteStore.upsertSite(data)
    await siteStore.fetchSites()
    siteStore.selectSite(data.id)
    selectedTemplate.value = null
    success.value = 'Сайт успешно создан'
    await router.replace(data.editor_url || `/sites/${data.id}/sections`)
  } catch (requestError) {
    idempotencyKey.value = `${Date.now()}-${Math.random().toString(16).slice(2)}`
    error.value = creationErrorMessage(requestError)
  } finally {
    creating.value = false
  }
}

function creationErrorMessage(requestError) {
  const status = requestError?.response?.status
  const data = requestError?.response?.data || {}
  if (data?.code === 'subscription_required') return data.detail || 'Для создания нового сайта необходимо выбрать тариф.'
  if (status === 401) return 'Сессия истекла. Войдите снова.'
  if (status === 403) return 'Недостаточно прав для создания сайта.'
  if (status === 404) return 'Шаблон не найден.'
  if (status === 409) return 'Такой запрос уже был обработан.'
  if (status >= 500) return 'Ошибка сервера при создании сайта.'
  return data?.company_name?.[0]
    || data?.site_name?.[0]
    || data?.template_slug?.[0]
    || data?.detail
    || 'Не удалось создать сайт. Повторите попытку.'
}

function fallbackClass(template) {
  const slug = String(template?.slug || '')
  if (slug.includes('expert')) return 'expert'
  if (slug.includes('country') || slug.includes('retreat')) return 'tourism'
  return 'business'
}

watch(companyName, (value, oldValue) => {
  if (!siteName.value || siteName.value === oldValue) siteName.value = value
})

onMounted(() => loadCatalog())
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Новый сайт</p>
        <h1>Создать сайт из шаблона</h1>
        <p>Выберите готовую структуру, укажите название компании и настройте сайт в обычном редакторе.</p>
      </div>
      <button type="button" class="icon-button" aria-label="Обновить каталог" @click="loadCatalog(activeCategory)">
        <RefreshCw :size="18" />
      </button>
    </header>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <p v-if="success" class="notice-success" role="status">{{ success }}</p>

    <nav class="surface flex flex-wrap gap-2 p-3">
      <button type="button" class="template-category" :class="{ active: !activeCategory }" @click="selectCategory('')">Все</button>
      <button
        v-for="category in categories"
        :key="category.slug"
        type="button"
        class="template-category"
        :class="{ active: activeCategory === category.slug }"
        @click="selectCategory(category.slug)"
      >
        {{ category.name }}
      </button>
    </nav>

    <section v-if="loading" class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      <article v-for="index in 3" :key="index" class="template-card skeleton-template-card">
        <div class="template-skeleton-media" />
        <div class="template-skeleton-line short" />
        <div class="template-skeleton-line" />
        <div class="template-skeleton-line mid" />
        <div class="template-skeleton-actions" />
      </article>
    </section>

    <section v-else-if="!visibleTemplates.length" class="empty-state">
      <h2>Шаблоны пока не добавлены</h2>
      <p>Администратор может зарегистрировать существующий сайт как источник шаблона.</p>
      <button v-if="error" type="button" class="action-button-secondary mt-3" @click="loadCatalog(activeCategory)">Повторить</button>
    </section>

    <section v-else class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      <article v-for="template in visibleTemplates" :key="template.slug" class="template-card site-card">
        <img
          v-if="template.preview_image"
          :src="template.preview_image || '/favicon.svg'"
          alt=""
          class="template-preview-image"
        >
        <div v-else class="template-preview-fallback" :class="fallbackClass(template)">
          <span>{{ template.category?.name || 'Шаблон' }}</span>
        </div>
        <div class="template-card-body">
          <p class="eyebrow">{{ template.category?.name || 'Шаблон' }}</p>
          <h2 class="mt-2 text-xl font-bold text-[#17223B]">{{ template.name }}</h2>
          <p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">{{ template.description || 'Готовая структура сайта для быстрого старта.' }}</p>
        </div>
        <div class="template-card-actions">
          <a
            :href="`/api/public/sites/${template.source_site_slug}/html/`"
            target="_blank"
            rel="noreferrer"
            class="action-button-secondary"
          >
            <Eye :size="17" />
            Предпросмотр
          </a>
          <button type="button" class="action-button-primary" @click="chooseTemplate(template)">
            <Plus :size="17" />
            Выбрать шаблон
          </button>
        </div>
      </article>
    </section>

    <Teleport to="body">
      <div v-if="selectedTemplate" class="template-modal" @click.self="selectedTemplate = null">
        <form class="template-dialog" @submit.prevent="createSite">
          <p class="eyebrow">Создание сайта</p>
          <h2>{{ selectedTemplate.name }}</h2>
          <label>
            <span>Название компании</span>
            <input v-model.trim="companyName" class="form-control" required maxlength="255" placeholder="Например: Волга Тур">
          </label>
          <label>
            <span>Название сайта</span>
            <input v-model.trim="siteName" class="form-control" required maxlength="255" placeholder="Например: Новый сайт">
          </label>
          <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
          <div class="flex flex-col gap-2 sm:flex-row">
            <button type="submit" class="action-button-primary" :disabled="creating || !companyName || !siteName">
              <span v-if="creating" class="button-spinner" />
              {{ creating ? 'Создаём сайт из шаблона...' : 'Создать сайт' }}
            </button>
            <button type="button" class="action-button-secondary" :disabled="creating" @click="selectedTemplate = null">Отмена</button>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.template-card {
  display: flex;
  min-height: 31rem;
  flex-direction: column;
}

.template-preview-image,
.template-preview-fallback,
.template-skeleton-media {
  height: 11rem;
  width: 100%;
  border-radius: 0.75rem;
}

.template-preview-image {
  object-fit: cover;
}

.template-preview-fallback {
  display: grid;
  place-items: end start;
  overflow: hidden;
  padding: 1rem;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #6d5df6, #17223b);
}

.template-preview-fallback.expert {
  background: linear-gradient(135deg, #10b981, #17223b);
}

.template-preview-fallback.tourism {
  background: linear-gradient(135deg, #0f766e, #84cc16);
}

.template-card-body {
  display: flex;
  min-height: 12.5rem;
  flex: 1;
  flex-direction: column;
  margin-top: 1rem;
}

.template-card-body h2 {
  line-height: 1.25;
}

.template-card-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: auto;
  padding-top: 1.25rem;
}

.template-card-actions > * {
  flex: 1 1 0;
  white-space: nowrap;
}

.skeleton-template-card {
  pointer-events: none;
}

.template-skeleton-media,
.template-skeleton-line,
.template-skeleton-actions {
  position: relative;
  overflow: hidden;
  background: #eef2ff;
}

.template-skeleton-line {
  height: 1rem;
  margin-top: 1rem;
  border-radius: 999px;
}

.template-skeleton-line.short {
  width: 34%;
}

.template-skeleton-line.mid {
  width: 68%;
}

.template-skeleton-actions {
  height: 2.75rem;
  margin-top: auto;
  border-radius: 1rem;
}

.template-skeleton-media::after,
.template-skeleton-line::after,
.template-skeleton-actions::after {
  position: absolute;
  inset: 0;
  content: "";
  transform: translateX(-100%);
  animation: template-shimmer 1.4s infinite;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.7), transparent);
}

@keyframes template-shimmer {
  100% {
    transform: translateX(100%);
  }
}

.template-category {
  min-height: 2.4rem;
  border: 1px solid rgba(109, 93, 246, 0.14);
  border-radius: 0.8rem;
  background: #fff;
  color: #475569;
  padding: 0 0.9rem;
  font-size: 0.875rem;
  font-weight: 700;
}

.template-category.active {
  border-color: transparent;
  background: #6d5df6;
  color: #fff;
}

.template-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.42);
}

.template-dialog {
  display: grid;
  width: min(100%, 32rem);
  gap: 1rem;
  border-radius: 1.5rem;
  background: #fff;
  padding: 1.5rem;
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.24);
}

.template-dialog h2 {
  margin: 0;
  color: #17223b;
  font-size: 1.35rem;
  font-weight: 800;
}

.template-dialog label {
  display: grid;
  gap: 0.5rem;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 700;
}

@media (max-width: 640px) {
  .template-card-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .template-card-actions > * {
    width: 100%;
  }
}
</style>
