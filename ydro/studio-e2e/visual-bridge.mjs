// Real browser test of the preview-only bridge. No API keys, paid jobs or user projects.
import assert from 'node:assert/strict'
import {createServer} from 'node:http'
import fs from 'node:fs/promises'
import path from 'node:path'
import {chromium} from 'playwright'

const bridge=await fs.readFile(process.env.TN_BRIDGE_HTML,'utf8')
const reportDir=process.env.TN_BROWSER_REPORT||'browser-report'
await fs.mkdir(reportDir,{recursive:true})
const html='<!doctype html><meta charset="utf-8"><style>body{margin:40px;font-family:Arial;background:#f5f5f5}h1{color:#222}a{color:#246}button{padding:10px}</style><h1>Original heading</h1><p>Original copy</p><a href="#target">Open link</a><p data-tn-film-caption>Protected caption</p><div id="target"></div>'
const parent='<!doctype html><meta charset="utf-8"><iframe id="site" src="http://127.0.0.1:8000/?tn_edit=1" sandbox="allow-scripts allow-same-origin" style="width:95vw;height:82vh;border:0"></iframe><script>window.events=[];window.addEventListener("message",e=>{if(e.origin==="http://127.0.0.1:8000"&&e.source===document.querySelector("iframe").contentWindow)window.events.push(e.data)});window.draft=changes=>document.querySelector("iframe").contentWindow.postMessage({type:"tn-visual-draft",changes},"http://127.0.0.1:8000")</script>'
const listen=(port,handler)=>new Promise((resolve,reject)=>{
  const server=createServer(handler)
  server.once('error',reject);server.listen(port,'127.0.0.1',()=>resolve(server))
})
const backend=await listen(8000,(req,res)=>{
  res.setHeader('Content-Type','text/html; charset=utf-8')
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors http://127.0.0.1:8001")
  res.end(html+(req.url.includes('tn_edit=1')?bridge:''))
})
const frontend=await listen(8001,(_req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(parent)})
let browser
try {
  browser=await chromium.launch({headless:true})
  const page=await browser.newPage({viewport:{width:1280,height:850}})
  const errors=[]
  page.on('pageerror',e=>errors.push(String(e)))
  await page.goto('http://127.0.0.1:8001')
  await page.waitForFunction(()=>window.events.some(e=>e.type==='tn-visual-ready'))
  const frame=page.frameLocator('#site')
  await frame.getByRole('heading',{name:'Original heading'}).click()
  await page.waitForFunction(()=>window.events.some(e=>e.type==='tn-visual-select'&&e.text==='Original heading'&&e.tag==='h1'))
  await page.evaluate(()=>window.draft([{before:'Original heading',after:'Edited heading',tag:'h1',styles:{color:'#123456','font-size':'2rem'}}]))
  await frame.getByRole('heading',{name:'Edited heading'}).waitFor()
  assert.equal(await frame.locator('h1').evaluate(el=>getComputedStyle(el).color),'rgb(18, 52, 86)')
  assert.equal(await frame.locator('h1').evaluate(el=>getComputedStyle(el).fontSize),'32px')
  await page.screenshot({path:path.join(reportDir,'desktop-edited.png')})
  await page.setViewportSize({width:390,height:844})
  await page.screenshot({path:path.join(reportDir,'mobile-edited.png')})
  // A forged event with an unrelated origin/source must not edit the iframe.
  await frame.locator('h1').evaluate(el=>window.dispatchEvent(new MessageEvent('message',{origin:'http://evil.example',source:window,data:{type:'tn-visual-draft',changes:[{before:'Original heading',after:'Forged',tag:'h1'}]}})))
  assert.equal(await frame.locator('h1').innerText(),'Edited heading')
  await page.evaluate(()=>window.draft([]))
  await frame.getByRole('heading',{name:'Original heading'}).waitFor()
  assert.equal(await frame.locator('h1').evaluate(el=>getComputedStyle(el).color),'rgb(34, 34, 34)')
  await frame.getByRole('link',{name:'Open link'}).click()
  assert.equal(await frame.getByRole('link',{name:'Open link'}).getAttribute('href'),'#target')
  assert.ok(!page.frames()[1].url().endsWith('#target'),'Editor should intercept text-link click')
  await page.evaluate(()=>window.draft([{before:'Protected caption',after:'Changed caption',tag:'p'}]))
  assert.equal(await frame.locator('[data-tn-film-caption]').innerText(),'Protected caption')
  await page.evaluate(()=>window.draft([{before:'Original heading',after:'<script>unsafe</script>',tag:'h1'}]))
  await frame.getByRole('heading',{name:'<script>unsafe</script>'}).waitFor()
  assert.equal(await frame.locator('h1 script').count(),0)
  assert.deepEqual(errors,[])
  const normal=await page.request.get('http://127.0.0.1:8000/')
  assert.ok(!(await normal.text()).includes('tn-visual-select'))
  await fs.writeFile(path.join(reportDir,'result.json'),JSON.stringify({passed:true,tests:['click','draft text','draft color and font','desktop/mobile screenshots','origin isolation','reset','link interception','caption protection','escaped markup','normal preview'],errors},null,2))
  console.log('STUDIO_VISUAL_BROWSER_OK')
}finally{
  if(browser)await browser.close()
  backend.close();frontend.close()
}
