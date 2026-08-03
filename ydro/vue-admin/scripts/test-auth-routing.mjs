import assert from 'node:assert/strict'

import {
  DEFAULT_AUTHENTICATED_ROUTE,
  intendedRouteAfterAuth,
  isLegacyOnboardingPath,
} from '../src/router/authRedirects.js'

assert.equal(DEFAULT_AUTHENTICATED_ROUTE, '/dashboard')

assert.equal(intendedRouteAfterAuth(), '/dashboard')
assert.equal(intendedRouteAfterAuth(['/billing', '/dashboard']), '/billing')
assert.equal(intendedRouteAfterAuth({ path: '/billing' }), '/dashboard')
assert.equal(intendedRouteAfterAuth('/dashboard'), '/dashboard')
assert.equal(intendedRouteAfterAuth('/billing'), '/billing')
assert.equal(intendedRouteAfterAuth('/sites/42/sections?tab=hero'), '/sites/42/sections?tab=hero')

assert.equal(isLegacyOnboardingPath('/onboarding'), true)
assert.equal(isLegacyOnboardingPath('/onboarding/create-site'), true)
assert.equal(isLegacyOnboardingPath('/dashboard'), false)

assert.equal(intendedRouteAfterAuth('/onboarding'), '/dashboard')
assert.equal(intendedRouteAfterAuth('/onboarding/create-site'), '/dashboard')

console.log('auth routing tests passed')
