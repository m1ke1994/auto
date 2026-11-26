import { chromium } from 'playwright'
import fs from 'node:fs/promises'

const base = process.env.STUDIO_URL || 'http://127.0.0.1:8001'
const email = process.env.STUDIO_TEST_EMAIL
const password = process.env.STUDIO_TEST_PASSWORD
const reuseProjects = process.env.STUDIO_REUSE_PROJECTS === '1'
if (!email || !password) throw new Error('STUDIO_TEST_EMAIL and STUDIO_TEST_PASSWORD are required')

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
const report = { base, consoleErrors: [], pageErrors: [], requestFailures: [], generations: [] }

page.on('console', message => {
  if (message.type() === 'error') report.consoleErrors.push(message.text())
})
page.on('pageerror', error => report.pageErrors.push(String(error)))
page.on('requestfailed', request => report.requestFailures.push({
  url: request.url().replace(/([?&](?:token|key)=)[^&]+/gi, '$1<redacted>'),
  reason: request.failure()?.errorText || 'unknown',
}))

async function createProject({ name, prompt, style }) {
  await page.getByRole('button', { name: /Новый проект/ }).click().catch(() => {})
  const form = page.locator('form.create-form')
  await form.locator('input[required]').fill(name)
  await form.locator('textarea[required]').first().fill(prompt)
  await form.locator('select').nth(0).selectOption('quick')
  await form.locator('select').nth(1).selectOption(style)
  const started = Date.now()
  await Promise.all([
    page.waitForResponse(response => response.url().includes('/api/studio/projects/') && response.request().method() === 'POST', { timeout: 120000 }),
    form.getByRole('button', { name: /быструю концепцию/i }).click(),
  ]).then(async ([response]) => {
    const body = await response.json().catch(() => ({}))
    if (response.status() !== 201) throw new Error(`Generation failed: HTTP ${response.status()} ${JSON.stringify(body)}`)
    report.generations.push({ name, style, status: response.status(), projectId: body.id, revisionId: body.revisions?.[0]?.id, durationMs: Date.now() - started })
  })
  await page.locator('iframe[title="Предпросмотр сайта"]').waitFor({ state: 'visible', timeout: 15000 })
  const frame = page.frameLocator('iframe[title="Предпросмотр сайта"]')
  await frame.locator('h1').waitFor({ state: 'visible', timeout: 15000 })
  const heading = await frame.locator('h1').innerText()
  if (!heading.trim()) throw new Error('Generated preview has an empty H1')
  report.generations.at(-1).heading = heading.trim()
}

try {
  await page.goto(`${base}/login?redirect=/studio`, { waitUntil: 'networkidle', timeout: 30000 })
  await page.locator('#auth-email').fill(email)
  await page.locator('#auth-password').fill(password)
  await Promise.all([
    page.waitForURL('**/studio', { timeout: 30000 }),
    page.locator('button[type="submit"]').click(),
  ])
  await page.getByRole('heading', { name: 'Studio', exact: true }).waitFor({ timeout: 30000 })
  report.providerBadge = await page.locator('.badge').innerText()

  if (reuseProjects) {
    await page.getByRole('button', { name: /^Northline Objects · Quick \/ макет$/ }).first().click()
    await page.locator('iframe[title="Предпросмотр сайта"]').waitFor({ state: 'visible', timeout: 15000 })
  } else {
    await createProject({
      name: 'Aurora Coffee Lab',
      prompt: 'Премиальная кофейня и обжарочная лаборатория. Нужен выразительный сайт с историей происхождения зерна, меню и контактами. Не выдумывать цены и адрес.',
      style: 'cinema',
    })
    await createProject({
      name: 'Northline Objects',
      prompt: 'Студия предметного дизайна: светильники, мебель и малые серии. Нужны портфолио, подход, этапы работы и форма контакта без вымышленных кейсов.',
      style: 'premium',
    })
  }

  const metrics = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }))
  report.noHorizontalOverflow = metrics.width <= metrics.viewport + 1
  await page.screenshot({ path: '/report/studio-two-generations.png', fullPage: true })

  await page.setViewportSize({ width: 390, height: 844 })
  await page.waitForTimeout(500)
  await page.getByRole('button', { name: 'Телефон' }).click()
  await page.frameLocator('iframe[title="Предпросмотр сайта"]').locator('h1').waitFor({ state: 'visible', timeout: 15000 })
  await page.waitForTimeout(500)
  await page.screenshot({ path: '/report/studio-mobile-preview.png', fullPage: true })
  const mobileMetrics = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }))
  report.mobileNoHorizontalOverflow = mobileMetrics.width <= mobileMetrics.viewport + 1
} finally {
  await fs.writeFile('/report/studio-flow-report.json', JSON.stringify(report, null, 2))
  await browser.close()
}

if (report.consoleErrors.length || report.pageErrors.length || report.requestFailures.length || !report.noHorizontalOverflow || !report.mobileNoHorizontalOverflow || (!reuseProjects && report.generations.length !== 2)) {
  console.error(JSON.stringify(report, null, 2))
  process.exit(1)
}
console.log(JSON.stringify(report, null, 2))
