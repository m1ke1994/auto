import assert from 'node:assert/strict'

import { REGISTER_SUCCESS_ROUTE, resolvePostSiteLoadRedirect } from '../src/router/routePolicy.js'

assert.deepEqual(
  REGISTER_SUCCESS_ROUTE,
  { name: 'dashboard', query: { registered: '1' } },
  'successful registration must target dashboard',
)

assert.equal(
  resolvePostSiteLoadRedirect(
    { name: 'dashboard', meta: { requiresAuth: true } },
    { loaded: true, error: '', sites: [] },
  ),
  null,
  'route guard must not redirect a registered user without sites back to onboarding',
)

assert.notDeepEqual(
  REGISTER_SUCCESS_ROUTE,
  { name: 'onboarding' },
  'successful registration must not target onboarding',
)

assert.equal(
  resolvePostSiteLoadRedirect(
    { name: 'billing', meta: { requiresAuth: true, billingExempt: true } },
    { loaded: true, error: '', sites: [] },
  ),
  null,
  'billing route must remain available for subscription flows',
)

assert.equal(
  resolvePostSiteLoadRedirect(
    { name: 'dashboard', meta: { requiresAuth: true } },
    { loaded: true, error: '', sites: [{ id: 1 }] },
  ),
  null,
  'existing-user dashboard login flow must not be redirected by onboarding policy',
)

assert.deepEqual(
  resolvePostSiteLoadRedirect(
    { name: 'onboarding', meta: { requiresAuth: true, onboardingRoute: true } },
    { loaded: true, error: '', sites: [{ id: 1 }] },
  ),
  { name: 'dashboard' },
  'manual onboarding route still exits to dashboard when the user already has sites',
)

assert.equal(
  resolvePostSiteLoadRedirect(
    { name: 'dashboard', meta: { requiresAuth: true } },
    { loaded: false, error: '', sites: [] },
  ),
  null,
  'failed or unfinished registration must not trigger a dashboard redirect from the guard',
)

console.log('registration routing policy tests passed')
