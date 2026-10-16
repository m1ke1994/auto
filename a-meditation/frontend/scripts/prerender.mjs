import {build} from 'vite'
import vue from '@vitejs/plugin-vue'
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
import {savePage,discovery,publicBundle} from './seo.mjs'
const temp='.seo-render';mkdirSync(temp,{recursive:true})
const bundle=await publicBundle(process.env.VITE_SITE_SLUG || 'a-meditation')
writeFileSync(`${temp}/entry.js`, `import {createSSRApp} from 'vue';import {renderToString} from '@vue/server-renderer';import App from '../src/App.vue';export function render(bundle){return renderToString(createSSRApp(App).provide('seo-public-content',bundle))}`)
try{
 await build({configFile:false,plugins:[vue()],build:{ssr:resolve(`${temp}/entry.js`),outDir:`${temp}/out`,rollupOptions:{output:{entryFileNames:'entry.mjs'}}},logLevel:'error'})
 const {render}=await import(pathToFileURL(resolve(`${temp}/out/entry.mjs`)))
 const body=await render(bundle);savePage(readFileSync('dist/index.html','utf8'),body);discovery(['/'])
 console.log('SEO: Leelabird HTML and platform attribution generated.')
 writeFileSync('dist/404.html','<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><title>Страница не найдена</title></head><body><main><h1>Страница не найдена</h1><a href="/">На главную</a></main><footer><a href="https://tracknode.ru/">by TrackNode</a></footer></body></html>')
}finally{rmSync(temp,{recursive:true,force:true})}
