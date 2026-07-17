<script setup>
import { computed, onMounted, ref } from 'vue'
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
const idempotencyKey = ref('')

const visibleTemplates = computed(() => templates.value)

async function loadCatalog(category = '') {
  loading.value = true
  error.value = ''
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
}

async function createSite() {
  if (!selectedTemplate.value || creating.value) return
  creating.value = true
  error.value = ''
  idempotencyKey.value = idempotencyKey.value || `${Date.now()}-${Math.random().toString(16).slice(2)}`
  try {
    const { data } = await createSiteFromTemplateRequest(
      {
        template_slug: selectedTemplate.value.slug,
        company_name: companyName.value,
      },
      { headers: { 'Idempotency-Key': idempotencyKey.value } },
    )
    siteStore.upsertSite(data)
    await router.replace(`/sites/${data.id}/sections`)
  } catch (requestError) {
    error.value = requestError?.response?.data?.company_name?.[0]
      || requestError?.response?.data?.template_slug?.[0]
      || requestError?.response?.data?.detail
      || 'Не удалось создать сайт.'
  } finally {
    creating.value = false
  }
}

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

    <p v-if="error" class="notice-error">{{ error }}</p>

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

    <section v-if="loading" class="empty-state">
      <span class="loading-dot" />
      <p>Загружаем шаблоны...</p>
    </section>

    <section v-else-if="!visibleTemplates.length" class="empty-state">
      <h2>Шаблоны пока не добавлены</h2>
      <p>Администратор может зарегистрировать существующий сайт как источник шаблона.</p>
    </section>

    <section v-else class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      <article v-for="template in visibleTemplates" :key="template.slug" class="site-card">
        <img
          :src="template.preview_image || '/favicon.svg'"
          alt=""
          class="h-44 w-full rounded-xl object-cover"
        >
        <div class="mt-4">
          <p class="eyebrow">{{ template.category?.name || 'Шаблон' }}</p>
          <h2 class="mt-2 text-xl font-bold text-[#17223B]">{{ template.name }}</h2>
          <p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">{{ template.description || 'Готовая структура сайта для быстрого старта.' }}</p>
        </div>
        <div class="mt-5 flex flex-wrap gap-2">
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
            <span>Название компании или сайта</span>
            <input v-model.trim="companyName" class="form-control" required maxlength="255" placeholder="Например: Волга Тур">
          </label>
          <div class="flex flex-col gap-2 sm:flex-row">
            <button type="submit" class="action-button-primary" :disabled="creating">
              <span v-if="creating" class="button-spinner" />
              {{ creating ? 'Создаём...' : 'Создать сайт' }}
            </button>
            <button type="button" class="action-button-secondary" :disabled="creating" @click="selectedTemplate = null">Отмена</button>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
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
</style>
