<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ExternalLink, Monitor, RefreshCw, Smartphone, Tablet, Wand2 } from '@lucide/vue'

import SiteGenerationProgress from '../components/SiteGenerationProgress.vue'
import { generateSiteFromCategoryRequest, getSiteTemplateCatalogRequest, regenerateSiteDesignRequest } from '../api/site'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const siteStore = useSiteStore()

const loading = ref(false)
const submitting = ref(false)
const regenerating = ref(false)
const phase = ref('form')
const error = ref('')
const categories = ref([])
const selectedCategoryId = ref(null)
const idempotencyKey = ref('')
const regenerateKey = ref('')
const result = ref(null)
const previewMode = ref('desktop')
const form = reactive({ company_name: '', description: '', phone: '', email: '', city: '' })

const selectedCategory = computed(() => categories.value.find((item) => item.id === selectedCategoryId.value))
const canSubmit = computed(() => selectedCategoryId.value && form.company_name.trim() && !submitting.value)
const previewWidth = computed(() => ({ desktop: '100%', tablet: '768px', mobile: '390px' }[previewMode.value]))
const currentTemplateId = computed(() => result.value?.selected_template?.id)
const previewUrl = computed(() => result.value?.preview_url || '')

function uuid() {
  return globalThis.crypto?.randomUUID ? globalThis.crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function loadCatalog() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await getSiteTemplateCatalogRequest()
    categories.value = Array.isArray(data.categories) ? data.categories : []
    if (!selectedCategoryId.value && categories.value.length) selectedCategoryId.value = categories.value[0].id
  } catch (requestError) {
    error.value = responseError(requestError, 'Не удалось загрузить категории.')
  } finally {
    loading.value = false
  }
}

async function submitGenerate({ retry = false } = {}) {
  if (!canSubmit.value && !retry) return
  if (submitting.value) return
  submitting.value = true
  phase.value = 'progress'
  error.value = ''
  if (!idempotencyKey.value || !retry) idempotencyKey.value = uuid()
  try {
    const { data } = await generateSiteFromCategoryRequest(
      { category_id: selectedCategoryId.value, ...form, idempotency_key: idempotencyKey.value },
      { headers: { 'Idempotency-Key': idempotencyKey.value } },
    )
    result.value = data
    siteStore.upsertSite(data.site)
    await siteStore.fetchSites()
    siteStore.selectSite(data.site.id)
    phase.value = 'result'
  } catch (requestError) {
    error.value = responseError(requestError, 'Не удалось создать сайт. Повторите попытку.')
    phase.value = 'form'
  } finally {
    submitting.value = false
  }
}

async function regenerateDesign() {
  if (!result.value?.site?.id || regenerating.value) return
  regenerating.value = true
  phase.value = 'progress'
  error.value = ''
  regenerateKey.value = uuid()
  try {
    const { data } = await regenerateSiteDesignRequest(
      result.value.site.id,
      { exclude_template_ids: currentTemplateId.value ? [currentTemplateId.value] : [], idempotency_key: regenerateKey.value },
      { headers: { 'Idempotency-Key': regenerateKey.value } },
    )
    result.value = data
    phase.value = 'result'
  } catch (requestError) {
    error.value = responseError(requestError, 'Не удалось подобрать другой дизайн.')
    phase.value = 'result'
  } finally {
    regenerating.value = false
  }
}

function responseError(requestError, fallback) {
  const data = requestError?.response?.data || {}
  if (data.code === 'category_has_no_templates') return 'Для выбранной категории пока нет доступных дизайнов.'
  if (data.code === 'no_alternative_templates') return 'В этой категории пока нет другого доступного дизайна.'
  if (Array.isArray(data.detail)) return data.detail.join(' ')
  if (typeof data.detail === 'string') return data.detail
  return fallback
}

onMounted(loadCatalog)
</script>

