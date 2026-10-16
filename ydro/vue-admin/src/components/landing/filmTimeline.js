import { clamp, smoothRange } from './storyMotion.js'
export const filmScenes = [
  { name: 'Начало', start: 0, end: 0.13 },
  { name: 'Связи', start: 0.13, end: 0.25 },
  { name: 'Аналитика', start: 0.25, end: 0.375 },
  { name: 'Заявки', start: 0.375, end: 0.5 },
  { name: 'SEO-аудит', start: 0.5, end: 0.625 },
  { name: 'Содержание', start: 0.625, end: 0.75 },
  { name: 'Единая система', start: 0.75, end: 0.875 },
  { name: 'Ваш следующий шаг', start: 0.875, end: 1 },
]
export function filmSceneAt(progress) {
  const index = filmScenes.findIndex(
    (scene) => clamp(progress) >= scene.start && clamp(progress) < scene.end,
  )
  return index < 0 ? 7 : index
}
export function filmCubeAt(progress) {
  return (
    clamp((progress - 0.08) / 0.2) * (1 - smoothRange(progress, 0.76, 0.95))
  )
}
export function filmSceneStyle(index, progress) {
  const scene = filmScenes[index]
  const appear =
    index === 0
      ? 1
      : smoothRange(progress, scene.start - 0.018, scene.start + 0.018)
  const disappear =
    index === 7
      ? 0
      : smoothRange(progress, scene.end - 0.018, scene.end + 0.018)
  const opacity = appear * (1 - disappear)
  return {
    opacity,
    transform: `translate3d(0,${(1 - appear) * 32 - disappear * 22}px,0) scale(${0.985 + 0.015 * opacity})`,
    visibility: opacity < 0.001 ? 'hidden' : 'visible',
  }
}
