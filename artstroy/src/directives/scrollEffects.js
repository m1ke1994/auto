const REVEAL_SYMBOL = Symbol('revealDirectiveState')
const PARALLAX_SYMBOL = Symbol('parallaxDirectiveState')

const EASE_PREMIUM = 'cubic-bezier(0.22, 1, 0.36, 1)'

const getReducedMotion = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const getMobileViewport = () => {
  if (typeof window === 'undefined') return false
  return window.innerWidth < 768
}

const parseRevealOptions = (binding) => {
  const source = binding?.value
  if (!source) {
    return { type: 'fade-up' }
  }

  if (typeof source === 'string') {
    return { type: source }
  }

  return {
    type: source.type || 'fade-up',
    delay: Number(source.delay || 0),
    duration: Number(source.duration || 0),
    mobileAlternate: Boolean(source.mobileAlternate),
    mobileIndex: Number(source.mobileIndex || 0),
    once: source.once !== false,
  }
}

const resolveRevealOffset = (options) => {
  const isMobile = getMobileViewport()
  const mobileDistance = 16
  const desktopDistance = 28

  if (options.mobileAlternate && isMobile) {
    const direction = options.mobileIndex % 2 === 0 ? 1 : -1
    return { x: direction * mobileDistance, y: 0 }
  }

  const distance = isMobile ? mobileDistance : desktopDistance

  switch (options.type) {
    case 'title':
    case 'fade-up':
    case 'contact-up':
    case 'project-card':
      return { x: 0, y: distance }
    case 'card-right':
      return { x: distance, y: 0 }
    case 'card-left':
    case 'review-left':
      return { x: -distance, y: 0 }
    default:
      return { x: 0, y: distance }
  }
}

const setRevealInitialState = (el, options) => {
  const offset = resolveRevealOffset(options)
  el.style.opacity = '0'
  el.style.transform = `translate3d(${offset.x}px, ${offset.y}px, 0)`
  el.style.willChange = 'opacity, transform'
}

const playRevealAnimation = (el, options) => {
  const isReducedMotion = getReducedMotion()
  const offset = resolveRevealOffset(options)

  if (isReducedMotion) {
    el.style.opacity = '1'
    el.style.transform = 'none'
    return
  }

  const duration = options.duration || (getMobileViewport() ? 640 : 900)
  const delay = Math.max(0, options.delay || 0)

  if (typeof el.animate !== 'function') {
    el.style.transition = `opacity ${duration}ms ${EASE_PREMIUM} ${delay}s, transform ${duration}ms ${EASE_PREMIUM} ${delay}s`
    el.style.opacity = '1'
    el.style.transform = 'none'
    window.setTimeout(() => {
      el.style.transition = ''
      el.style.willChange = 'auto'
    }, duration + delay * 1000 + 40)
    return
  }

  const animation = el.animate(
    [
      { opacity: 0, transform: `translate3d(${offset.x}px, ${offset.y}px, 0)` },
      { opacity: 1, transform: 'translate3d(0, 0, 0)' },
    ],
    {
      duration,
      delay: delay * 1000,
      easing: EASE_PREMIUM,
      fill: 'forwards',
    },
  )

  animation.onfinish = () => {
    el.style.opacity = '1'
    el.style.transform = 'none'
    el.style.willChange = 'auto'
  }
}

export const revealDirective = {
  mounted(el, binding) {
    const options = parseRevealOptions(binding)

    if (getReducedMotion()) {
      el.style.opacity = '1'
      el.style.transform = 'none'
      return
    }

    setRevealInitialState(el, options)

    const observer = new IntersectionObserver(
      (entries) => {
        const hasIntersecting = entries.some((entry) => entry.isIntersecting)
        if (!hasIntersecting) return

        playRevealAnimation(el, options)

        if (options.once !== false) {
          observer.disconnect()
        }
      },
      {
        threshold: 0.16,
        rootMargin: '0px 0px -10% 0px',
      },
    )

    observer.observe(el)
    el[REVEAL_SYMBOL] = { observer }
  },
  unmounted(el) {
    const state = el[REVEAL_SYMBOL]
    if (state?.observer) {
      state.observer.disconnect()
    }
    delete el[REVEAL_SYMBOL]
  },
}

const parseParallaxSpeed = (binding) => {
  const speed = Number(binding?.value)
  if (Number.isNaN(speed)) return 0.06
  return speed
}

const shouldEnableParallax = () => {
  if (typeof window === 'undefined') return false
  if (getReducedMotion()) return false
  return window.innerWidth >= 1024
}

export const parallaxDirective = {
  mounted(el, binding) {
    if (!shouldEnableParallax()) return

    const speed = parseParallaxSpeed(binding)
    let rafId = null

    const update = () => {
      const rect = el.getBoundingClientRect()
      const viewportHeight = window.innerHeight || 0
      const centerDelta = rect.top + rect.height / 2 - viewportHeight / 2
      const offset = -(centerDelta * speed) / 10

      el.style.transform = `translate3d(0, ${offset.toFixed(2)}px, 0)`
      el.style.willChange = 'transform'
      rafId = null
    }

    const requestUpdate = () => {
      if (rafId !== null) return
      rafId = window.requestAnimationFrame(update)
    }

    requestUpdate()
    window.addEventListener('scroll', requestUpdate, { passive: true })
    window.addEventListener('resize', requestUpdate)

    el[PARALLAX_SYMBOL] = {
      requestUpdate,
      cleanup: () => {
        if (rafId !== null) {
          window.cancelAnimationFrame(rafId)
          rafId = null
        }
        window.removeEventListener('scroll', requestUpdate)
        window.removeEventListener('resize', requestUpdate)
        el.style.transform = 'none'
        el.style.willChange = 'auto'
      },
    }
  },
  unmounted(el) {
    const state = el[PARALLAX_SYMBOL]
    if (state?.cleanup) {
      state.cleanup()
    }
    delete el[PARALLAX_SYMBOL]
  },
}
