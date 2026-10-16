import {mkdirSync,readFileSync,writeFileSync} from 'node:fs'
import {dirname,resolve} from 'node:path'
export const SITE = {"key": "konakovo", "url": "https://novoe-konakovo.ru", "name": "Новое Конаково", "title": "Новое Конаково — экскурсии, отдых на природе и мероприятия", "description": "Новое Конаково: экскурсии в Братство Лосей, авторские программы, мастер-классы и беговые встречи. Форматы отдыха, расписание, новости и контакты."}
export const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
export function graph(path='/', title=SITE.title, description=SITE.description) {
 const root=SITE.url+'/'
 const platform={'@type':'Organization','@id':'https://tracknode.ru/#organization',name:'TrackNode',url:'https://tracknode.ru/'}
 const app={'@type':'SoftwareApplication','@id':'https://tracknode.ru/#platform',name:'TrackNode',url:'https://tracknode.ru/',applicationCategory:'BusinessApplication',operatingSystem:'Web',description:'Платформа для сайтов, аналитики, заявок и технического SEO-аудита',publisher:{'@id':platform['@id']}}
 const website={'@type':'WebSite','@id':root+'#website',url:root,name:SITE.name,inLanguage:'ru-RU',creator:{'@id':platform['@id']}}
 if(SITE.key==='tracknode') website.publisher={'@id':platform['@id']}
 const webpage={'@type':SITE.key==='portfolio'?'ProfilePage':'WebPage','@id':SITE.url+path+'#webpage',url:SITE.url+path,name:title,description,inLanguage:'ru-RU',isPartOf:{'@id':website['@id']},mentions:{'@id':app['@id']}}
 const nodes=[platform,app,website,webpage]
 if(SITE.key==='portfolio') {const person={'@type':'Person','@id':root+'#person',name:'Александр Тишечкин',url:root,knowsAbout:['Веб-разработка','Vue','React','Django','Автоматизация','TrackNode']};nodes.push(person);webpage.mainEntity={'@id':person['@id']}}
 if(path!=='/') nodes.push({'@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:SITE.name,item:root},{'@type':'ListItem',position:2,name:title,item:SITE.url+path}]})
 return {'@context':'https://schema.org','@graph':nodes}
}
export function head(html,{path='/',title=SITE.title,description=SITE.description,noindex=false,image}={}) {
 const canonical=SITE.url+path
 html=html.replace(/<title>[\s\S]*?<\/title>/gi,'').replace(/<link\b[^>]*rel=["']canonical["'][^>]*>/gi,'')
 html=html.replace(/<meta\b[^>]*(?:name=["'](?:description|robots|twitter:[^"']+)["']|property=["']og:[^"']+["'])[^>]*>/gi,'')
 html=html.replace(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>[\s\S]*?<\/script>/gi,'')
 const picture=image || SITE.url+(SITE.key==='tracknode'?'/og-image.svg':SITE.key==='portfolio'?'/alex-presents-elegance.lovable.app.JPG':SITE.key==='leelabird'?'/images/Lila_Olga_2.2.poster.jpg':'/og-image.jpg')
 const meta=(name,value,property=false)=>`<meta ${property?'property':'name'}="${name}" content="${escape(value)}">`
 const tags=[`<title>${escape(title)}</title>`,meta('description',description),meta('robots',noindex?'noindex,follow':'index,follow,max-image-preview:large'),`<link rel="canonical" href="${escape(canonical)}">`,...Object.entries({'og:type':'website','og:locale':'ru_RU','og:site_name':SITE.name,'og:title':title,'og:description':description,'og:url':canonical,'og:image':picture}).map(([k,v])=>meta(k,v,true)),...Object.entries({'twitter:card':'summary_large_image','twitter:title':title,'twitter:description':description,'twitter:image':picture}).map(([k,v])=>meta(k,v)),`<script id="tracknode-platform-json-ld" type="application/ld+json">${JSON.stringify(graph(path,title,description)).replace(/</g,'\\u003c')}</script>`]
 return html.replace('</head>',tags.join('\n')+'\n</head>')
}
export function savePage(template,body,options={}) {
 const path=options.path || '/'
 const id=SITE.key==='portfolio'?'root':'app'
 const html=head(template,options).replace(new RegExp(`<div id="${id}">[\\s\\S]*<\\/div>`),()=>`<div id="${id}">${body}</div>`)
 const file=resolve('dist',path==='/'?'index.html':path.slice(1)+'/index.html')
 if (!file.startsWith(resolve('dist')+'/')) throw Error('Invalid page path')
 mkdirSync(dirname(file),{recursive:true});writeFileSync(file,html)
}
export function discovery(paths) {
 const unique=[...new Set(paths)]
 writeFileSync('dist/robots.txt',`User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin/\n${SITE.key==='tracknode'?'Disallow: /dashboard\nDisallow: /sites/\nDisallow: /mini\n':''}\nSitemap: ${SITE.url}/sitemap.xml\n`)
 writeFileSync('dist/sitemap.xml',`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${unique.map(path=>`<url><loc>${escape(SITE.url+path)}</loc></url>`).join('')}</urlset>`)
}
export async function publicBundle(slug) {
 if(process.env.SEO_CONTENT_FILE){const data=JSON.parse(readFileSync(process.env.SEO_CONTENT_FILE,'utf8'));if(data.site?.slug!==slug||!Array.isArray(data.sections))throw Error('Invalid SEO content fixture');return data}
 const base=(process.env.VITE_API_URL || 'https://tracknode.ru/api').replace(/\/$/,'')
 try {const r=await fetch(`${base}/sites/${slug}/`,{signal:AbortSignal.timeout(6000)});if(!r.ok)throw Error('HTTP '+r.status);const data=await r.json();if(!data.site || !Array.isArray(data.sections))throw Error('Invalid public content');return data}
 catch(e){if(process.env.SEO_ALLOW_DEFAULT_CONTENT!=='1')throw new Error('SEO public content is required before publishing: '+e.message);console.warn('SEO local verification: rendering defaults because public API is unavailable:',e.message);return null}
}
