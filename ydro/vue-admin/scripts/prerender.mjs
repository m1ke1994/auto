import {build} from 'vite'
import vue from '@vitejs/plugin-vue'
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
import {savePage,discovery,SITE} from './seo.mjs'
import { marketingPageList } from '../src/content/marketingPages.js'
const temp='.seo-render'
const mode=process.argv.includes('--example')?'example':'production'
mkdirSync(temp,{recursive:true})
writeFileSync(`${temp}/entry.js`, `
import {createSSRApp,h} from 'vue';import {renderToString} from '@vue/server-renderer';
import {createRouter,createMemoryHistory,RouterView} from 'vue-router';
import Landing from '../src/views/LandingPage.vue';import Legal from '../src/views/LegalPage.vue';
import Marketing from '../src/views/MarketingPage.vue';import { marketingPageList } from '../src/content/marketingPages.js';
export async function render(path){const router=createRouter({history:createMemoryHistory(),routes:[{path:'/',component:Landing},...marketingPageList.map(page=>({path:page.path,component:Marketing,props:{pageKey:page.key}})),...['privacy','terms','consent','cookies'].map(type=>({path:'/'+type,component:Legal,props:{type}}))]});await router.push(path);return renderToString(createSSRApp({render:()=>h(RouterView)}).use(router));}`)
try {
 await build({configFile:false,mode,plugins:[vue()],build:{ssr:resolve(`${temp}/entry.js`),outDir:`${temp}/out`,rollupOptions:{output:{entryFileNames:'entry.mjs'}}},logLevel:'error'})
 const {render}=await import(pathToFileURL(resolve(`${temp}/out/entry.mjs`)))
 const template=readFileSync('dist/index.html','utf8')
 savePage(template,await render('/'))
 for(const page of marketingPageList) savePage(template,await render(page.path),{path:page.path,title:page.title,description:page.description})
 const legal={privacy:'Политика обработки персональных данных',terms:'Условия использования',consent:'Согласие на обработку персональных данных',cookies:'Политика использования cookies'}
 for(const [type,label] of Object.entries(legal))savePage(template,await render('/'+type),{path:'/'+type,title:`${label} | TrackNode`,description:`${label}: документы платформы TrackNode.`})
 discovery(['/',...marketingPageList.map(page=>page.path),...Object.keys(legal).map(x=>'/'+x)])
 console.log('SEO: TrackNode, 4 commercial and 4 legal pages prerendered as HTML.')
}finally{rmSync(temp,{recursive:true,force:true})}
