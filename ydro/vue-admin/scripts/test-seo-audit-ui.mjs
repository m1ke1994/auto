import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const view = readFileSync(resolve(root, 'src/views/mini/MiniSeoAuditView.vue'), 'utf8')
const miniApi = readFileSync(resolve(root, 'src/api/mini.js'), 'utf8')

assert.match(view, /permissions\?\.platform_access/)
assert.match(view, /mode\.value === 'external'/)
assert.match(view, /target_url:\s*targetUrl\.value\.trim\(\)/)
assert.match(view, /siteId\.value && !canUseExternalUrl\.value/)
assert.match(view, /https:\/\/example\.com или example\.com/)
assert.match(view, /backendErrorMessage/)
assert.match(view, /firstErrorMessage/)
assert.match(miniApi, /const payload = \{ \.\.\.params \}/)
assert.match(miniApi, /if \(String\(domain \|\| ''\)\.trim\(\)\) payload\.domain/)
assert.match(view, /Проверить любой сайт/)
assert.match(view, /Запустить SEO-аудит/)

console.log('seo audit UI tests passed')
