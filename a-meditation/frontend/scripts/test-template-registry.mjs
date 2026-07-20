import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const registry = readFileSync(new URL('../src/templates/templateRegistry.js', import.meta.url), 'utf8')
const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/composables/useLeadApi.js', import.meta.url), 'utf8')
const content = readFileSync(new URL('../src/composables/usePublicSiteContent.js', import.meta.url), 'utf8')
const viteConfig = readFileSync(new URL('../vite.config.js', import.meta.url), 'utf8')
const builtIndex = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8')
const nginxHttp = readFileSync(new URL('../../../ydro/docker/nginx/templates/default.conf.template', import.meta.url), 'utf8')
const nginxHttps = readFileSync(new URL('../../../ydro/docker/nginx/templates-https/default.conf.template', import.meta.url), 'utf8')

assert.match(registry, /'art-troy': ArtStroyTemplate/)
assert.match(registry, /'a-meditation': AMeditationTemplate/)
assert.match(registry, /legacyTemplateKeysBySlug/)
assert.match(app, /Неизвестный шаблон/)
assert.match(api, /if \(isPreviewMode\)/)
assert.match(content, /if \(isPreviewMode\) return/)
assert.match(viteConfig, /base: '\/public-site-assets\/'/)
assert.match(builtIndex, /src="\/public-site-assets\/assets\/index-[^"]+\.js"/)
assert.match(builtIndex, /href="\/public-site-assets\/assets\/index-[^"]+\.css"/)
assert.match(nginxHttp, /location \/public-site-assets\//)
assert.match(nginxHttps, /location \/public-site-assets\//)
console.log('template registry checks passed')
