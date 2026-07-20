import AMeditationTemplate from './AMeditationTemplate.vue'
import ArtStroyTemplate from './ArtStroyTemplate.vue'

export const templateRegistry = Object.freeze({
  'a-meditation': AMeditationTemplate,
  'art-troy': ArtStroyTemplate,
})

export const supportedTemplateKeys = Object.freeze(Object.keys(templateRegistry))
const legacyTemplateKeysBySlug = Object.freeze({ 'a-meditation': 'a-meditation' })

export function resolveTemplateComponent(key, siteSlug = '') {
  const resolvedKey = String(key || '').trim() || legacyTemplateKeysBySlug[String(siteSlug || '').trim()] || ''
  return templateRegistry[resolvedKey] || null
}
