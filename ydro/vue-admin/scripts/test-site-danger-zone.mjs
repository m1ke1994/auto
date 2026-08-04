import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const view = readFileSync(resolve(root, 'src/views/SiteOverviewView.vue'), 'utf8')
const api = readFileSync(resolve(root, 'src/api/site.js'), 'utf8')
const store = readFileSync(resolve(root, 'src/stores/site.js'), 'utf8')

assert.match(api, /clearSiteAnalyticsRequest/)
assert.match(api, /deleteMySiteRequest/)
assert.match(api, /http\.delete\(`\/api\/admin\/my-sites\/\$\{siteId\}\/analytics\/`/)
assert.match(api, /http\.delete\(`\/api\/admin\/my-sites\/\$\{siteId\}\/`/)

assert.match(store, /async function clearSiteAnalytics/)
assert.match(store, /async function deleteSite/)
assert.match(store, /sites\.value = sites\.value\.filter/)
assert.match(store, /currentSiteId\.value = sites\.value\[0\]\?\.id \?\? null/)

assert.match(view, /Опасная зона/)
assert.match(view, /clearModalOpen/)
assert.match(view, /deleteModalOpen/)
assert.match(view, /clearConfirmationValid/)
assert.match(view, /deleteConfirmationValid/)
assert.match(view, /Введите название сайта или ОЧИСТИТЬ/)
assert.match(view, /Введите точное название сайта/)
assert.match(view, /disabled="!clearConfirmationValid \|\| clearing"/)
assert.match(view, /disabled="!deleteConfirmationValid \|\| deleting"/)
assert.match(view, /siteStore\.deleteSite/)
assert.match(view, /router\.push\('\/dashboard'\)/)

console.log('site danger zone UI tests passed')
