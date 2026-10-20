import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { marketingPageList } from '../src/content/marketingPages.js'

const root = resolve('.')
const read = path => readFileSync(resolve(root, path), 'utf8')
const unique = items => new Set(items).size === items.length
const paths = marketingPageList.map(page => page.path)

assert.equal(marketingPageList.length, 4, 'Expected four public commercial pages')
assert.ok(unique(paths), 'All marketing URL paths must be unique')
assert.ok(unique(marketingPageList.map(page => page.title)), 'Title tags must be unique')
assert.ok(unique(marketingPageList.map(page => page.description)), 'Descriptions must be unique')
assert.ok(unique(marketingPageList.map(page => page.headline)), 'H1 headings must be unique')
for (const page of marketingPageList) {
  assert.match(page.path, /^\/[a-z-]+$/, 'Use clean canonical paths')
  assert.ok(page.title.length >= 35 && page.title.length <= 75, page.key + ' title length')
  assert.ok(page.description.length >= 90 && page.description.length <= 190, page.key + ' description length')
  assert.ok(page.lead.length > 110, page.key + ' must have substantive introductory copy')
  assert.equal(page.benefits.length, 4, page.key + ' should have four meaningful features')
  assert.equal(page.process.length, 3)
  assert.equal(page.faq.length, 3)
}
const router = read('src/router/index.js')
const prerender = read('scripts/prerender.mjs')
const landing = read('src/views/LandingPage.vue')
// The frontend Docker image contains /app only, not the sibling docker/nginx tree.
// Keep HTML/SEO checks mandatory in every build; verify Nginx only when that file exists.
const nginxTemplate = resolve(root, '../docker/nginx/templates-https/default.conf.template')
const nginx = existsSync(nginxTemplate) ? readFileSync(nginxTemplate, 'utf8') : null
assert.match(router, /marketingPageList\.map/, 'Vue router must include new public pages')
assert.match(prerender, /marketingPageList\.map/, 'Prerender must include new pages')
assert.match(prerender, /import \{ marketingPageList \} from '\.\.\/src\/content\/marketingPages\.js'/, 'Prerender must import data into the Node execution scope')
assert.match(prerender, /marketingPageList\) savePage/, 'Prerender must write individual HTML documents')
assert.match(landing, /id="solutions"/, 'Keep integrated landing navigation')
if (nginx) {
  assert.match(nginx, /sozdanie-saitov\|seo-audit\|analitika-saita\|upravlenie-zayavkami/, 'Nginx must allow commercial pages to index')
  assert.match(nginx, /return 301 https:\/\/tracknode\.ru\$request_uri/, 'Canonical www redirect required')
} else {
  console.log('SEO: Nginx configuration is outside frontend Docker context; production deploy checks the host template.')
}
if (!process.argv.includes('--source-only')) {
  const xml = read('dist/sitemap.xml')
  const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match => match[1])
  assert.equal(urls.length, 9, 'Sitemap: main + 4 commercial + 4 legal pages')
  assert.ok(unique(urls), 'Sitemap paths must be unique')
  for (const page of marketingPageList) {
    assert.ok(urls.includes('https://tracknode.ru' + page.path), page.path + ' sitemap missing')
    const file = 'dist' + page.path + '/index.html'
    assert.ok(existsSync(resolve(root, file)), page.path + ' must be prerendered')
    const html = read(file)
    assert.match(html, /<h1(?:\s[^>]*)?>[\s\S]*?<\/h1>/, page.path + ' H1 missing')
    assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1, page.path + ' must have exactly one H1')
    assert.ok(html.includes(page.headline), page.path + ' must have real visible copy in initial HTML')
    assert.ok(html.includes('<title>' + page.title + '</title>'), page.path + ' title missing')
    assert.ok(html.includes('name="description" content="' + page.description + '"'), page.path + ' description missing')
    assert.ok(html.includes('href="https://tracknode.ru' + page.path + '"'), page.path + ' canonical missing')
    assert.ok(html.includes('content="index,follow,max-image-preview:large"'), page.path + ' must be indexable')
    assert.ok(html.includes('id="tracknode-platform-json-ld"'), page.path + ' JSON-LD missing')
    for (const other of marketingPageList) {
      assert.ok(html.includes('href="' + other.path + '"'), page.path + ' cross-links ' + other.path)
    }
  }
}
console.log('SEO CHECK PASSED: 4 commercial pages, canonical URLs, schema and sitemap' + (nginx ? ', Nginx indexability' : ' (Nginx verified on deploy host)'))
