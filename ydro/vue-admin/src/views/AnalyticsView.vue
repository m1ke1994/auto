<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  BarChart3,
  CircleAlert,
  Copy,
  FileText,
  Filter,
  Flame,
  Funnel,
  Gauge,
  KeyRound,
  ListVideo,
  MonitorSmartphone,
  MousePointerClick,
  Play,
  RefreshCw,
  Route,
  ScrollText,
  Sparkles,
} from '@lucide/vue'

import {
  getSiteAnalyticsSectionRequest,
  getSiteAnalyticsSessionRequest,
  getSiteAnalyticsSummaryRequest,
} from '../api/analytics'
import AnalyticsInfoBlock from '../components/AnalyticsInfoBlock.vue'
import AnalyticsInsightBlock from '../components/AnalyticsInsightBlock.vue'
import AnalyticsRecommendationCard from '../components/AnalyticsRecommendationCard.vue'
import AnalyticsSummaryCard from '../components/AnalyticsSummaryCard.vue'
import DashboardStats from '../components/DashboardStats.vue'
import EmptyAnalyticsState from '../components/EmptyAnalyticsState.vue'
import MetricHelpTooltip from '../components/MetricHelpTooltip.vue'
import MetricStatusBadge from '../components/MetricStatusBadge.vue'
import WhatToDoNextBlock from '../components/WhatToDoNextBlock.vue'
import { refreshSiteTrackingKeyRequest } from '../api/site'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const loading = ref(false)
const sectionLoading = ref(false)
const sessionLoading = ref(false)
const error = ref('')
const success = ref('')
const summary = ref(null)
const sectionData = ref({})
const sessionDetail = ref(null)
const sessionDetailBlock = ref(null)
const activeTab = ref('overview')
const days = ref(14)
const includeBots = ref(false)
const action = ref('')
const pageFilter = ref('')
const deviceFilter = ref('all')
const eventTypeFilter = ref('')

const siteId = computed(() => Number(route.params.siteId))
const trackerScript = computed(() => summary.value?.tracker?.script_tag || siteStore.currentSite?.tracker_script_tag || '')
const activePayload = computed(() => sectionData.value[activeTab.value] || {})

const tabs = [
  { key: 'overview', label: 'Обзор', icon: BarChart3 },
  { key: 'heatmap', label: 'Тепловая карта', icon: Flame },
  { key: 'scrollmap', label: 'Карта скроллинга', icon: ScrollText },
  { key: 'sessions', label: 'Записи сессий', icon: ListVideo },
  { key: 'paths', label: 'Пути пользователей', icon: Route },
  { key: 'funnels', label: 'Воронки', icon: Funnel },
  { key: 'events', label: 'События', icon: MousePointerClick },
  { key: 'pages', label: 'Страницы', icon: FileText },
  { key: 'errors', label: 'Ошибки', icon: CircleAlert },
  { key: 'performance', label: 'Производительность', icon: Gauge },
  { key: 'recommendations', label: 'AI-рекомендации', icon: Sparkles },
]

const endpointByTab = {
  heatmap: 'heatmap',
  scrollmap: 'scrollmap',
  sessions: 'sessions',
  paths: 'paths',
  funnels: 'funnels',
  events: 'events',
  pages: 'pages',
  errors: 'errors',
  performance: 'performance',
  recommendations: 'recommendations',
}

const deviceRows = computed(() => distributionRows(summary.value?.devices))
const browserRows = computed(() => distributionRows(summary.value?.browsers))
const osRows = computed(() => distributionRows(summary.value?.os))
const heatmapCanvas = computed(() => activePayload.value?.canvas || { width: 1440, height: 1800 })
const heatmapPoints = computed(() => activePayload.value?.points || [])
const periodLabel = computed(() => {
  const value = summary.value?.period_days || days.value
  return `последние ${value} дней`
})
const pageOptions = computed(() => {
  const rawPages = activePayload.value?.pages?.length ? activePayload.value.pages : (summary.value?.top_pages || [])
  const seen = new Set()
  return rawPages
    .map((page) => page.path || page.pathname || '/')
    .filter((path) => {
      if (seen.has(path)) return false
      seen.add(path)
      return true
    })
})

const overviewMetricCards = computed(() => {
  const visits = Number(summary.value?.real_visitors ?? summary.value?.visit_count ?? 0)
  const unique = Number(summary.value?.unique_real_visitors ?? summary.value?.visitors_unique ?? 0)
  const pageviews = Number(summary.value?.pageviews_count ?? 0)
  const leads = Number(summary.value?.leads_count ?? 0)
  const conversion = Number(summary.value?.conversion ?? 0)
  const avgDuration = Number(summary.value?.avg_duration ?? 0)
  return [
    {
      label: 'Посещения',
      value: visits,
      description: 'Сколько раз сайт открывали за выбранный период.',
      tooltip: 'Если один человек заходил несколько раз, каждое посещение считается отдельно.',
      status: countStatus(visits, 20, 5),
      recommendation: visits < 5 ? 'Проверьте рекламу, SEO, ссылки на сайт и установку трекера.' : 'Смотрите, какие страницы и источники приводят качественные визиты.',
    },
    {
      label: 'Уникальные посетители',
      value: unique,
      description: 'Сколько разных людей посетили сайт.',
      tooltip: 'Мы стараемся отличать реальных людей от повторных заходов и ботов.',
      status: countStatus(unique, 15, 5),
      recommendation: unique < 5 ? 'Сайту пока не хватает входящего трафика.' : 'Сравните уникальных посетителей с заявками и конверсией.',
    },
    {
      label: 'Просмотры',
      value: pageviews,
      description: 'Сколько страниц открыли посетители.',
      tooltip: 'Один посетитель может открыть несколько страниц.',
      status: visits < 5 ? 'Недостаточно данных' : pageviews / Math.max(visits, 1) >= 1.5 ? 'Хорошо' : 'Требует внимания',
      recommendation: pageviews <= visits ? 'Добавьте заметные переходы на услуги, контакты и форму заявки.' : 'Посмотрите, какие страницы удерживают пользователей лучше всего.',
    },
    {
      label: 'Заявки',
      value: leads,
      description: 'Сколько людей оставили заявку через формы сайта.',
      tooltip: 'Это ключевой показатель эффективности сайта.',
      status: visits < 5 ? 'Недостаточно данных' : leads > 0 ? 'Хорошо' : 'Критично',
      recommendation: leads ? 'Проверьте, какие страницы и пути чаще приводят заявки.' : 'Если трафик есть, проверьте форму, оффер, кнопки и тепловую карту.',
    },
    {
      label: 'Конверсия',
      value: `${conversion}%`,
      description: 'Какая доля посетителей оставила заявку.',
      tooltip: 'Конверсия показывает, насколько хорошо сайт превращает посетителей в клиентов.',
      status: conversionStatus(conversion, visits),
      recommendation: conversion < 2 ? 'Улучшите первый экран, кнопки и форму заявки.' : 'Усильте страницы и источники, которые уже дают заявки.',
    },
    {
      label: 'Среднее время на сайте',
      value: formatSeconds(avgDuration),
      description: 'Сколько в среднем посетители проводят на сайте.',
      tooltip: 'Низкое время может означать, что пользователи не находят нужную информацию.',
      status: durationStatus(avgDuration, visits),
      recommendation: avgDuration < 30 ? 'Проверьте скорость загрузки и понятность первого экрана.' : 'Посмотрите пути пользователей и страницы с хорошим удержанием.',
    },
  ]
})

