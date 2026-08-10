import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const view = readFileSync(resolve(root, 'src/views/mini/MiniSeoAuditView.vue'), 'utf8')
const miniApi = readFileSync(resolve(root, 'src/api/mini.js'), 'utf8')

assert.doesNotMatch(view, /permissions\?\.platform_access/)
assert.doesNotMatch(view, /mode\.value === 'external'/)
assert.match(view, /target_url:\s*auditTarget\.value/)
assert.doesNotMatch(view, /site_id/)
assert.match(view, /https:\/\/example\.com или example\.com/)
assert.match(view, /backendErrorMessage/)
assert.match(view, /firstErrorMessage/)
assert.match(miniApi, /const payload = \{ \.\.\.params \}/)
assert.match(miniApi, /if \(String\(domain \|\| ''\)\.trim\(\)\) payload\.domain/)
assert.match(view, /URL сайта/)
assert.match(view, /Запустить SEO-аудит/)

console.log('seo audit UI tests passed')
