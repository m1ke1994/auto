import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'

const root = process.cwd()
const landing = fs.readFileSync(path.join(root, 'src/views/LandingPage.vue'), 'utf8')
const router = fs.readFileSync(path.join(root, 'src/router/index.js'), 'utf8')
const sitemap = fs.readFileSync(path.join(root, 'public/sitemap.xml'), 'utf8')

assert.match(landing, /Заказать разработку сайта/)
assert.match(landing, /Подключить аналитику/)
assert.match(landing, /https:\/\/tishechkinalexandr\.ru\//)
assert.match(landing, /portfolio_link_click/)
assert.match(landing, /tracknode_website_order/)
assert.match(landing, /v-model="form\.consent"/)
assert.match(router, /path: '\/terms'/)
assert.match(router, /path: '\/privacy'/)
assert.match(router, /path: '\/user-agreement'[\s\S]*redirect: '\/terms'/)
assert.match(sitemap, /https:\/\/tracknode\.ru\/terms/)
assert.match(sitemap, /https:\/\/tracknode\.ru\/privacy/)

console.log('TrackNode landing regression checks passed')
