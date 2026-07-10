const CATEGORY_ALIASES = {
  conversion: 'Конверсия', seo: 'SEO', content: 'Контент', engagement: 'Вовлечённость',
  performance: 'Производительность', mobile: 'Мобильная версия', traffic: 'Источники трафика',
  forms: 'Формы и заявки', leads: 'Формы и заявки', behavior: 'Поведение пользователей',
  ux: 'Поведение пользователей', technical: 'Технические ошибки', errors: 'Технические ошибки',
  general: 'Общие рекомендации', combined: 'Общие рекомендации',
}

const PRIORITY_ALIASES = {
  critical: 'high', high: 'high', very_important: 'high', urgent: 'high',
  medium: 'medium', recommended: 'medium', normal: 'medium',
  low: 'low', later: 'low', optional: 'low',
}

export const priorityMeta = {
  high: { label: 'Высокий приоритет', short: 'Высокий', order: 0 },
  medium: { label: 'Средний приоритет', short: 'Средний', order: 1 },
  low: { label: 'Низкий приоритет', short: 'Низкий', order: 2 },
  neutral: { label: 'Без приоритета', short: 'Не указан', order: 3 },
}

export function plainMarkdown(value) {
  if (typeof value !== 'string') return ''
  return value
    .replace(/```[\s\S]*?```/g, (block) => block.replace(/```[\w-]*\n?/g, '').replace(/```/g, ''))
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^>\s?/gm, '')
    .replace(/[*_~`]/g, '')
    .trim()
}

function firstText(...values) {
  return plainMarkdown(values.find((value) => typeof value === 'string' && value.trim()) || '')
}

function textList(value) {
  if (Array.isArray(value)) return value.map((item) => typeof item === 'string' ? plainMarkdown(item) : firstText(item?.label, item?.text, item?.title, item?.value)).filter(Boolean)
  if (typeof value === 'string') return value.split(/\n|;/).map((item) => plainMarkdown(item.replace(/^[-•\d.)\s]+/, ''))).filter(Boolean)
  return []
}

export function normalizeCategory(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/[\s-]+/g, '_')
  if (CATEGORY_ALIASES[raw]) return CATEGORY_ALIASES[raw]
  if (/form|lead|заяв/.test(raw)) return 'Формы и заявки'
  if (/mobile|device|мобил/.test(raw)) return 'Мобильная версия'
  if (/speed|perform|скорост/.test(raw)) return 'Производительность'
  if (/traffic|source|трафик|источник/.test(raw)) return 'Источники трафика'
  if (/error|ошиб/.test(raw)) return 'Технические ошибки'
  if (/behav|engage|поведен|вовлеч/.test(raw)) return 'Поведение пользователей'
  if (/content|контент/.test(raw)) return 'Контент'
  if (/seo|поиск/.test(raw)) return 'SEO'
  if (/convert|конверс/.test(raw)) return 'Конверсия'
  return 'Общие рекомендации'
}

export function normalizePriority(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/[\s-]+/g, '_')
  return PRIORITY_ALIASES[raw] || 'neutral'
}

function normalizeOne(item, index) {
  if (typeof item === 'string') {
    return { id: `legacy-${index}`, title: 'Общая рекомендация', description: plainMarkdown(item), details: '', priority: 'neutral', category: 'Общие рекомендации', effect: '', evidence: [], metrics: [], actions: [] }
  }
  const actions = textList(item?.actions || item?.steps || item?.checklist)
  const actionText = firstText(item?.action, item?.recommendation, item?.what_to_do, item?.solution, item?.details)
  if (!actions.length && actionText) actions.push(...textList(actionText))
  return {
    id: String(item?.id || `recommendation-${index}`),
    title: firstText(item?.title, item?.name, item?.heading) || 'Рекомендация по развитию сайта',
    description: firstText(item?.problem, item?.description, item?.why_important, item?.summary),
    details: firstText(item?.details, item?.recommendation, item?.action, item?.what_to_do),
    priority: normalizePriority(item?.priority),
    category: normalizeCategory(item?.category || item?.type || item?.group),
    effect: firstText(item?.benefit, item?.expected_impact, item?.expected_result, item?.impact),
    evidence: textList(item?.evidence || item?.reasons || item?.basis),
    metrics: textList(item?.metrics || item?.related_metrics || item?.signals),
    actions,
  }
}

export function normalizeResult(result) {
  if (!result) return { summary: '', score: null, recommendations: [] }
  if (typeof result === 'string') return { summary: '', score: null, recommendations: [normalizeOne(result, 0)] }
  if (Array.isArray(result)) return { summary: '', score: null, recommendations: result.map(normalizeOne) }
  let source = result.recommendations
  if (typeof source === 'string') source = [source]
  if (!Array.isArray(source)) source = []
  if (!source.length) {
    const legacy = firstText(result.text, result.content, result.message, result.answer)
    if (legacy) source = [legacy]
  }
  const rawPotential = result.improvement_potential ?? result.potential ?? null
  return {
    summary: firstText(result.summary, result.overview, result.conclusion),
    score: Number.isFinite(Number(result.score)) ? Number(result.score) : null,
    potential: ['string', 'number'].includes(typeof rawPotential) ? rawPotential : null,
    recommendations: source.map(normalizeOne).sort((a, b) => priorityMeta[a.priority].order - priorityMeta[b.priority].order),
  }
}

export function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('ru-RU', { dateStyle: 'medium', timeStyle: 'short' })
}
