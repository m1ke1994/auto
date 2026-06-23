import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { extname, resolve } from 'node:path'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

function xmlEscape(value) {
  return value.replace(/[<>&'"]/g, (character) => ({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    "'": '&apos;',
    '"': '&quot;',
  })[character])
}

const insecureProtocol = 'http:' + '//'
const forbiddenProductionHttpUrls = [
  `${insecureProtocol}tracknode.ru`,
  `${insecureProtocol}www.tracknode.ru`,
  `${insecureProtocol}leelabird.ru`,
  `${insecureProtocol}www.leelabird.ru`,
]

const scannedBuildExtensions = new Set([
  '.css',
  '.html',
  '.js',
  '.json',
  '.map',
  '.svg',
  '.txt',
  '.webmanifest',
  '.xml',
])

function listBuildFiles(directory) {
  if (!existsSync(directory)) return []
  return readdirSync(directory).flatMap((entry) => {
    const path = resolve(directory, entry)
    if (statSync(path).isDirectory()) return listBuildFiles(path)
    return [path]
  })
}

function assertNoForbiddenProductionHttpUrls(directory) {
  const offenders = []
  for (const file of listBuildFiles(directory)) {
    if (!scannedBuildExtensions.has(extname(file))) continue
    const content = readFileSync(file, 'utf8')
    const found = forbiddenProductionHttpUrls.filter((url) => content.includes(url))
    if (found.length) offenders.push(`${file}: ${found.join(', ')}`)
  }

  if (offenders.length) {
    throw new Error(`Production build contains insecure HTTP production URLs:\n${offenders.join('\n')}`)
  }
}

export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, process.cwd(), '')
  const siteUrl = String(
    process.env.VITE_PUBLIC_SITE_URL ||
      process.env.VITE_SITE_URL ||
      fileEnv.VITE_PUBLIC_SITE_URL ||
      fileEnv.VITE_SITE_URL ||
      'http://localhost:5173',
  ).replace(/\/+$/, '')

  return {
    plugins: [
      vue(),
      {
        name: 'production-seo-files',
        closeBundle() {
          const robots = [
            'User-agent: *',
            'Allow: /',
            'Disallow: /api/',
            'Disallow: /admin/',
            'Disallow: /dashboard',
            'Disallow: /login',
            'Disallow: /sites/',
            'Disallow: /mini',
            '',
            `Sitemap: ${siteUrl}/sitemap.xml`,
            '',
          ].join('\n')
          const sitemap = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '  <url>',
            `    <loc>${xmlEscape(siteUrl)}/</loc>`,
            '    <changefreq>weekly</changefreq>',
            '    <priority>1.0</priority>',
            '  </url>',
            '</urlset>',
            '',
          ].join('\n')

          writeFileSync(resolve('dist/robots.txt'), robots, 'utf8')
          writeFileSync(resolve('dist/sitemap.xml'), sitemap, 'utf8')
          assertNoForbiddenProductionHttpUrls(resolve('dist'))
        },
      },
    ],
  }
})