const periodSummaryText = computed(() => {
  const visits = Number(summary.value?.real_visitors ?? summary.value?.visit_count ?? 0)
  const leads = Number(summary.value?.leads_count ?? 0)
  const conversion = Number(summary.value?.conversion ?? 0)
  if (!summary.value || visits < 5) {
    return 'Данных пока недостаточно для точной оценки. Проверьте, установлен ли код трекера, открыт ли сайт публично и были ли реальные посещения.'
  }
  const status = conversionStatus(conversion, visits).toLowerCase()
  if (leads === 0) {
    return `За ${periodLabel.value} сайт посетили ${visits} человек, но заявок пока нет. Трафик есть, поэтому стоит проверить форму, кнопки и тепловую карту.`
  }
  if (conversion < 2) {
    return `За ${periodLabel.value} сайт посетили ${visits} человек. Заявок — ${leads}, конверсия ${conversion}%. Это требует внимания: пользователи доходят до сайта, но не становятся клиентами.`
  }
  return `За ${periodLabel.value} сайт посетили ${visits} человек. Из них ${leads} оставили заявку. Конверсия составляет ${conversion}%, это ${status} показатель для текущего периода.`
})

const attentionItems = computed(() => {
  const visits = Number(summary.value?.real_visitors ?? summary.value?.visit_count ?? 0)
  const total = Number(summary.value?.total_visitors ?? visits)
  const bots = Number(summary.value?.bot_visitors ?? 0)
  const leads = Number(summary.value?.leads_count ?? 0)
  const conversion = Number(summary.value?.conversion ?? 0)
  const avgDuration = Number(summary.value?.avg_duration ?? 0)
  const pageviews = Number(summary.value?.pageviews_count ?? 0)
  const items = []
  if (visits < 5) items.push('Пока мало данных: проверьте установку трекера и выбранный период.')
  if (visits >= 5 && leads === 0) items.push('Трафик есть, но заявок нет: проверьте форму, оффер и кнопки.')
  if (visits >= 5 && conversion < 2) items.push('Конверсия ниже ожидаемой: стоит посмотреть тепловую карту и записи сессий.')
  if (total > 0 && bots / total > 0.25) items.push('Высокая доля ботов: основные выводы лучше делать по реальным посетителям.')
  if (visits >= 5 && avgDuration < 30) items.push('Среднее время на сайте низкое: первый экран может быть непонятным или страница грузится долго.')
  if (visits >= 5 && pageviews <= visits) items.push('Пользователи редко переходят дальше первой страницы.')
  const mobile = Number(summary.value?.devices?.mobile || 0)
  const deviceTotal = Object.values(summary.value?.devices || {}).reduce((sum, value) => sum + Number(value || 0), 0)
  if (deviceTotal && mobile / deviceTotal >= 0.6) items.push('Большинство посетителей заходят с телефона: проверьте мобильную форму и кнопки.')
  return items.slice(0, 6)
})

const sectionGuide = computed(() => buildSectionGuide(activeTab.value, activePayload.value))

function distributionRows(distribution) {
  const entries = Object.entries(distribution || {})
  const total = entries.reduce((sum, [, count]) => sum + Number(count || 0), 0)
  return entries
    .map(([name, count]) => ({
      name,
      count: Number(count || 0),
      percent: total ? Math.round((Number(count || 0) / total) * 100) : 0,
    }))
    .filter((item) => item.count > 0)
    .sort((left, right) => right.count - left.count)
}

function countStatus(value, good, normal) {
  const count = Number(value || 0)
  if (count <= 0) return 'Недостаточно данных'
  if (count >= good) return 'Хорошо'
  if (count >= normal) return 'Нормально'
  return 'Требует внимания'
}

function conversionStatus(value, visits) {
  if (Number(visits || 0) < 5) return 'Недостаточно данных'
  const conversion = Number(value || 0)
  if (conversion > 5) return 'Хорошо'
  if (conversion >= 2) return 'Нормально'
  if (conversion >= 1) return 'Требует внимания'
  return 'Критично'
}

function durationStatus(value, visits) {
  if (Number(visits || 0) < 5) return 'Недостаточно данных'
  const seconds = Number(value || 0)
  if (seconds > 90) return 'Хорошо'
  if (seconds >= 30) return 'Нормально'
  if (seconds >= 10) return 'Требует внимания'
  return 'Критично'
}

