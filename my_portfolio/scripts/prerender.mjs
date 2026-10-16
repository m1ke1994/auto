import {build} from 'vite'
import react from '@vitejs/plugin-react-swc'
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
import {savePage,discovery,publicBundle} from './seo.mjs'
const temp='.seo-render';mkdirSync(temp,{recursive:true})
const bundle=await publicBundle(process.env.VITE_SITE_SLUG || 'my-portfolio')
writeFileSync(`${temp}/entry.tsx`, `import React from 'react';import {renderToString} from 'react-dom/server';import Index from '../src/pages/Index';import {PortfolioProvider} from '../src/lib/tracknode';import {ContactModalProvider} from '../src/components/ContactModal';export function render(bundle){return renderToString(<PortfolioProvider initialBundle={bundle || undefined}><ContactModalProvider><Index/></ContactModalProvider></PortfolioProvider>)}`)
try{
 await build({configFile:false,plugins:[react()],resolve:{alias:{'@':resolve('src')}},build:{ssr:resolve(`${temp}/entry.tsx`),outDir:`${temp}/out`,rollupOptions:{output:{entryFileNames:'entry.mjs'}}},logLevel:'error'})
 const {render}=await import(pathToFileURL(resolve(`${temp}/out/entry.mjs`)))
 savePage(readFileSync('dist/index.html','utf8'),render(bundle).replace(/opacity:0(?=;|")/g,'opacity:1'));discovery(['/'])
 console.log('SEO: portfolio content and TrackNode credit prerendered.')
 writeFileSync('dist/404.html','<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><title>Страница не найдена</title></head><body><main><h1>Страница не найдена</h1><a href="/">На главную</a></main><footer><a href="https://tracknode.ru/">by TrackNode</a></footer></body></html>')
}finally{rmSync(temp,{recursive:true,force:true})}
