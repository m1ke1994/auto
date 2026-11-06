// Pure UI formatting. No requests, database writes, or modification of API payloads.
const count = value => {
  if (value === null || value === undefined || value === '') return '—'
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed.toLocaleString('ru-RU') : '—'
}

export function overviewMetrics(summary, { showLeads = true } = {}) {
  if (!summary) return []
  const metrics = [
    { label: 'Посетители', value: count(summary.visitors_unique), sub: 'Разные посетители за 14 дней' },
    { label: 'Просмотры страниц', value: count(summary.pageviews_count), sub: 'Сколько страниц открыли' },
  ]
  if (showLeads) {
    const conversion = summary.conversion
    const numericConversion = Number(conversion)
    metrics.push(
      { label: 'Заявки', value: count(summary.leads_count), sub: 'Обращения за 14 дней' },
      { label: 'Конверсия в заявку', value: conversion == null || conversion === '' || !Number.isFinite(numericConversion) ? '—' : numericConversion.toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + '%', sub: 'Доля посетителей, оставивших заявку' },
    )
  }
  return metrics
}

export function overviewMessage(summary, { showLeads = true, isActive = true } = {}) {
  if (isActive === false) return 'Сайт отмечен как отключённый. Проверьте его настройки перед оценкой статистики.'
  if (!summary) return 'Статистика пока не получена.'
  const visitors = Number(summary.visitors_unique)
  if (!Number.isFinite(visitors) || summary.visitors_unique == null) return 'Число посетителей пока не рассчитано.'
  if (visitors === 0) return 'За последние 14 дней посещений не зафиксировано. Проверьте адрес сайта и подключение аналитики.'
  if (!showLeads) return 'Посмотрите, какие страницы чаще открывают посетители, в разделе «Посмотреть посещения».'
  const leads = Number(summary.leads_count)
  if (!Number.isFinite(leads) || summary.leads_count == null) return 'Данные о заявках пока не получены. Для проверки откройте раздел заявок.'
  if (leads === 0) return 'Посетители заходили на сайт, но заявок за 14 дней нет. Проверьте форму обратной связи и кнопки связи.'
  return 'За последние 14 дней на сайте были посетители и заявки. Откройте раздел заявок, чтобы проверить новые обращения.'
}
