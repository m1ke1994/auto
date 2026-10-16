import { publicSiteUrl } from '../config/api'
const origin = publicSiteUrl || 'https://novoe-konakovo.ru'
export function applyPageSeo({path, title, description, image, noindex=false}) {
  if (typeof document === 'undefined') return
  const canonical=origin+path.split(/[?#]/)[0]
  const text=String(description || title).replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim().slice(0,220)
  const meta=(attribute,name,content)=>{
    let el=document.head.querySelector(`meta[${attribute}="${name}"]`)
    if(!el){el=document.createElement('meta');el.setAttribute(attribute,name);document.head.appendChild(el)}
    el.content=content
  }
  document.title=title
  meta('name','description',text)
  meta('name','robots',noindex?'noindex,follow':'index,follow,max-image-preview:large')
  for(const [name,value] of Object.entries({'og:title':title,'og:description':text,'og:url':canonical,'og:type':'website','og:site_name':'Новое Конаково'}))meta('property',name,value)
  meta('name','twitter:title',title);meta('name','twitter:description',text)
  if(image){meta('property','og:image',image);meta('name','twitter:image',image)}
  let link=document.head.querySelector('link[rel="canonical"]')
  if(!link){link=document.createElement('link');link.rel='canonical';document.head.appendChild(link)}
  link.href=canonical
  let schema=document.getElementById('route-page-json-ld')
  if(!schema){schema=document.createElement('script');schema.type='application/ld+json';schema.id='route-page-json-ld';document.head.appendChild(schema)}
  schema.textContent=JSON.stringify({'@context':'https://schema.org','@type':'WebPage','@id':canonical+'#webpage',url:canonical,name:title,description:text,isPartOf:{'@id':origin+'/#website'}})
}
