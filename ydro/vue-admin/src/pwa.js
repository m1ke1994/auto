let registrationPromise

export function supportsPushNotifications() {
  return Boolean(
    window.isSecureContext &&
      'serviceWorker' in navigator &&
      'PushManager' in window &&
      'Notification' in window,
  )
}

export function getServiceWorkerRegistration() {
  if (!('serviceWorker' in navigator)) {
    return Promise.reject(new Error('Service Worker API is not supported.'))
  }

  if (!registrationPromise) {
    registrationPromise = navigator.serviceWorker
      .register('/service-worker.js', { scope: '/', updateViaCache: 'none' })
      .then(async (registration) => {
        registration.update().catch(() => {})
        return navigator.serviceWorker.ready
      })
      .catch((error) => {
        registrationPromise = undefined
        throw error
      })
  }

  return registrationPromise
}

export function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return
  const hasExistingController = Boolean(navigator.serviceWorker.controller)
  let reloadingForUpdate = false

  if (hasExistingController) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (reloadingForUpdate) return
      reloadingForUpdate = true
      window.location.reload()
    })
  }

  window.addEventListener('load', () => {
    getServiceWorkerRegistration().catch((error) => {
      console.error('TrackNode service worker registration failed.', error)
    })
  })
}