function scrollStatus(value, sessions) {
  if (Number(sessions || 0) < 3) return 'Недостаточно данных'
  const depth = Number(value || 0)
  if (depth > 75) return 'Хорошо'
  if (depth >= 50) return 'Нормально'
  if (depth >= 25) return 'Требует внимания'
  return 'Критично'
}

function buildSectionGuide(tab, payload) {
  if (tab === 'heatmap') {
    const clicks = Number(payload.total_clicks || 0)
    return {
      title: 'Тепловая карта кликов',
      description: 'Показывает, куда посетители нажимают на страницах сайта. Красные зоны получают больше всего кликов.',
      usage: 'Выберите страницу и устройство. Если люди кликают не туда, где есть действие, элемент может выглядеть как кнопка или отвлекать от заявки.',
      insight: clicks ? `За период собрано ${clicks} кликов. Посмотрите, совпадают ли горячие зоны с кнопками заявки и важными ссылками.` : 'Кликов пока нет. Данные появятся после новых посещений сайта.',
      meaning: [
        'Если важная кнопка почти не получает кликов, её нужно сделать заметнее или поднять выше.',
        'Если много кликов по изображению, пользователи могут считать его интерактивным.',
        'Если клики распределены хаотично, на странице может быть слишком много отвлекающих элементов.',
      ],
      actions: [
        'Поднимите ключевую кнопку ближе к первому экрану.',
        'Сделайте кнопку заявки контрастнее и понятнее.',
        'Добавьте ссылку на элемент, по которому часто кликают.',
        'Уберите или ослабьте элементы, которые отвлекают от формы.',
      ],
    }
  }
  if (tab === 'scrollmap') {
    const depth = Number(payload.average_depth || 0)
    return {
      title: 'Карта скроллинга',
      description: 'Показывает, до какой части страницы реально доходят посетители.',
      usage: 'Если форма, контакты или преимущества находятся ниже средней глубины, большинство пользователей их не увидит.',
      insight: depth ? `Средняя глубина прокрутки ${depth}%. Статус: ${scrollStatus(depth, payload.sessions)}.` : 'Пока нет данных о прокрутке.',
      meaning: [
        'Если пользователи не доходят до важного блока, его лучше перенести выше.',
        'Если до формы доходят меньше 30%, форма находится слишком низко.',
        'Низкая глубина часто означает слабый первый экран или недостаточно понятное предложение.',
      ],
      actions: [
        'Поднимите форму или кнопку заявки выше.',
        'Сократите длинные вступительные блоки.',
        'Добавьте переход к заявке в первой видимой области.',
      ],
    }
  }
  if (tab === 'sessions') {
    const count = Number(payload.count || 0)
    return {
      title: 'Записи сессий',
      description: 'Это timeline поведения без записи видео: переходы, клики, скроллы и отправки форм.',
      usage: 'Откройте сессию и посмотрите, где пользователь останавливается, куда кликает и доходит ли до формы.',
      insight: count ? `За период найдено ${count} сессий. Начните с коротких сессий без заявки и сессий с большим числом кликов.` : 'Сессий пока нет.',
      meaning: [
        'Повторяющиеся клики в одном месте часто означают непонятный интерфейс.',
        'Короткие сессии без скролла могут указывать на слабый первый экран.',
        'Если пользователь дошёл до формы и ушёл, проверьте длину и понятность формы.',
      ],
      actions: [
        'Посмотрите 5-10 последних сессий без заявки.',
        'Проверьте, не кликают ли пользователи по неактивным элементам.',
        'Сравните поведение на мобильных и десктопе.',
      ],
    }
  }
  if (tab === 'paths') {
    const top = payload.paths?.[0]
    return {
      title: 'Пути пользователей',
      description: 'Показывает, по каким страницам люди проходят до заявки или до выхода.',
      usage: 'Ищите пути, которые заканчиваются выходом, и страницы, после которых пользователи чаще оставляют заявку.',
      insight: top ? `Самый популярный путь: ${top.path}. Сессий: ${top.sessions}, конверсия: ${top.conversion}%.` : 'Пути пока не сформировались.',
      meaning: [
        'Если путь часто заканчивается выходом, на последней странице не хватает следующего действия.',
        'Если путь до формы длинный, часть пользователей теряется по дороге.',
        'Пути с заявками стоит усиливать и делать более заметными.',
      ],
      actions: [
        'Добавьте кнопку заявки на страницы выхода.',
        'Сделайте путь до формы короче.',
        'Добавьте внутренние ссылки с популярных страниц на контакты или услуги.',
      ],
    }
  }
  if (tab === 'funnels') {
    const steps = payload.steps || []
    const worst = steps.slice(1).sort((a, b) => Number(b.lost || 0) - Number(a.lost || 0))[0]
    return {
      title: 'Воронки',
      description: 'Показывает, сколько людей проходит от посещения сайта до заявки.',
      usage: 'Главное место потерь показывает, какой шаг мешает росту заявок.',
      insight: worst ? `Самая большая потеря сейчас на шаге «${worst.title}»: ${worst.lost} пользователей.` : 'Воронка появится после новых посещений и событий.',
      meaning: [
        'Потери до формы говорят о слабых переходах или незаметных кнопках.',
        'Потери после открытия формы могут означать длинную или непонятную форму.',
        'Резкое падение на первом шаге часто связано с первым экраном и скоростью.',
      ],
      actions: [
        'Уменьшите количество полей в форме.',
        'Сделайте кнопку отправки заметнее.',
        'Добавьте пояснение рядом с формой: что произойдёт после отправки.',
      ],
    }
  }
  if (tab === 'events') {
    const total = (payload.events || []).reduce((sum, event) => sum + Number(event.count || 0), 0)
    return {
      title: 'События',
      description: 'Журнал активности сайта: просмотры, клики, формы, ошибки и технические события.',
      usage: 'Смотрите, какие действия происходят часто, а какие почти не появляются.',
      insight: total ? `За период сгруппировано ${total} событий. Сравните клики, открытия формы и отправки заявки.` : 'Событий пока нет.',
      meaning: [
        'Много кликов и мало заявок означает, что пользователи взаимодействуют, но не доходят до цели.',
        'Ошибки на важных страницах могут мешать отправке формы.',
        'Если форму открывают часто, но не отправляют, проблема может быть в форме.',
      ],
      actions: [
        'Проверьте события form_submit и error.',
        'Сравните клики по кнопкам с фактическими заявками.',
        'Откройте записи сессий для подозрительных событий.',
      ],
    }
  }
  if (tab === 'pages') {
    const topLeadPage = (payload.pages || []).slice().sort((a, b) => Number(b.leads || 0) - Number(a.leads || 0))[0]
    return {
      title: 'Страницы',
      description: 'Показывает, какие страницы привлекают внимание, теряют пользователей и приводят заявки.',
      usage: 'Сравните просмотры, глубину, клики и конверсию. Страница с трафиком без заявок требует улучшения.',
      insight: topLeadPage?.leads ? `Больше всего заявок даёт страница ${topLeadPage.path}: ${topLeadPage.leads}.` : 'Пока нет страницы, которая стабильно даёт заявки.',
      meaning: [
        'Страница с просмотрами и нулём заявок может не давать понятного следующего шага.',
        'Высокие выходы показывают, где пользователь чаще заканчивает путь.',
        'Низкая глубина и низкое время говорят, что контент не удерживает внимание.',
      ],
      actions: [
        'Добавьте кнопку заявки на страницы с высоким трафиком.',
        'Усильте страницы, которые уже дают заявки.',
        'Улучшите страницы с высоким показателем отказов.',
      ],
    }
  }
  if (tab === 'errors') {
    const errors = payload.errors || []
    return {
      title: 'Ошибки',
      description: 'Показывает технические ошибки, которые могут мешать заявкам и нормальной работе сайта.',
      usage: 'В первую очередь исправляйте повторяющиеся ошибки на страницах с формой и высоким трафиком.',
      insight: errors.length ? `Найдено ${errors.length} групп ошибок. Повторяющиеся ошибки стоит исправлять первыми.` : 'Ошибок за период не найдено.',
      meaning: [
        'Ошибки JavaScript могут ломать кнопки, формы или интерактивные блоки.',
        'Ошибка на странице заявки важнее, чем ошибка на второстепенной странице.',
        'Повторяющиеся ошибки затрагивают больше пользователей и сильнее влияют на конверсию.',
      ],
      actions: [
        'Сначала исправьте ошибки на страницах с формой.',
        'Проверьте ошибки, которые повторяются чаще всего.',
        'После исправления сравните количество заявок и ошибок за новый период.',
      ],
    }
  }
  if (tab === 'performance') {
    const lcp = Number(payload.averages?.lcp || 0)
    return {
      title: 'Производительность',
      description: 'Показывает скорость загрузки и стабильность страниц.',
      usage: 'Медленная загрузка особенно критична на мобильных: пользователь может уйти до просмотра формы.',
      insight: lcp ? `Средний LCP ${lcp} ms. ${lcp > 2500 ? 'Загрузка требует внимания.' : 'Скорость выглядит приемлемо.'}` : 'Данных о скорости пока нет.',
      meaning: [
        'Медленная загрузка снижает количество заявок.',
        'Высокий CLS означает, что элементы прыгают и мешают нажимать.',
        'Высокий INP означает задержки при взаимодействии с сайтом.',
      ],
      actions: [
        'Проверьте тяжёлые изображения и видео.',
        'Особенно внимательно проверьте мобильные устройства.',
        'Оптимизируйте страницы с плохими метриками.',
      ],
    }
  }
  return {
    title: 'AI-рекомендации',
    description: 'Локальные правила анализируют поведение пользователей и подсказывают, что может увеличить заявки.',
    usage: 'Начните с рекомендаций высокой важности, затем проверьте связанные разделы.',
    insight: (payload.recommendations || []).length ? `Сформировано рекомендаций: ${payload.recommendations.length}.` : 'Рекомендации появятся после накопления данных.',
    meaning: [
      'Рекомендации строятся на фактах: кликах, скролле, заявках, ошибках и скорости.',
      'Высокая важность означает, что сигнал может заметно влиять на заявки.',
      'Связанные разделы помогают проверить причину рекомендации.',
    ],
    actions: [
      'Начните с рекомендаций высокой важности.',
      'Проверьте связанные страницы и разделы аналитики.',
      'После изменений сравните показатели за новый период.',
    ],
  }
}

