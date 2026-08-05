import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const view = readFileSync(resolve(root, 'src/views/mini/MiniSeoAuditView.vue'), 'utf8')

assert.match(view, /permissions\?\.platform_access/)
assert.match(view, /mode\.value === 'external'/)
assert.match(view, /target_url:\s*targetUrl\.value\.trim\(\)/)
assert.match(view, /siteId\.value && !canUseExternalUrl\.value/)
assert.match(view, /backendErrorMessage/)
assert.match(view, /firstErrorMessage/)
assert.match(view, /Проверить любой сайт/)
assert.match(view, /Запустить SEO-аудит/)

console.log('seo audit UI tests passed')
