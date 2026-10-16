import {build} from 'vite'
import vue from '@vitejs/plugin-vue'
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
import {savePage,discovery,publicBundle,SITE} from './seo.mjs'
const temp='.seo-render';mkdirSync(temp,{recursive:true})
const bundle=await publicBundle(process.env.VITE_SITE_SLUG || 'novaya-konakova')
writeFileSync(`${temp}/entry.js`, `
import {createSSRApp,h} from 'vue';import {renderToString} from '@vue/server-renderer';import {RouterView} from 'vue-router';
import router from '../src/router/index.js';import {seedSsrPublicSite,getJsonSectionItems} from '../src/api/publicSite.js';
import {loadServices,useServices} from '../src/composables/useServices.js';import {revealDirective} from '../src/composables/useRevealOnScroll.js';
export async function pages(bundle) {
 seedSsrPublicSite(bundle);await loadServices();
 const [articles,news,contentPages]=await Promise.all(['articles','news','pages'].map(key=>getJsonSectionItems(key)));
 const routes=router.getRoutes().filter(r=>!r.redirect&&!r.path.includes(':')).map(r=>({path:r.path,title:typeof r.meta.title==='string'?r.meta.title:'',description:r.meta.description}));
 const editorial=['/about','/volunteer','/running-club','/brotherhood'];
 const output=routes.filter(r=>!editorial.includes(r.path)||contentPages.some(p=>'/'+p.slug===r.path));
 const segment=s=>encodeURIComponent(String(s));
 for(const row of articles)if(row.slug&&row.title)output.push({path:'/articles/'+segment(row.slug),title:row.title+' — Новое Конаково',description:row.preview_description});
 for(const row of news)if(row.slug&&row.title)output.push({path:'/news/'+segment(row.slug),title:row.title+' — Новое Конаково',description:row.description});
 function services(rows){for(const row of rows){if(row.path)output.push({path:'/services/'+row.path.split('/').map(segment).join('/'),title:(row.fullTitle||row.title)+' — Новое Конаково',description:row.description});services(row.children||[])}}
 services(useServices().servicesTree.value);return output;
}
export async function render(path){await router.push(path);await router.isReady();return renderToString(createSSRApp({render:()=>h(RouterView)}).use(router).directive('reveal',revealDirective))}
`)
try{
 await build({configFile:false,plugins:[vue()],resolve:{alias:{"@":resolve("src")}},build:{ssr:resolve(`${temp}/entry.js`),outDir:`${temp}/out`,rollupOptions:{output:{entryFileNames:'entry.mjs'}}},logLevel:'error'})
 const {render,pages}=await import(pathToFileURL(resolve(`${temp}/out/entry.mjs`)))
 const template=readFileSync('dist/index.html','utf8');const entries=await pages(bundle)
 for(const page of entries){const body=await render(page.path);savePage(template,body,{...page,title:page.path==='/'?SITE.title:page.title,description:String(page.path==='/'?SITE.description:(page.description||SITE.description)).replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim()})}
 discovery(entries.map(p=>p.path));console.log(`SEO: ${entries.length} Konakovo pages prerendered with per-page canonical URLs.`)
}finally{rmSync(temp,{recursive:true,force:true})}
