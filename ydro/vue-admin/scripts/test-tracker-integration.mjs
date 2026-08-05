import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const root = new URL('../', import.meta.url)

function read(relativePath) {
  return readFileSync(new URL(relativePath, root), 'utf8')
}

const publicSite = read('src/api/publicSite.js')
const trackerView = read('../clients/views.py')
const serviceWorker = read('public/service-worker.js')

assert.match(publicSite, /removeExistingTrackNodeTrackerScripts/)
assert.match(publicSite, /script\.dataset\.siteKey = trackerKey/)
assert.match(publicSite, /script\.dataset\.tracknodeManaged = 'true'/)
assert.match(publicSite, /activeTracker\.destroy\?\.\('public_site_key_changed'\)/)
assert.doesNotMatch(publicSite, /localStorage/)

assert.match(trackerView, /window\.__trackNodeTracker/)
assert.match(trackerView, /function destroyTracker/)
assert.match(trackerView, /function addManagedEventListener/)
assert.match(trackerView, /function isActiveInstance/)
assert.match(trackerView, /maskPayloadForLog\(payload\)/)
assert.match(trackerView, /var sessionKey = 'saas_tracker_session_id_' \+ storageScope/)
assert.match(trackerView, /addManagedEventListener\(document, 'click', onClick, true\)/)
assert.match(trackerView, /previousTracker\.destroy\('token_changed'\)/)
assert.match(trackerView, /response\["Cache-Control"\] = "no-store, max-age=0"/)

assert.match(serviceWorker, /pathname === '\/tracker\.js'/)
assert.match(serviceWorker, /pathname\.startsWith\('\/api\/'\)/)
assert.match(serviceWorker, /CACHE_PREFIX\}v6/)

console.log('tracker integration checks passed')
