const MAIN_KEYS = [
  'id',
  'slug',
  'key',
  'code',
  'title',
  'name',
  'label',
  'month',
  'year',
  'date',
  'weekday',
  'subtitle',
  'eyebrow',
  'tag',
  'brand',
]

const CONTENT_KEYS = [
  'text',
  'description',
  'content',
  'intro',
  'body',
  'image',
  'avatar',
  'photo',
  'video',
  'poster',
  'gallery',
  'background',
  'src',
  'alt',
]

const PARAMETER_KEYS = [
  'price',
  'duration',
  'time',
  'order',
  'rating',
  'type',
  'format',
  'category',
  'color',
  'href',
  'to',
  'url',
  'link',
  'active',
  'visible',
  'show',
  'enabled',
  'number',
  'phone',
  'email',
]

const GROUPS = [
  { id: 'main', title: 'Основное', description: 'ID, slug, название и ключевые подписи.' },
  { id: 'content', title: 'Контент', description: 'Тексты, описания и медиа.' },
  { id: 'parameters', title: 'Параметры', description: 'Порядок, цена, формат, ссылки и переключатели.' },
  { id: 'lists', title: 'Карточки и списки', description: 'Повторяемые элементы этой секции.' },
  { id: 'other', title: 'Дополнительно', description: 'Остальные поля схемы.' },
]

const ROW_ENTITY_BY_LABEL = [
  [/отзыв/i, 'Отзыв'],
  [/услуг|формат|карточ/i, 'Карточка'],
  [/распис|месяц/i, 'Месяц'],
  [/дн(и|ь|я)/i, 'День'],
  [/событ/i, 'Событие'],
  [/стат/i, 'Статья'],
  [/новост/i, 'Новость'],
  [/страниц/i, 'Страница'],
  [/пункт/i, 'Пункт'],
  [/ссыл/i, 'Ссылка'],
  [/этап|процесс/i, 'Этап'],
  [/изображ|фото|галере/i, 'Изображение'],
]

function lower(value) {
  return String(value || '').toLowerCase()
}

function includesAny(value, keys) {
  const source = lower(value)
  return keys.some((key) => source.includes(key))
}

export function visibleFields(fields = []) {
  return Array.isArray(fields) ? fields.filter((field) => !field?.hidden) : []
}

export function fieldGroupId(field) {
  const key = lower(field?.key)
  const label = lower(field?.label)
  const type = lower(field?.type)
  const target = `${key} ${label}`

  if (type === 'repeater') return 'lists'
  if (includesAny(target, MAIN_KEYS)) return 'main'
  if (type === 'textarea' || ['image', 'video', 'media'].includes(type) || includesAny(target, CONTENT_KEYS)) return 'content'
  if (['number', 'boolean', 'select'].includes(type) || includesAny(target, PARAMETER_KEYS)) return 'parameters'
  return 'other'
}

export function groupFields(fields = []) {
  const groups = GROUPS.map((group) => ({ ...group, fields: [] }))

  for (const field of visibleFields(fields)) {
    const group = groups.find((item) => item.id === fieldGroupId(field))
    const targetGroup = group || groups[groups.length - 1]
    targetGroup.fields.push(field)
  }

  return groups.filter((group) => group.fields.length)
}

export function countRepeaterItems(content = {}) {
  if (!content || typeof content !== 'object') return 0

  return Object.values(content).reduce((sum, value) => {
    if (Array.isArray(value)) return sum + value.length
    return sum
  }, 0)
}

export function elementCountLabel(count) {
  const value = Number(count || 0)
  const mod10 = value % 10
  const mod100 = value % 100
  const noun = mod10 === 1 && mod100 !== 11
    ? 'элемент'
    : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)
      ? 'элемента'
      : 'элементов'

  return `${value} ${noun}`
}

export function sectionTypeLabel(section = {}) {
  return section.section_type || section.component_key || section.key || 'section'
}

export function rowEntityLabel(field = {}) {
  const label = String(field.label || field.key || '').trim()
  const match = ROW_ENTITY_BY_LABEL.find(([pattern]) => pattern.test(label))
  return match?.[1] || 'Элемент'
}

export function rowTitle(row = {}) {
  if (!row || typeof row !== 'object') return ''

  const preferredKeys = [
    'title',
    'name',
    'label',
    'slug',
    'key',
    'id',
    'event_name',
    'month',
    'date',
    'time_start',
  ]

  for (const key of preferredKeys) {
    const value = row[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim()
    }
  }

  return ''
}

export function rowSummary(field, row, index) {
  const title = rowTitle(row)
  const fallback = row?.slug || row?.key || row?.id || ''
  const suffix = title || fallback
  return suffix ? `${rowEntityLabel(field)} ${index + 1} — ${suffix}` : `${rowEntityLabel(field)} ${index + 1}`
}

export function fieldTypeLabel(field = {}) {
  return {
    text: 'Текст',
    textarea: 'Большой текст',
    image: 'Изображение',
    video: 'Видео',
    media: 'Медиа',
    number: 'Число',
    boolean: 'Переключатель',
    select: 'Список',
    repeater: 'Список элементов',
  }[field.type] || 'Поле'
}
