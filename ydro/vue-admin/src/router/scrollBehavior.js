// New routes open at the top. In-page section links scroll smoothly.
// Explicit cross-page hashes (e.g. /#contact) still target their section.
export function resolveScrollPosition(to, from, savedPosition, { reducedMotion = false } = {}) {
  const pageChanged = to.path !== from.path
  if (to.hash) {
    return { el: to.hash, behavior: pageChanged || reducedMotion ? 'instant' : 'smooth' }
  }
  if (pageChanged) return { left: 0, top: 0, behavior: 'instant' }
  if (savedPosition) return { ...savedPosition, behavior: 'instant' }
  return { left: 0, top: 0, behavior: 'instant' }
}