<template>
  <SiteGenerationProgress v-if="phase === 'progress'" active />

  <div v-else-if="phase === 'result' && result" class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Готово</p>
        <h1>Ваш сайт готов</h1>
        <p>Проверьте черновик в предпросмотре, откройте редактор или подберите другой дизайн в той же категории.</p>
      </div>
      <button type="button" class="action-button-secondary" @click="router.push('/dashboard')">
        <ArrowLeft :size="17" />
        В личный кабинет
      </button>
    </header>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>

    <section class="surface result-toolbar">
      <div class="device-tabs" role="group" aria-label="Размер предпросмотра">
        <button type="button" :class="{ active: previewMode === 'desktop' }" @click="previewMode = 'desktop'"><Monitor :size="17" />Компьютер</button>
        <button type="button" :class="{ active: previewMode === 'tablet' }" @click="previewMode = 'tablet'"><Tablet :size="17" />Планшет</button>
        <button type="button" :class="{ active: previewMode === 'mobile' }" @click="previewMode = 'mobile'"><Smartphone :size="17" />Телефон</button>
      </div>
      <div class="result-actions">
        <button type="button" class="action-button-primary" @click="router.push(result.editor_url)">
          <ExternalLink :size="17" />
          Редактировать сайт
        </button>
        <button type="button" class="action-button-secondary" :disabled="regenerating" @click="regenerateDesign">
          <RefreshCw :size="17" :class="{ spinning: regenerating }" />
          Выбрать другой дизайн
        </button>
      </div>
    </section>

    <section class="preview-stage">
      <iframe :src="previewUrl" title="Предпросмотр сайта" :style="{ width: previewWidth }" />
    </section>
  </div>

  <div v-else class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Новый сайт</p>
        <h1>Создать сайт</h1>
        <p>Выберите категорию бизнеса, заполните данные компании, и TrackNode подберет подходящий опубликованный дизайн.</p>
      </div>
      <button type="button" class="icon-button" aria-label="Обновить категории" @click="loadCatalog">
        <RefreshCw :size="18" />
      </button>
    </header>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>

    <section class="surface create-grid">
      <div>
        <h2>Категория бизнеса</h2>
        <div v-if="loading" class="category-skeleton" />
        <div v-else class="category-list">
          <button
            v-for="category in categories"
            :key="category.id"
            type="button"
            class="category-button"
            :class="{ active: selectedCategoryId === category.id }"
            @click="selectedCategoryId = category.id"
          >
            {{ category.name }}
          </button>
        </div>
      </div>

      <form class="company-form" @submit.prevent="submitGenerate()">
        <p v-if="selectedCategory" class="eyebrow">Выбрано: {{ selectedCategory.name }}</p>
        <label>Название компании<input v-model.trim="form.company_name" class="form-control" maxlength="255" required placeholder="Например: СтройДом"></label>
        <label>Короткое описание<textarea v-model.trim="form.description" class="form-control" rows="3" placeholder="Чем занимается компания"></textarea></label>
        <div class="form-row">
          <label>Телефон<input v-model.trim="form.phone" class="form-control" maxlength="100" placeholder="+7 900 000-00-00"></label>
          <label>Email<input v-model.trim="form.email" class="form-control" maxlength="255" type="email" placeholder="example@example.com"></label>
        </div>
        <label>Город<input v-model.trim="form.city" class="form-control" maxlength="120" placeholder="Москва"></label>
        <div class="form-actions">
          <button type="submit" class="action-button-primary" :disabled="!canSubmit">
            <Wand2 :size="17" />
            {{ submitting ? 'Создаем сайт...' : 'Создать сайт' }}
          </button>
          <button v-if="idempotencyKey && error" type="button" class="action-button-secondary" :disabled="submitting" @click="submitGenerate({ retry: true })">
            Повторить
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<style scoped>
.create-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 1.5rem;
}

.create-grid h2 {
  margin: 0 0 1rem;
  color: #17223b;
  font-size: 1.2rem;
  font-weight: 850;
}

.category-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.category-button {
  min-height: 2.6rem;
  border: 1px solid rgba(101, 71, 232, 0.18);
  border-radius: 0.8rem;
  background: #fff;
  padding: 0 1rem;
  color: #475569;
  font-size: 0.9rem;
  font-weight: 750;
}

.category-button.active {
  border-color: transparent;
  background: #6547e8;
  color: #fff;
}

.category-skeleton {
  height: 7rem;
  border-radius: 1rem;
  background: linear-gradient(90deg, #eef2ff, #f8fafc, #eef2ff);
}

.company-form {
  display: grid;
  gap: 1rem;
}

.company-form label {
  display: grid;
  gap: 0.45rem;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 750;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.form-actions,
.result-actions,
.result-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.result-toolbar {
  justify-content: space-between;
}

.device-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  border-radius: 0.9rem;
  background: #f1f5f9;
  padding: 0.35rem;
}

.device-tabs button {
  display: inline-flex;
  min-height: 2.35rem;
  align-items: center;
  gap: 0.4rem;
  border-radius: 0.7rem;
  padding: 0 0.85rem;
  color: #475569;
  font-weight: 750;
}

.device-tabs button.active {
  background: #fff;
  color: #17223b;
  box-shadow: 0 8px 20px rgba(32, 40, 70, 0.08);
}

.preview-stage {
  overflow-x: auto;
  border-radius: 1rem;
  background: #e2e8f0;
  padding: 1rem;
}

.preview-stage iframe {
  display: block;
  min-width: 320px;
  max-width: 100%;
  height: 74vh;
  margin: 0 auto;
  border: 0;
  border-radius: 0.75rem;
  background: #fff;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .create-grid,
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
