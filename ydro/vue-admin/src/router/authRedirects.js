const DEFAULT_AUTHENTICATED_ROUTE = '/dashboard'
const LEGACY_ONBOARDING_PREFIX = '/onboarding'

export function isLegacyOnboardingPath(path) {
  return path === LEGACY_ONBOARDING_PREFIX || path.startsWith(`${LEGACY_ONBOARDING_PREFIX}/`)
}

export function intendedRouteAfterAuth(path) {
  if (Array.isArray(path)) return intendedRouteAfterAuth(path[0])
  if (typeof path !== 'string') return DEFAULT_AUTHENTICATED_ROUTE
  if (!path || isLegacyOnboardingPath(path)) return DEFAULT_AUTHENTICATED_ROUTE
  return path
}

export { DEFAULT_AUTHENTICATED_ROUTE }
