import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { overviewMetrics, overviewMessage } from '../src/views/dashboardPresentation.js'

const read = path => readFileSync(path, 'utf8')
const site = read('src/views/SiteOverviewView.vue')
const dashboard = read('src/views/DashboardView.vue')
const sidebar = read('src/components/Sidebar.vue')
const analytics = read('src/views/AnalyticsView.vue')
const router = read('src/router/index.js')
const store = read('src/stores/site.js')
const api = read('src/api/analytics.js')

// Missing/failed requests must never be represented as zero visits or zero leads.
assert.deepEqual(overviewMetrics(null), [])
assert.equal(overviewMessage(null), 'Статистика пока не получена.')
const exactZero = overviewMetrics({
  visitors_unique: 0, pageviews_count: 0, leads_count: 0, conversion: 0,
})
assert.deepEqual(exactZero.map(item => item.value), ['0', '0', '0', '0%'])
const missingNumbers = overviewMetrics({})
assert.deepEqual(missingNumbers.map(item => item.value), ['—', '—', '—', '—'])
assert.deepEqual(overviewMetrics({ visitors_unique: 12, pageviews_count: 30, leads_count: 2, conversion: 16.667 }, { showLeads: false }).map(item => item.label), ['Посетители', 'Просмотры страниц'])
assert.ok(overviewMessage({ visitors_unique: 15, leads_count: 0 }).includes('заявок за 14 дней нет'))
assert.ok(overviewMessage({ visitors_unique: 15, leads_count: 2 }).includes('были посетители и заявки'))
assert.ok(overviewMessage({ visitors_unique: 15, leads_count: 2 }, { isActive: false }).includes('отключённый'))
assert.ok(!overviewMessage({ visitors_unique: 15, leads_count: 2 }, { showLeads: false }).includes('заявк'))

// Navigation and permissions: existing routes and feature checks remain in place.
for (const path of ['/dashboard', '/sites/:siteId/overview', '/sites/:siteId/leads', '/sites/:siteId/analytics', '/sites/:siteId/sections']) {
  assert.ok(router.includes(path.replace(':siteId/', ':siteId/')) || router.includes(path.slice(1).replace(':siteId/', ':siteId/')), 'Route '+path)
}
assert.ok(sidebar.includes('return items.filter((item) => item.showWhenLocked || accessStore.can(item.feature))'))
assert.ok(sidebar.includes('navGroups'))
for (const label of ['Главное', 'Дополнительные инструменты', 'Аккаунт и настройки']) assert.ok(sidebar.includes(label))
assert.ok(site.includes('accessStore.can(\'analytics\')'))
assert.ok(site.includes('accessStore.can(\'leads\')'))
assert.ok(site.includes('accessStore.can(action.feature)'))
assert.ok(site.includes('analyticsError'))
assert.ok(site.includes('summary.value = null'))
assert.ok(site.includes('watch(siteId, load)'))
assert.ok(site.includes('!accessStore.can(\'analytics\')'))

// Destructive actions remain separately gated and require explicit typed confirmation.
assert.ok(site.includes('canClearAnalytics = computed'))
assert.ok(site.includes('canDeleteSite = computed'))
assert.ok(site.includes("value === 'ОЧИСТИТЬ'"))
assert.ok(site.includes('deleteConfirmation.value.trim() === siteStore.currentSite?.name'))
assert.ok(site.includes('confirmClearAnalytics'))
assert.ok(site.includes('confirmDeleteSite'))
assert.ok(site.includes('v-if="canClearAnalytics || canDeleteSite"'))
assert.ok(site.includes('Дополнительные настройки сайта'))
assert.ok(site.includes('<details'))
assert.ok(site.includes('v-if="clearModalOpen"'))
assert.ok(site.includes('v-if="deleteModalOpen"'))

// Ordinary users see the primary navigation first, while details are still reachable.
assert.ok(dashboard.includes('Перейти к обзору'))
assert.ok(dashboard.includes('siteStore.error'))
assert.ok(dashboard.includes('Повторить'))
assert.ok(analytics.includes('const primaryTabs'))
assert.ok(analytics.includes('const advancedTabs'))
assert.ok(analytics.includes('advancedTabsOpen'))
assert.ok(analytics.includes('v-if="activeTab === \'overview\' && summary"'))
assert.ok(analytics.includes('Подключение и настройка аналитики'))
assert.ok(analytics.includes('Как читать этот отчёт и что делать с результатами'))
assert.ok(analytics.includes('if (advancedTabs.some(tab => tab.key === tabKey)) advancedTabsOpen.value = true'))

// API interfaces and store data management remain untouched.
assert.ok(api.includes('/analytics/summary/'))
assert.ok(store.includes('deleteMySiteRequest'))
assert.ok(store.includes('clearSiteAnalyticsRequest'))
console.log('TrackNode dashboard clarity and safety tests passed')