function deviceLabel(value) {
  return { desktop: 'Компьютер', mobile: 'Телефон', tablet: 'Планшет', unknown: 'Не определено' }[value] || value || 'Не определено'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatSeconds(value) {
  const seconds = Number(value || 0)
  if (seconds < 60) return `${seconds} сек.`
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return rest ? `${minutes} мин. ${rest} сек.` : `${minutes} мин.`
}

function heatPointStyle(point) {
  const width = Number(heatmapCanvas.value.width || 1440)
  const height = Number(heatmapCanvas.value.height || 1800)
  const size = Math.min(42, 14 + Number(point.count || 0) * 3)
  const alpha = Math.max(0.22, Math.min(0.84, Number(point.intensity || 0.25)))
  return {
    left: `${Math.min(100, Math.max(0, (Number(point.x || 0) / width) * 100))}%`,
    top: `${Math.min(100, Math.max(0, (Number(point.y || 0) / height) * 100))}%`,
    width: `${size}px`,
    height: `${size}px`,
    backgroundColor: `rgba(220, 38, 38, ${alpha})`,
    boxShadow: `0 0 ${size}px rgba(245, 158, 11, ${alpha})`,
  }
}

function sectionParams() {
  const params = {
    days: days.value,
    include_bots: includeBots.value ? 'true' : undefined,
  }
  if (['heatmap', 'scrollmap', 'events'].includes(activeTab.value) && pageFilter.value) {
    params.page = pageFilter.value
  }
  if (['heatmap', 'events'].includes(activeTab.value) && deviceFilter.value !== 'all') {
    params.device = deviceFilter.value
  }
  if (activeTab.value === 'events' && eventTypeFilter.value) {
    params.event_type = eventTypeFilter.value
  }
  if (activeTab.value === 'sessions') {
    params.limit = 50
  }
  return params
}

async function loadSummary() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, {
      days: days.value,
      include_bots: includeBots.value ? 'true' : undefined,
    })
    summary.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить аналитику.'
  } finally {
    loading.value = false
  }
}

