import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const registry = readFileSync(new URL('../src/templates/templateRegistry.js', import.meta.url), 'utf8')
const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/composables/useLeadApi.js', import.meta.url), 'utf8')
const content = readFileSync(new URL('../src/composables/usePublicSiteContent.js', import.meta.url), 'utf8')

assert.match(registry, /'art-troy': ArtStroyTemplate/)
assert.match(registry, /'a-meditation': AMeditationTemplate/)
assert.match(registry, /legacyTemplateKeysBySlug/)
assert.match(app, /Неизвестный шаблон/)
assert.match(api, /if \(isPreviewMode\)/)
assert.match(content, /if \(isPreviewMode\) return/)
console.log('template registry checks passed')
