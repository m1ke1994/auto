import assert from 'node:assert/strict'
import { normalizeCategory, normalizePriority, normalizeResult, plainMarkdown } from '../src/utils/aiRecommendations.js'

const structured = normalizeResult({ summary: 'Итог', score: 72, recommendations: [{ id: '1', title: 'Ускорьте сайт', category: 'performance', priority: 'very_important', why_important: 'Посетители могут уйти.', actions: ['Сжать изображения'], benefit: 'Больше посетителей увидят услуги.' }] })
assert.equal(structured.recommendations.length, 1)
assert.equal(structured.recommendations[0].category, 'Производительность')
assert.equal(structured.recommendations[0].priority, 'high')
assert.deepEqual(structured.recommendations[0].actions, ['Сжать изображения'])

const legacyObject = normalizeResult({ recommendations: [{ name: 'Проверить форму', problem: 'Мало обращений', recommendation: 'Сократить количество полей', priority: 'medium', category: 'forms', evidence: ['Есть посещения'], expected_impact: 'Больше заявок' }] })
assert.equal(legacyObject.recommendations[0].category, 'Формы и заявки')
assert.equal(legacyObject.recommendations[0].effect, 'Больше заявок')

const legacyText = normalizeResult('## Общий совет\n\n**Сделайте** предложение понятнее.')
assert.equal(legacyText.recommendations.length, 1)
assert.ok(!legacyText.recommendations[0].description.includes('**'))
assert.equal(plainMarkdown('[Текст](https://example.test)'), 'Текст')
assert.equal(normalizeCategory('mobile_ux'), 'Мобильная версия')
assert.equal(normalizePriority(undefined), 'neutral')
assert.deepEqual(normalizeResult(null).recommendations, [])

console.log('AI recommendations normalization checks passed')