async function loadActiveTab() {
  if (activeTab.value === 'overview') {
    await loadSummary()
    return
  }
  const endpoint = endpointByTab[activeTab.value]
  if (!endpoint) return
  sectionLoading.value = true
  error.value = ''
  try {
    const { data } = await getSiteAnalyticsSectionRequest(siteId.value, endpoint, sectionParams())
    sectionData.value = { ...sectionData.value, [activeTab.value]: data }
    if (activeTab.value !== 'sessions') sessionDetail.value = null
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить раздел аналитики.'
  } finally {
    sectionLoading.value = false
  }
}

async function refreshAll() {
  if (activeTab.value === 'overview') {
    await loadSummary()
    return
  }
  await Promise.all([loadSummary(), loadActiveTab()])
}

async function copyScript() {
  if (!trackerScript.value) return
  action.value = 'copy'
  error.value = ''
  success.value = ''
  try {
    await navigator.clipboard.writeText(trackerScript.value)
    success.value = 'Скрипт аналитики скопирован.'
  } catch {
    error.value = 'Не удалось скопировать скрипт. Выделите код вручную.'
  } finally {
    action.value = ''
  }
}

async function refreshKey() {
  action.value = 'key'
  error.value = ''
  success.value = ''
  try {
    const { data } = await refreshSiteTrackingKeyRequest(siteId.value)
    summary.value = {
      ...(summary.value || {}),
      tracker: {
        api_key: data.api_key,
        script_tag: data.tracker_script_tag,
      },
    }
    await siteStore.fetchSite(siteId.value)
    success.value = data?.detail || 'Ключ аналитики обновлён.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось обновить ключ аналитики.'
  } finally {
    action.value = ''
  }
}

