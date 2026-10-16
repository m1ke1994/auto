import assert from 'node:assert/strict'
import { build } from 'vite'
import vue from '@vitejs/plugin-vue'
import { mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
const temp = '.landing-render-check'
mkdirSync(temp, { recursive: true })
writeFileSync(`${temp}/entry.js`, `
import {createSSRApp} from 'vue'
import {renderToString} from '@vue/server-renderer'
import {createRouter,createMemoryHistory,RouterView} from 'vue-router'
import {h} from 'vue'
import Landing from '../src/views/LandingPage.vue'
import Legal from '../src/views/LegalPage.vue'
export async function render(path) {
 const router=createRouter({history:createMemoryHistory(),routes:[{path:'/',component:Landing},...['privacy','terms','consent','cookies'].map(type=>({path:'/'+type,component:Legal,props:{type}}))]})
 await router.push(path)
 return renderToString(createSSRApp({render:()=>h(RouterView)}).use(router))
}`)
try {
 await build({ configFile:false, mode:'example', plugins:[vue()], build:{ssr:resolve(`${temp}/entry.js`),outDir:`${temp}/out`,rollupOptions:{output:{entryFileNames:'entry.mjs'}}},logLevel:'error' })
 const {render}=await import(pathToFileURL(resolve(`${temp}/out/entry.mjs`)))
 const html=await render('/')
 assert.match(html, /Меньше хаоса/)
 assert.match(html, /href="\/login"/)
 assert.match(html, /href="\/register"/)
 assert.match(html, /cube-host/)
 assert.match(html, /name="consent"|type="checkbox"/)
 for(const path of ['/privacy','/terms','/consent','/cookies']) {
  const document=await render(path)
  assert.match(document, /<h1[\s>]/)
  assert.ok(document.length>2500, path)
 }
 console.log('Landing and four existing legal pages render successfully; login/register links and consent are present.')
} finally { rmSync(temp,{recursive:true,force:true}) }
