import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const view = readFileSync(new URL('../src/views/SectionsView.vue', import.meta.url), 'utf8')

assert.match(view, /siteStore\.currentSite\?\.preview_url/)
assert.match(view, /:src="previewUrl"/)
assert.match(view, /:href="previewUrl"/)
assert.match(view, /URL предпросмотра отсутствует/)
assert.match(view, /min-height:720px/)
assert.match(view, /@load="handlePreviewLoad"/)
assert.match(view, /@error="handlePreviewError"/)
console.log('site preview checks passed')
