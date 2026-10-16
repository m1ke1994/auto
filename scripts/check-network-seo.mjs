import assert from 'node:assert/strict'
import {readFileSync,existsSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
const projects=['ydro/vue-admin','my_portfolio','a-meditation/frontend','volga/frontend']
for(const root of projects){
 const {SITE,head,graph,publicBundle}=await import(pathToFileURL(resolve(root,'scripts/seo.mjs')))
 const html=readFileSync(root+'/dist/index.html','utf8')
 assert.match(html,/<h1[\s>]/,root+' must deliver a real heading before JavaScript')
 assert.match(html,/name="description" content="[^\"]{40,}"/)
 assert.match(html,/name="robots" content="index,follow/)
 assert.equal((html.match(/rel="canonical"/g)||[]).length,1)
 assert.ok(html.includes(`href="${SITE.url}/"`))
 assert.doesNotMatch(html,/%VITE_/)
 if(SITE.key!=='tracknode')assert.match(html,/>by TrackNode<\/a>/)
 const match=html.match(/<script id="tracknode-platform-json-ld" type="application\/ld\+json">([\s\S]*?)<\/script>/)
 const schema=JSON.parse(match[1]);assert.ok(schema['@graph'].some(x=>x['@id']==='https://tracknode.ru/#platform'))
 const website=schema['@graph'].find(x=>x['@type']==='WebSite')
 assert.equal(website.url,SITE.url+'/');assert.equal(website.creator['@id'],'https://tracknode.ru/#organization')
 const image=html.match(/property="og:image" content="([^"]*)"/)[1]
 if(image.startsWith(SITE.url))assert.ok(existsSync(root+'/public/'+image.slice(SITE.url.length+1)),root+' OG image must exist')
 const robots=readFileSync(root+'/dist/robots.txt','utf8');assert.ok(robots.includes(`Sitemap: ${SITE.url}/sitemap.xml`))
 const xml=readFileSync(root+'/dist/sitemap.xml','utf8');const urls=[...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1])
 assert.equal(new Set(urls).size,urls.length)
 for(const url of urls){assert.ok(url.startsWith(SITE.url+'/'));assert.doesNotMatch(url,/[?#]/);const pathname=new URL(url).pathname;assert.ok(existsSync(root+'/dist'+(pathname==='/'?'/index.html':pathname+'/index.html')),url+' must have HTML')}
 const escaped=head('<head><title>Old</title><meta name="description" content="old"><link rel="canonical" href="old"></head>',{title:'<bad> & "title"',description:'</script><script>bad</script>'})
 assert.doesNotMatch(escaped,/<script>bad/);assert.match(escaped,/&lt;bad&gt;/)
 const originalFetch=globalThis.fetch;globalThis.fetch=async()=>{throw Error('simulated unavailable API')};
 try{await assert.rejects(()=>publicBundle('unavailable-site'),/required before publishing/)}finally{globalThis.fetch=originalFetch}
 console.log('SEO OK:',SITE.name,urls.length,'HTML pages, correct canonical, attribution, JSON-LD and discovery files')
}
