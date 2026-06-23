const prefersReducedMotion = () =>
  window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches

let sharedObserver = null

const getObserver = () => {
  if (sharedObserver || typeof window === "undefined") {
    return sharedObserver
  }

  sharedObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return

        const el = entry.target
        el.classList.add("reveal--in", "reveal--animating")

        const onTransitionEnd = (event) => {
          if (event.propertyName === "opacity" || event.propertyName === "transform") {
            el.classList.remove("reveal--animating")
          }
        }

        el.addEventListener("transitionend", onTransitionEnd, { once: true })
        sharedObserver.unobserve(el)
      })
    },
    { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
  )

  return sharedObserver
}

const applyRevealClasses = (el, binding) => {
  el.classList.add("reveal")
  if (binding?.modifiers?.right) {
    el.classList.add("reveal--right")
  } else {
    el.classList.add("reveal--left")
  }

  const delay = Number.parseInt(binding?.value, 10)
  if (!Number.isNaN(delay)) {
    el.style.setProperty("--reveal-delay", `${delay}ms`)
  }
}

export const revealDirective = {
  mounted(el, binding) {
    applyRevealClasses(el, binding)

    if (typeof window === "undefined") return

    if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
      el.classList.add("reveal--in")
      return
    }

    const observer = getObserver()
    observer?.observe(el)
  },
  updated(el, binding) {
    applyRevealClasses(el, binding)
  },
  unmounted(el) {
    sharedObserver?.unobserve(el)
  },
}

export const useRevealOnScroll = () => revealDirective