async function openSession(sessionId) {
  if (!sessionId) return
  sessionLoading.value = true
  sessionDetail.value = null
  await nextTick()
  sessionDetailBlock.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  try {
    const { data } = await getSiteAnalyticsSessionRequest(siteId.value, sessionId, {
      days: days.value,
      include_bots: includeBots.value ? 'true' : undefined,
    })
    sessionDetail.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить сессию.'
  } finally {
    sessionLoading.value = false
  }
  await nextTick()
  sessionDetailBlock.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function setTab(tabKey) {
  activeTab.value = tabKey
}

watch(activeTab, () => {
  pageFilter.value = ''
  eventTypeFilter.value = ''
  sessionDetail.value = null
  loadActiveTab()
})

watch(siteId, () => {
  sectionData.value = {}
  sessionDetail.value = null
  loadSummary()
  if (activeTab.value !== 'overview') loadActiveTab()
})

onMounted(async () => {
  await loadSummary()
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Посетители сайта</p>
        <h1>Аналитика</h1>
        <p>Обзор, поведенческие события, страницы, пути и технические сигналы.</p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <div class="inline-flex rounded-2xl border border-brand-100 bg-white/86 p-1 shadow-sm">
          <button
            type="button"
            class="rounded-xl px-3 py-2 text-sm font-semibold transition"
            :class="!includeBots ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-brand-800'"
            @click="includeBots = false; refreshAll()"
          >
            Только реальные
          </button>
          <button
            type="button"
            class="rounded-xl px-3 py-2 text-sm font-semibold transition"
            :class="includeBots ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-brand-800'"
            @click="includeBots = true; refreshAll()"
          >
            С ботами
          </button>
        </div>
        <select v-model.number="days" class="form-control w-36" @change="refreshAll">
          <option :value="7">7 дней</option>
          <option :value="14">14 дней</option>
          <option :value="30">30 дней</option>
          <option :value="90">90 дней</option>
        </select>
        <button type="button" class="icon-button" title="Обновить" aria-label="Обновить" @click="refreshAll">
          <RefreshCw :size="18" />
        </button>
      </div>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>

    <nav class="overflow-x-auto rounded-2xl border border-brand-100 bg-white/90 p-2 shadow-soft backdrop-blur">
      <div class="flex min-w-max gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="inline-flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition"
          :class="activeTab === tab.key ? 'bg-brand-600 text-white shadow-[0_10px_24px_rgba(109,93,246,0.22)]' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-800'"
          @click="setTab(tab.key)"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.label }}
        </button>
      </div>
    </nav>

    <section v-if="(activeTab === 'overview' && loading) || (activeTab !== 'overview' && sectionLoading)" class="empty-state">
      <span class="loading-dot" />
      <p>Собираем статистику...</p>
    </section>

    <template v-else>
      <template v-if="activeTab !== 'overview'">
        <AnalyticsInfoBlock
          :title="sectionGuide.title"
          :description="sectionGuide.description"
          :usage="sectionGuide.usage"
          :insight="sectionGuide.insight"
        />
        <AnalyticsInsightBlock :items="sectionGuide.meaning" />
        <WhatToDoNextBlock :items="sectionGuide.actions" />
      </template>

      <template v-if="activeTab === 'overview'">
        <AnalyticsSummaryCard :text="periodSummaryText" :attention-items="attentionItems" />

        <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <article v-for="metric in overviewMetricCards" :key="metric.label" class="surface">
            <div class="flex flex-col items-start gap-3 sm:flex-row sm:justify-between">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <h2 class="text-base font-semibold text-[#17223B]">{{ metric.label }}</h2>
                  <MetricHelpTooltip :text="metric.tooltip" />
                </div>
                <p class="mt-1 text-sm leading-6 text-slate-500">{{ metric.description }}</p>
              </div>
              <MetricStatusBadge :status="metric.status" />
            </div>
            <p class="mt-4 text-3xl font-bold text-[#17223B]">{{ metric.value }}</p>
            <p class="mt-3 rounded-2xl border border-brand-100 bg-[#F5F7FD] p-3 text-sm leading-6 text-slate-600">{{ metric.recommendation }}</p>
          </article>
        </section>

        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Скрипт аналитики</h2>
              <p>Код трекера для публичного сайта.</p>
            </div>
            <KeyRound :size="21" class="text-brand-700" />
          </div>
          <code class="block overflow-x-auto rounded-2xl bg-[#17223B] px-4 py-3 text-sm leading-6 text-slate-50">{{ trackerScript || 'Ключ аналитики пока не создан.' }}</code>
          <div class="mt-3 flex flex-col gap-2 sm:flex-row">
            <button type="button" class="action-button-primary" :disabled="!trackerScript || Boolean(action)" @click="copyScript">
              <Copy :size="17" />
              Скопировать скрипт
            </button>
            <button type="button" class="action-button-secondary" :disabled="Boolean(action)" @click="refreshKey">
              <KeyRound :size="17" />
              {{ action === 'key' ? 'Обновляем...' : 'Обновить ключ' }}
            </button>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-2">
          <section class="surface">
            <div class="section-heading">
              <div>
                <h2>Популярные страницы</h2>
                <p>Что посетители смотрят чаще всего.</p>
              </div>
              <BarChart3 :size="21" class="text-brand-700" />
            </div>
            <div v-if="(summary?.top_pages || []).length" class="space-y-2">
              <div v-for="page in summary.top_pages" :key="page.pathname" class="flex items-center justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
                <span class="min-w-0 truncate text-sm font-medium text-slate-800">{{ page.pathname || '/' }}</span>
                <span class="status-badge status-neutral">{{ page.count }} просмотров</span>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading">
              <div>
                <h2>Устройства</h2>
                <p>С чего заходят посетители.</p>
              </div>
              <MonitorSmartphone :size="21" class="text-brand-700" />
            </div>
            <div v-if="deviceRows.length" class="space-y-2">
              <div v-for="item in deviceRows" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm font-medium">{{ deviceLabel(item.name) }}</span>
                <strong class="text-sm text-slate-950">{{ item.percent }}%</strong>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Браузеры</h2><p>Клиентские браузеры посетителей.</p></div></div>
            <div v-if="browserRows.length" class="space-y-2">
              <div v-for="item in browserRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span>
                <strong class="text-sm">{{ item.percent }}%</strong>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Операционные системы</h2><p>Системы на устройствах посетителей.</p></div></div>
            <div v-if="osRows.length" class="space-y-2">
              <div v-for="item in osRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span>
                <strong class="text-sm">{{ item.percent }}%</strong>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Источники переходов</h2><p>Откуда приходит трафик.</p></div></div>
            <div v-if="(summary?.sources || []).length" class="space-y-2">
              <div v-for="item in summary.sources.slice(0, 8)" :key="item.referrer || 'direct'" class="grid grid-cols-[1fr_auto] items-center gap-3 border-b border-slate-100 py-3 last:border-0">
                <span class="truncate text-sm font-medium">{{ item.referrer || 'Прямой переход' }}</span>
                <span class="text-xs text-slate-500">{{ item.count }} визитов</span>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Время на сайте</h2><p>Средняя длительность визита.</p></div></div>
            <p class="text-4xl font-semibold text-slate-950">{{ formatSeconds(summary?.avg_duration || 0) }}</p>
            <p class="mt-2 text-sm text-slate-500">Всего: {{ formatSeconds(summary?.total_time_on_site_seconds || 0) }}</p>
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'heatmap'">
        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Тепловая карта кликов</h2>
              <p>{{ activePayload.total_clicks || 0 }} кликов за период.</p>
            </div>
            <Filter :size="20" class="text-brand-700" />
          </div>
          <div class="grid gap-3 md:grid-cols-[1fr_180px_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <select v-model="deviceFilter" class="form-control" @change="loadActiveTab">
              <option value="all">Все устройства</option>
              <option value="desktop">Компьютер</option>
              <option value="mobile">Телефон</option>
              <option value="tablet">Планшет</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.8fr)]">
          <section class="surface">
            <div class="section-heading"><div><h2>Карта</h2><p>{{ heatmapCanvas.width }} x {{ heatmapCanvas.height }}</p></div></div>
            <div v-if="heatmapPoints.length" class="max-w-full overflow-x-auto overscroll-x-contain pb-2">
              <div class="relative h-[620px] w-full min-w-[640px] overflow-hidden rounded-2xl border border-brand-100 bg-[#F5F7FD] lg:min-w-0">
                <div class="absolute inset-x-0 top-0 h-px bg-slate-200" />
                <div
                  v-for="point in heatmapPoints"
                  :key="`${point.x}-${point.y}-${point.count}`"
                  class="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/70"
                  :style="heatPointStyle(point)"
                  :title="`${point.count} кликов`"
                />
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>

          <section class="surface">
            <div class="section-heading"><div><h2>Кликабельные элементы</h2><p>Группировка по тексту и тегу.</p></div></div>
            <div v-if="(activePayload.top_elements || []).length" class="space-y-2">
              <div v-for="item in activePayload.top_elements" :key="`${item.element}-${item.path}`" class="border-b border-slate-100 py-3 last:border-0">
                <div class="flex items-center justify-between gap-3">
                  <span class="min-w-0 truncate text-sm font-semibold text-slate-800">{{ item.element || item.tag || 'Без подписи' }}</span>
                  <span class="status-badge status-neutral">{{ item.count }}</span>
                </div>
                <p class="mt-1 truncate text-xs text-slate-500">{{ item.path }}</p>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'scrollmap'">
        <section class="surface">
          <div class="section-heading">
            <div>
              <h2>Карта скроллинга</h2>
              <p>Средняя глубина: {{ activePayload.average_depth || 0 }}%.</p>
            </div>
          </div>
          <div class="grid gap-3 md:grid-cols-[1fr_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <section class="surface">
            <div class="section-heading"><div><h2>Глубина просмотра</h2><p>{{ activePayload.sessions || 0 }} сессий со скроллом.</p></div></div>
            <div class="space-y-3">
              <div v-for="threshold in ['25', '50', '75', '100']" :key="threshold">
                <div class="mb-1 flex items-center justify-between text-sm">
                  <span class="font-medium text-slate-700">{{ threshold }}%</span>
                  <span class="text-slate-500">{{ activePayload.thresholds?.[threshold]?.rate || 0 }}%</span>
                </div>
                <div class="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div class="h-full rounded-full bg-brand-600" :style="{ width: `${activePayload.thresholds?.[threshold]?.rate || 0}%` }" />
                </div>
              </div>
            </div>
          </section>
          <section class="surface">
            <div class="section-heading"><div><h2>Страницы с худшей глубиной</h2><p>Сортировка по средней глубине.</p></div></div>
            <div v-if="(activePayload.worst_pages || []).length" class="overflow-x-auto">
              <table class="data-table">
                <thead><tr><th>Страница</th><th>Сессии</th><th>Глубина</th></tr></thead>
                <tbody>
                  <tr v-for="page in activePayload.worst_pages" :key="page.path">
                    <td>{{ page.path }}</td>
                    <td>{{ page.sessions }}</td>
                    <td>{{ page.avg_depth }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <EmptyAnalyticsState v-else />
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'sessions'">
        <section class="surface">
          <div class="section-heading"><div><h2>Записи сессий</h2><p>{{ activePayload.count || 0 }} сессий за период.</p></div></div>
          <div v-if="(activePayload.results || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Дата</th><th>Устройство</th><th>Браузер</th><th>Длительность</th><th>Клики</th><th>Страницы</th><th></th></tr></thead>
              <tbody>
                <tr v-for="session in activePayload.results" :key="session.session_id">
                  <td>{{ formatDate(session.started_at) }}</td>
                  <td>{{ deviceLabel(session.device_type) }}</td>
                  <td>{{ session.browser }}</td>
                  <td>{{ formatSeconds(session.duration) }}</td>
                  <td>{{ session.clicks }}</td>
                  <td class="max-w-sm truncate">{{ (session.pages || []).join(' -> ') || '—' }}</td>
                  <td>
                    <button type="button" class="action-button-secondary min-h-9 px-3 py-1.5" @click="openSession(session.session_id)">
                      <Play :size="15" />
                      Воспроизвести
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyAnalyticsState v-else />
        </section>

        <section v-if="sessionLoading" ref="sessionDetailBlock" class="empty-state scroll-mt-20"><span class="loading-dot" /><p>Загружаем сессию...</p></section>
        <section v-else-if="sessionDetail" ref="sessionDetailBlock" class="surface scroll-mt-20">
          <div class="section-heading">
            <div>
              <h2>Timeline сессии</h2>
              <p>{{ sessionDetail.session.session_id }}</p>
            </div>
          </div>
          <div class="space-y-3">
            <div v-for="event in sessionDetail.events" :key="event.id" class="grid gap-2 rounded-2xl border border-brand-100 bg-white/76 p-3 sm:grid-cols-[150px_140px_1fr]">
              <span class="text-xs text-slate-500">{{ formatDate(event.timestamp) }}</span>
              <span class="status-badge status-neutral justify-center">{{ event.type }}</span>
              <span class="min-w-0 truncate text-sm text-slate-700">{{ event.path }} {{ event.element ? `- ${event.element}` : '' }}</span>
            </div>
          </div>
        </section>
      </template>

      <template v-else-if="activeTab === 'paths'">
        <section class="surface">
          <div class="section-heading"><div><h2>Пути пользователей</h2><p>Популярные цепочки страниц.</p></div></div>
          <div v-if="(activePayload.paths || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Путь</th><th>Сессии</th><th>Конверсия</th><th>Средняя длительность</th></tr></thead>
              <tbody>
                <tr v-for="path in activePayload.paths" :key="path.path">
                  <td class="min-w-[360px]">{{ path.path }}</td>
                  <td>{{ path.sessions }}</td>
                  <td>{{ path.conversion }}%</td>
                  <td>{{ formatSeconds(path.avg_duration) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>

      <template v-else-if="activeTab === 'funnels'">
        <section class="surface">
          <div class="section-heading"><div><h2>{{ activePayload.name || 'Базовая воронка' }}</h2><p>Переходы между ключевыми шагами.</p></div></div>
          <div v-if="(activePayload.steps || []).length" class="grid gap-3 lg:grid-cols-4">
            <article v-for="step in activePayload.steps" :key="step.key" class="rounded-2xl border border-brand-100 bg-white/86 p-4 shadow-sm">
              <p class="text-sm font-semibold text-[#17223B]">{{ step.title }}</p>
              <p class="mt-3 text-3xl font-semibold text-brand-700">{{ step.users }}</p>
              <p class="mt-2 text-xs text-slate-500">Переход: {{ step.rate }}%, потери: {{ step.lost }}</p>
            </article>
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>

      <template v-else-if="activeTab === 'events'">
        <section class="surface">
          <div class="section-heading"><div><h2>События</h2><p>Агрегация по типу, странице и элементу.</p></div></div>
          <div class="grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
            <select v-model="pageFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все страницы</option>
              <option v-for="path in pageOptions" :key="path" :value="path">{{ path }}</option>
            </select>
            <select v-model="eventTypeFilter" class="form-control" @change="loadActiveTab">
              <option value="">Все события</option>
              <option v-for="item in activePayload.types || []" :key="item.type" :value="item.type">{{ item.type }}</option>
            </select>
            <select v-model="deviceFilter" class="form-control" @change="loadActiveTab">
              <option value="all">Все устройства</option>
              <option value="desktop">Компьютер</option>
              <option value="mobile">Телефон</option>
              <option value="tablet">Планшет</option>
            </select>
            <button type="button" class="action-button-secondary" @click="loadActiveTab"><RefreshCw :size="17" />Обновить</button>
          </div>
        </section>
        <section class="surface">
          <div v-if="(activePayload.events || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Тип</th><th>Страница</th><th>Элемент</th><th>Количество</th><th>Уникальные</th><th>Последнее</th></tr></thead>
              <tbody>
                <tr v-for="event in activePayload.events" :key="`${event.event_type}-${event.page}-${event.element}`">
                  <td>{{ event.event_type }}</td>
                  <td>{{ event.page || '—' }}</td>
                  <td>{{ event.element || '—' }}</td>
                  <td>{{ event.count }}</td>
                  <td>{{ event.unique_visitors }}</td>
                  <td>{{ formatDate(event.last_seen) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>

      <template v-else-if="activeTab === 'pages'">
        <section class="surface">
          <div class="section-heading"><div><h2>Страницы</h2><p>Детальная аналитика по URL.</p></div></div>
          <div v-if="(activePayload.pages || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Страница</th><th>Просмотры</th><th>Уникальные</th><th>Время</th><th>Скролл</th><th>Клики</th><th>Заявки</th><th>Конверсия</th><th>Выходы</th><th>Отказы</th></tr></thead>
              <tbody>
                <tr v-for="page in activePayload.pages" :key="page.path">
                  <td class="min-w-[220px]">{{ page.path }}</td>
                  <td>{{ page.views }}</td>
                  <td>{{ page.unique_visitors }}</td>
                  <td>{{ formatSeconds(page.avg_time) }}</td>
                  <td>{{ page.avg_scroll_depth }}%</td>
                  <td>{{ page.clicks }}</td>
                  <td>{{ page.leads }}</td>
                  <td>{{ page.conversion }}%</td>
                  <td>{{ page.exits }}</td>
                  <td>{{ page.bounce_rate }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>

      <template v-else-if="activeTab === 'errors'">
        <section class="surface">
          <div class="section-heading"><div><h2>Ошибки</h2><p>JS errors, unhandled rejection и failed fetch.</p></div></div>
          <div v-if="(activePayload.errors || []).length" class="overflow-x-auto">
            <table class="data-table">
              <thead><tr><th>Сообщение</th><th>Страница</th><th>Браузер</th><th>Устройство</th><th>Количество</th><th>Последняя дата</th></tr></thead>
              <tbody>
                <tr v-for="item in activePayload.errors" :key="`${item.message}-${item.page}`">
                  <td class="min-w-[260px]">{{ item.message }}</td>
                  <td>{{ item.page || '—' }}</td>
                  <td>{{ item.browser }}</td>
                  <td>{{ deviceLabel(item.device) }}</td>
                  <td>{{ item.count }}</td>
                  <td>{{ formatDate(item.last_seen) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>

      <template v-else-if="activeTab === 'performance'">
        <DashboardStats
          :items="[
            { label: 'LCP', value: `${activePayload.averages?.lcp || 0} ms`, sub: 'Largest Contentful Paint' },
            { label: 'CLS', value: activePayload.averages?.cls || 0, sub: 'Layout shift' },
            { label: 'INP', value: `${activePayload.averages?.inp || activePayload.averages?.fid || 0} ms`, sub: 'Interaction latency' },
            { label: 'TTFB', value: `${activePayload.averages?.ttfb || 0} ms`, sub: 'Response start' },
          ]"
        />
        <div class="grid gap-4 xl:grid-cols-2">
          <section class="surface">
            <div class="section-heading"><div><h2>Плохие страницы</h2><p>Срабатывания порогов производительности.</p></div></div>
            <div v-if="(activePayload.bad_pages || []).length" class="space-y-2">
              <div v-for="page in activePayload.bad_pages" :key="page.path" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
                <span class="text-sm font-medium">{{ page.path }}</span>
                <span class="status-badge status-warning">{{ page.count }}</span>
              </div>
            </div>
            <EmptyAnalyticsState v-else />
          </section>
          <section class="surface">
            <div class="section-heading"><div><h2>По устройствам</h2><p>Средние значения по типу устройства.</p></div></div>
            <div v-if="(activePayload.devices || []).length" class="overflow-x-auto">
              <table class="data-table">
                <thead><tr><th>Устройство</th><th>LCP</th><th>CLS</th><th>INP</th><th>Load</th></tr></thead>
                <tbody>
                  <tr v-for="item in activePayload.devices" :key="item.device">
                    <td>{{ deviceLabel(item.device) }}</td>
                    <td>{{ item.metrics?.lcp || 0 }}</td>
                    <td>{{ item.metrics?.cls || 0 }}</td>
                    <td>{{ item.metrics?.inp || 0 }}</td>
                    <td>{{ item.metrics?.page_load_time || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <EmptyAnalyticsState v-else />
          </section>
        </div>
      </template>

      <template v-else-if="activeTab === 'recommendations'">
        <section class="surface">
          <div class="section-heading"><div><h2>AI-рекомендации</h2><p>Правила и локальные сигналы без внешнего AI API.</p></div></div>
          <div v-if="(activePayload.recommendations || []).length" class="grid gap-3 lg:grid-cols-2">
            <AnalyticsRecommendationCard v-for="item in activePayload.recommendations" :key="`${item.title}-${item.page}`" :item="item" />
          </div>
          <EmptyAnalyticsState v-else />
        </section>
      </template>
    </template>
  </div>
</template>
