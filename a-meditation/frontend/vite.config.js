import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { extname, resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

function csv(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

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
  const env = loadEnv(mode, process.cwd(), '')
  const allowedHosts = csv(env.VITE_DEV_ALLOWED_HOSTS)
  const proxyTarget = String(env.VITE_DEV_API_PROXY_TARGET || '').trim()
  const publicSiteUrl = String(
    env.VITE_PUBLIC_SITE_URL || env.VITE_SITE_URL || 'https://leelabird.ru',
  ).replace(/\/+$/, '')

  return {
    plugins: [
      vue(),
      {
        name: 'public-seo-files',
        closeBundle() {
          const robots = [
            'User-agent: *',
            'Allow: /',
            '',
            `Sitemap: ${publicSiteUrl}/sitemap.xml`,
            '',
          ].join('\n')
          const sitemap = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '  <url>',
            `    <loc>${xmlEscape(publicSiteUrl)}/</loc>`,
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
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            const normalizedId = id.replace(/\\/g, '/')
            if (normalizedId.includes('/node_modules/three/')) {
              return 'three'
            }
          },
        },
      },
    },
    server: {
      host: '0.0.0.0',
      port: Number(env.VITE_DEV_SERVER_PORT || 3000),
      strictPort: true,
      cors: true,
      ...(allowedHosts.length ? { allowedHosts } : {}),
      ...(proxyTarget
        ? {
            proxy: {
              '/api': {
                target: proxyTarget,
                changeOrigin: true,
              },
            },
          }
        : {}),
    },
  }
})
