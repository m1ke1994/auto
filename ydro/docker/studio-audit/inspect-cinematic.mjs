import { chromium } from 'playwright'
import fs from 'node:fs/promises'

const studioUrl = process.env.STUDIO_URL || 'http://127.0.0.1:8001'
const email = process.env.STUDIO_TEST_EMAIL
const password = process.env.STUDIO_TEST_PASSWORD
const projectName = process.env.STUDIO_PROJECT_NAME
if (!email || !password || !projectName) throw new Error('Studio credentials and project name are required')

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const studio = await context.newPage()
const report = { projectName, consoleErrors: [], pageErrors: [], requestFailures: [] }

function observe(page) {
  page.on('console', message => {
    if (message.type() === 'error') report.consoleErrors.push({ url: page.url(), text: message.text() })
  })
  page.on('pageerror', error => report.pageErrors.push({ url: page.url(), text: String(error) }))
  page.on('requestfailed', request => report.requestFailures.push({
    url: request.url().replace(/([?&](?:token|key)=)[^&]+/gi, '$1<redacted>'),
    reason: request.failure()?.errorText || 'unknown',
  }))
}

observe(studio)
try {
  await studio.goto(`${studioUrl}/login?redirect=/studio`, { waitUntil: 'networkidle', timeout: 30000 })
  await studio.locator('#auth-email').fill(email)
  await studio.locator('#auth-password').fill(password)
  await Promise.all([
    studio.waitForURL(url => url.pathname === '/studio', { timeout: 30000 }),
    studio.locator('button[type="submit"]').click(),
  ])
  await studio.getByRole('heading', { name: 'Studio', exact: true }).waitFor({ timeout: 30000 })
  await studio.getByRole('button', { name: new RegExp(`^${projectName.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&')}`) }).first().click()
  await studio.waitForFunction(expected => document.querySelector('.workspace aside h2')?.textContent?.trim() === expected, projectName)
  const iframe = studio.locator('iframe[title="Кинематографический предпросмотр сайта"]')
  await iframe.waitFor({ state: 'visible', timeout: 20000 })
  await iframe.contentFrame().locator('h1').first().waitFor({ state: 'visible', timeout: 20000 })
  await studio.screenshot({ path: '/report/velora-studio.png', fullPage: true })

  const src = await iframe.getAttribute('src')
  if (!src) throw new Error('Studio preview iframe has no src')
  const preview = await context.newPage()
  observe(preview)
  await preview.goto(new URL(src, studio.url()).href, { waitUntil: 'networkidle', timeout: 45000 })
  await preview.locator('[data-tn-model]').first().waitFor({ state: 'visible', timeout: 20000 })
  await preview.waitForFunction(() => document.querySelector('[data-tn-model]')?.dataset.tnModelState === 'ready', null, { timeout: 20000 })
  const firstPose = await preview.locator('[data-tn-model]').first().getAttribute('data-tn-camera-pose')
  await preview.screenshot({ path: '/report/velora-preview-desktop.png', fullPage: true, timeout: 45000 })
  await preview.locator('[data-tn-about-metrics]').scrollIntoViewIfNeeded()
  await preview.waitForFunction(() => document.querySelector('[data-tn-about-metrics]')?.dataset.tnMetricState === 'complete', null, { timeout: 5000 })
  await preview.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight * .3, behavior: 'instant' }))
  await preview.waitForTimeout(650)
  const movedPose = await preview.locator('[data-tn-model]').first().getAttribute('data-tn-camera-pose')
  report.desktop = await preview.evaluate(() => ({
    title: document.title,
    h1: document.querySelector('h1')?.textContent?.trim() || '',
    sections: document.querySelectorAll('[data-tn-section]').length,
    modelState: document.querySelector('[data-tn-model]')?.dataset.tnModelState || '',
    metricState: document.querySelector('[data-tn-about-metrics]')?.dataset.tnMetricState || '',
    metrics: [...document.querySelectorAll('[data-tn-metric-value]')].map(node => node.dataset.tnMetricValue),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    brokenImages: [...document.images].filter(image => image.complete && !image.naturalWidth).length,
  }))
  report.desktop.cameraMoved = Boolean(firstPose && movedPose && firstPose !== movedPose)

  await preview.setViewportSize({ width: 390, height: 844 })
  await preview.reload({ waitUntil: 'networkidle' })
  await preview.waitForFunction(() => document.querySelector('[data-tn-model]')?.dataset.tnModelState === 'ready', null, { timeout: 20000 })
  report.mobile = await preview.evaluate(() => ({
    h1Visible: Boolean(document.querySelector('h1')?.getBoundingClientRect().height),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    brokenImages: [...document.images].filter(image => image.complete && !image.naturalWidth).length,
  }))
  await preview.screenshot({ path: '/report/velora-preview-mobile.png', fullPage: true, timeout: 45000 })
  await preview.close()
} finally {
  await fs.writeFile('/report/velora-studio-report.json', JSON.stringify(report, null, 2))
  await browser.close()
}

const invalid = report.consoleErrors.length || report.pageErrors.length || report.requestFailures.length ||
  report.desktop?.modelState !== 'ready' || report.desktop?.metricState !== 'complete' ||
  report.desktop?.metrics?.join('|') !== '100%|2000+|2.5' || !report.desktop?.cameraMoved ||
  report.desktop?.overflow > 2 || report.desktop?.brokenImages || !report.mobile?.h1Visible ||
  report.mobile?.overflow > 2 || report.mobile?.brokenImages
console.log(JSON.stringify(report, null, 2))
if (invalid) process.exit(1)
