export const REGISTER_SUCCESS_ROUTE = Object.freeze({
  name: 'dashboard',
  query: Object.freeze({ registered: '1' }),
})

export function resolvePostSiteLoadRedirect(to, siteState) {
  const siteStoreLoaded = Boolean(siteState?.loaded)
  const siteStoreHasError = Boolean(siteState?.error)
  const sites = Array.isArray(siteState?.sites) ? siteState.sites : []
  const hasSites = siteStoreLoaded && !siteStoreHasError && sites.length > 0

  if (to?.name === 'onboarding' && hasSites) {
    return { name: 'dashboard' }
  }

  return null
}
