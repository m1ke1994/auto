export const clamp = (n, min = 0, max = 1) => Math.min(max, Math.max(min, n))
export function smoothRange(value, from, to) {
  const t = clamp((value - from) / (to - from))
  return t * t * (3 - 2 * t)
}
export function sampleStory(value) {
  const progress = clamp(value)
  return {
    progress,
    explode: smoothRange(progress, 0.08, 0.34),
    resolve: smoothRange(progress, 0.3, 0.51),
    orbit: smoothRange(progress, 0, 0.52),
    active:
      progress < 0.48 ? -1 : Math.min(3, Math.floor((progress - 0.48) / 0.13)),
  }
}
