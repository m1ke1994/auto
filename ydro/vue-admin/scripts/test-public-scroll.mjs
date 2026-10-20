import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolveScrollPosition } from '../src/router/scrollBehavior.js'

const route = (path, hash = '') => ({ path, hash })
const top = { left: 0, top: 0, behavior: 'instant' }

// A user reading the bottom of one page must start the next page at its top.
assert.deepEqual(resolveScrollPosition(route('/seo-audit'), route('/'), null), top)
assert.deepEqual(resolveScrollPosition(route('/analitika-saita'), route('/seo-audit'), { left: 0, top: 2600 }), top)
assert.deepEqual(resolveScrollPosition(route('/privacy'), route('/consent'), { left: 0, top: 1800 }), top)
assert.deepEqual(resolveScrollPosition(route('/'), route('/seo-audit'), null), top)
assert.deepEqual(resolveScrollPosition(route('/login'), route('/'), null), top)

// Within one public page, section jumps use a native smooth scroll.
assert.deepEqual(
  resolveScrollPosition(route('/', '#features'), route('/'), null),
  { el: '#features', behavior: 'smooth' },
)
assert.deepEqual(
  resolveScrollPosition(route('/', '#solutions'), route('/', '#features'), null),
  { el: '#solutions', behavior: 'smooth' },
)
assert.deepEqual(
  resolveScrollPosition(route('/', '#pricing'), route('/'), null, { reducedMotion: true }),
  { el: '#pricing', behavior: 'instant' },
)

// Navigation from a service page to the landing contact form retains the anchor.
assert.deepEqual(
  resolveScrollPosition(route('/', '#contact'), route('/sozdanie-saitov'), null),
  { el: '#contact', behavior: 'instant' },
)
assert.deepEqual(
  resolveScrollPosition(route('/seo-audit', '#marketing-content'), route('/seo-audit'), null),
  { el: '#marketing-content', behavior: 'smooth' },
)
assert.deepEqual(
  resolveScrollPosition(route('/'), route('/'), { top: 375, left: 0 }),
  { top: 375, left: 0, behavior: 'instant' },
)

const router = readFileSync('src/router/index.js', 'utf8')
const app = readFileSync('src/App.vue', 'utf8')
const styles = readFileSync('src/style.css', 'utf8')
const landing = readFileSync('src/views/LandingPage.vue', 'utf8')
const marketing = readFileSync('src/views/MarketingPage.vue', 'utf8')

assert.ok(router.includes('scrollBehavior(to, from, savedPosition)'))
assert.ok(router.includes('resolveScrollPosition(to, from, savedPosition'))
assert.ok(app.includes("document.documentElement.classList.toggle('tn-public-scroll'"))
assert.ok(styles.includes('html.tn-public-scroll'))
assert.ok(styles.includes('scroll-behavior: smooth'))
assert.ok(styles.includes('prefers-reduced-motion: reduce'))
for (const section of ['top', 'system', 'solutions', 'features', 'pricing', 'contact']) {
  assert.ok(landing.includes('id="' + section + '"') || landing.includes('href="#' + section + '"'), 'Landing section anchor: ' + section)
}
assert.ok(marketing.includes('to="/#contact"'))
assert.ok(!marketing.includes('href="/#contact"'))

console.log('TrackNode page-start and smooth-section scroll tests passed')
