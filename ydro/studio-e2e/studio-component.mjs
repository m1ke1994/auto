// Real Vue Studio component + iframe bridge, mocked API, no AI calls.
import assert from 'node:assert/strict'
import {createServer} from 'node:http'
import {spawn} from 'node:child_process'
import fs from 'node:fs/promises'
import path from 'node:path'
import {chromium} from 'playwright'
const root=process.env.TN_VUE_ROOT
const report=process.env.TN_BROWSER_REPORT
const bridge=await fs.readFile(process.env.TN_BRIDGE_HTML,'utf8')
await fs.mkdir(report,{recursive:true})
const id='11111111-1111-4111-8111-111111111111'
const version='22222222-2222-4222-8222-222222222222'
const field='a'.repeat(32)
const project={id,name:'Visual QA fixture',engine:'cinematic',generation_status:'complete',preview_version:'original',preview_path:'/studio-preview/fixture/',source_archive_available:true,versions:[{id:version,number:1,current:true}],revisions:[],block_edits:[]}
const catalog={expected_version:version,source_fingerprint:'b'.repeat(64),fields:[{id:field,text:'Original heading',tag:'h1',section:'home',styles:{}}],color_properties:['color','background-color'],style_choices:{'font-size':['1rem','2rem'],'font-weight':['400','700'],'text-align':['left','center']}}
const cfg={configured:true,cinematic_enabled:true,cinematic_max_cost_usd:2.5,worker:{required:true,available:true,visual_available:true,visual_style_available:true,scope_edit_available:true}}
let payload=null
const server=createServer(async(req,res)=>{
  res.setHeader('Access-Control-Allow-Origin','http://127.0.0.1:8001')
  res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS')
  res.setHeader('Access-Control-Allow-Headers','Content-Type,Authorization')
  if(req.method==='OPTIONS'){res.writeHead(204);res.end();return}
  const url=new URL(req.url,'http://127.0.0.1:8000')
  const json=(data,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(data))}
  if(url.pathname==='/api/studio/config/')return json(cfg)
  if(url.pathname==='/api/studio/projects/')return json([project])
  if(url.pathname==='/api/studio/projects/'+id+'/')return json(project)
  if(url.pathname.endsWith('/blocks/'))return json({available:true,expected_version:version,blocks:[{id:'home',label:'Главная'}]})
  if(url.pathname.endsWith('/visual-fields/'))return json(catalog)
  if(url.pathname.endsWith('/visual-save/')&&req.method==='POST'){
    let body='';for await(const chunk of req)body+=chunk
    payload=JSON.parse(body)
    project.block_edit={id:'fixture-edit',status:'queued',stage:'queued',decision:'pending'}
    return json(project,202)
  }
  if(url.pathname==='/studio-preview/fixture/'){
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors http://127.0.0.1:8001"})
    return res.end('<!doctype html><h1>Original heading</h1><p>Unchanged copy</p>'+(url.searchParams.get('tn_edit')==='1'?bridge:''))
  }
  res.writeHead(404);res.end()
})
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8000,'127.0.0.1',resolve)})
let browser,vite
const testHtml=path.join(root,'__studio_test.html'),testJs=path.join(root,'__studio_test.mjs')
try{
  await fs.copyFile(process.env.TN_COMPONENT_HTML,testHtml,fs.constants.COPYFILE_EXCL)
  await fs.copyFile(process.env.TN_COMPONENT_ENTRY,testJs,fs.constants.COPYFILE_EXCL)
  vite=spawn(process.execPath,[path.join(root,'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','8001','--strictPort','--mode','example'],{cwd:root,env:{...process.env,VITE_BACKEND_URL:'http://127.0.0.1:8000',VITE_API_URL:'http://127.0.0.1:8000/api',VITE_SITE_URL:'http://127.0.0.1:8001',VITE_PUBLIC_SITE_URL:'http://127.0.0.1:8001'},stdio:'inherit'})
  for(let i=0;i<100;i++){
    if(vite.exitCode!==null)throw new Error('Vite exited')
    try{if((await fetch('http://127.0.0.1:8001/__studio_test.html')).ok)break}catch{}
    if(i===99)throw new Error('Vite not ready')
    await new Promise(r=>setTimeout(r,200))
  }
  browser=await chromium.launch()
  const page=await browser.newPage({viewport:{width:1440,height:1000}})
  const errors=[]
  page.on('pageerror',e=>errors.push(String(e)))
  await page.goto('http://127.0.0.1:8001/__studio_test.html')
  await page.getByRole('button',{name:/Visual QA fixture/}).click()
  await page.getByRole('button',{name:'Визуально',exact:true}).click()
  const frame=page.frameLocator('iframe[title="Кинематографический предпросмотр сайта"]')
  await frame.getByRole('heading',{name:'Original heading'}).click()
  const text=page.locator('.visual-editor textarea')
  await text.fill('Text only edit')
  await frame.getByRole('heading',{name:'Text only edit'}).waitFor()
  await page.getByLabel('Размер шрифта',{exact:true}).selectOption('2rem')
  await frame.locator('h1[style*="font-size: 2rem"]').waitFor()
  const color=page.getByLabel('Цвет текста',{exact:true})
  await color.fill('#123456')
  await text.fill('Text after styling')
  await frame.getByRole('heading',{name:'Text after styling'}).waitFor()
  assert.equal(await frame.locator('h1').evaluate(el=>getComputedStyle(el).color),'rgb(18, 52, 86)')
  await page.screenshot({path:path.join(report,'studio-component-desktop.png')})
  await page.getByRole('button',{name:'Телефон',exact:true}).click()
  await page.screenshot({path:path.join(report,'studio-component-mobile-preview.png')})
  await page.getByRole('button',{name:'Сбросить',exact:true}).click()
  await frame.getByRole('heading',{name:'Original heading'}).waitFor()
  assert.equal(await frame.locator('h1').evaluate(el=>el.style.fontSize),'')
  await text.fill('Save candidate')
  await page.getByLabel('Размер шрифта',{exact:true}).selectOption('2rem')
  await page.getByRole('button',{name:'Собрать версию',exact:true}).click()
  await page.waitForFunction(()=>document.querySelector('.block-live-status')?.textContent.includes('В очереди'))
  assert.deepEqual(payload,{expected_version:version,source_fingerprint:'b'.repeat(64),changes:[{id:field,text:'Save candidate',styles:{'font-size':'2rem'}}]})
  assert.deepEqual(await page.evaluate(()=>window.studioErrors),[])
  assert.deepEqual(errors,[])
  await fs.writeFile(path.join(report,'studio-component-result.json'),JSON.stringify({passed:true,tests:['Vue text','Vue reactive style transport','text after style','reset','candidate request','no uncaught errors']},null,2))
  console.log('STUDIO_COMPONENT_BROWSER_OK')
}finally{
  if(browser)await browser.close()
  if(vite)vite.kill()
  server.close()
  await fs.rm(testHtml,{force:true});await fs.rm(testJs,{force:true})
}
