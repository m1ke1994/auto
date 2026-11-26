import { chromium } from 'playwright'
import fs from 'node:fs/promises'

const studioUrl=process.env.STUDIO_URL||'http://127.0.0.1:8001'
const email=process.env.STUDIO_TEST_EMAIL
const password=process.env.STUDIO_TEST_PASSWORD
if(!email||!password)throw new Error('Studio test credentials are required')

const browser=await chromium.launch({headless:true})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const studio=await context.newPage()
const report={projects:[],consoleErrors:[],pageErrors:[],requestFailures:[],httpErrors:[]}
const bind=page=>{
  page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push({url:page.url(),text:m.text()})})
  page.on('pageerror',e=>report.pageErrors.push({url:page.url(),text:String(e)}))
  page.on('requestfailed',r=>report.requestFailures.push({url:r.url(),reason:r.failure()?.errorText||'unknown'}))
  page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:r.url(),status:r.status()})})
}
bind(studio)

async function inspectProject(name,slug,{requiresModel=false}={}){
  await studio.bringToFront()
  const previousSrc=await studio.locator('iframe[title="Кинематографический предпросмотр сайта"]').getAttribute('src').catch(()=>null)
  await studio.getByRole('button',{name:new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).first().click()
  await studio.waitForFunction(expected=>document.querySelector('.workspace aside h2')?.textContent?.trim()===expected,name,{timeout:20000})
  const iframe=studio.locator('iframe[title="Кинематографический предпросмотр сайта"]')
  await iframe.waitFor({state:'visible',timeout:20000})
  if(previousSrc)await studio.waitForFunction(({old})=>document.querySelector('iframe[title="Кинематографический предпросмотр сайта"]')?.getAttribute('src')!==old,{old:previousSrc},{timeout:20000})
  const src=await iframe.getAttribute('src')
  if(!src)throw new Error(`${name}: missing preview src`)
  const page=await context.newPage();bind(page)
  await page.goto(src,{waitUntil:'networkidle',timeout:45000})
  await page.locator('h1').first().waitFor({state:'visible',timeout:20000})
  let modelReady=true
  if(requiresModel)await page.waitForFunction(()=>document.querySelector('[data-tn-model]')?.dataset.tnModelState==='ready',{}, {timeout:20000}).catch(()=>{modelReady=false})
  const initial=await page.evaluate(()=>({
    title:document.title,h1:document.querySelector('h1')?.innerText?.trim()||'',
    text:document.body.innerText.length,sections:document.querySelectorAll('[data-tn-section]').length,
    scenes:document.querySelectorAll('[data-tn-scene]').length,
    carousels:document.querySelectorAll('[data-tn-carousel]').length,
    stories:document.querySelectorAll('[data-tn-story]').length,
    broken:[...document.images].filter(x=>x.complete&&!x.naturalWidth).length,
    overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
    model:document.querySelector('[data-tn-model]')?.dataset.tnModelState||null,
    modelFailure:document.querySelector('[data-tn-model]')?.dataset.tnModelFailure||null,
    pose:document.querySelector('[data-tn-model]')?.dataset.tnCameraPose||null,
  }))
  const scrollHeight=await page.evaluate(()=>document.documentElement.scrollHeight)
  for(let y=0;y<scrollHeight;y+=Math.max(520,Math.floor((await page.viewportSize()).height*.72))){
    await page.evaluate(top=>window.scrollTo({top,behavior:'instant'}),y)
    await page.waitForTimeout(70)
  }
  await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}))
  await page.waitForTimeout(500)
  await page.screenshot({path:`/report/${slug}-desktop.png`,fullPage:true,timeout:45000})
  await page.evaluate(()=>window.scrollTo({top:document.documentElement.scrollHeight*.28,behavior:'instant'}))
  await page.waitForTimeout(1000)
  const movedPose=await page.locator('[data-tn-model]').count()?await page.locator('[data-tn-model]').first().getAttribute('data-tn-camera-pose'):null
  await page.setViewportSize({width:390,height:844});await page.reload({waitUntil:'networkidle'});await page.waitForTimeout(600)
  const mobile=await page.evaluate(()=>({broken:[...document.images].filter(x=>x.complete&&!x.naturalWidth).length,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,h1Visible:!!document.querySelector('h1')?.getBoundingClientRect().height}))
  await page.screenshot({path:`/report/${slug}-mobile.png`,fullPage:true,timeout:45000})
  report.projects.push({name,src,initial,mobile,modelReady,cameraMoved:requiresModel&&initial.pose&&movedPose&&initial.pose!==movedPose})
  await page.close()
}

try{
  await studio.goto(`${studioUrl}/login?redirect=/studio`,{waitUntil:'networkidle',timeout:30000})
  await studio.locator('#auth-email').fill(email);await studio.locator('#auth-password').fill(password)
  await Promise.all([studio.waitForURL('**/studio',{timeout:30000}),studio.locator('button[type="submit"]').click()])
  await studio.getByRole('heading',{name:'Studio',exact:true}).waitFor({timeout:30000})
  await inspectProject('ÉLAN Beauty Atelier','beauty')
  await inspectProject('AUREON Automotive','automotive',{requiresModel:true})
  await inspectProject('MONOLITH Architecture','architecture')
  await studio.screenshot({path:'/report/studio-cinematic-projects.png',fullPage:true})
}finally{
  await fs.writeFile('/report/cinematic-studio-report.json',JSON.stringify(report,null,2))
  await browser.close()
}

const invalid=report.consoleErrors.length||report.pageErrors.length||report.requestFailures.length||report.httpErrors.length||report.projects.length!==3||report.projects.some(p=>p.initial.text<200||p.initial.sections<4||p.initial.broken||p.initial.overflow>2||p.mobile.broken||p.mobile.overflow>2||!p.mobile.h1Visible)||(report.projects.find(p=>p.name==='AUREON Automotive')?.initial.model!=='ready')||!report.projects.find(p=>p.name==='AUREON Automotive')?.cameraMoved
console.log(JSON.stringify(report,null,2))
if(invalid)process.exit(1)
