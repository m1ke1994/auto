import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
import fs from 'node:fs/promises'
import path from 'node:path'
import {chromium} from 'playwright'
const root=process.env.TN_VUE_ROOT,report=process.env.TN_BROWSER_REPORT
await fs.mkdir(report,{recursive:true})
const html=path.join(root,'__carousel_test.html'),entry=path.join(root,'__carousel_test.mjs'),component=path.join(root,'__carousel_test.vue')
let browser,vite,page
try{
  await fs.writeFile(html,'<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"></div><script type="module" src="/__carousel_test.mjs"></script>',{flag:'wx'})
  await fs.copyFile(process.env.TN_CAROUSEL_ENTRY,entry,fs.constants.COPYFILE_EXCL)
  await fs.copyFile(process.env.TN_CAROUSEL_SOURCE,component,fs.constants.COPYFILE_EXCL)
  vite=spawn(process.execPath,[path.join(root,'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','8002','--strictPort'],{cwd:root,stdio:'inherit'})
  for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:8002/__carousel_test.html')).ok)break}catch{}if(i===99)throw Error('Vite unavailable');await new Promise(r=>setTimeout(r,200))}
  browser=await chromium.launch()
  const errors=[]
  for(const [width,height] of [[1440,900],[834,1112],[390,844]]){
    page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'})
    page.on('pageerror',e=>errors.push(String(e)))
    for(const mode of ['narrative','horizontal','stack','showcase','chapter','editorial']){
      console.log('CAROUSEL_CASE',width,height,mode)
      await page.goto('http://127.0.0.1:8002/__carousel_test.html?mode='+mode)
      const carousel=page.locator('[data-tn-carousel]'),track=page.locator('[data-tn-carousel-track]')
      await carousel.waitFor()
      assert.equal(await track.evaluate(el=>getComputedStyle(el).scrollbarWidth),'none')
      assert.equal(await track.evaluate(el=>getComputedStyle(el,'::-webkit-scrollbar').display),'none')
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth+2))
      const active=async i=>{await page.waitForFunction(i=>Number(document.querySelector('[data-tn-carousel]').dataset.tnActive)===i,i)}
      await carousel.locator('[data-tn-carousel-next]').click();await active(1)
      await carousel.locator('[data-tn-carousel-prev]').click();await active(0)
      await track.hover()
      await page.mouse.wheel(0,180);await active(1)
      await track.focus();await track.press('End');await active(3)
      await track.hover()
      const before=await page.evaluate(()=>scrollY)
      await page.mouse.wheel(0,300)
      await page.waitForFunction(y=>scrollY>y+5,before,{timeout:5000})
      await track.focus();await track.press('Home');await active(0)
      await track.hover();const upper=await page.evaluate(()=>scrollY)
      await page.mouse.wheel(0,-300);await page.waitForFunction(y=>scrollY<y-5,upper,{timeout:5000})
      await carousel.scrollIntoViewIfNeeded()
      if(mode==='horizontal')await page.screenshot({path:path.join(report,'carousel-'+width+'.png')})
    }
    await page.close()
  }
  assert.deepEqual(errors,[])
  console.log('STUDIO_CAROUSEL_BROWSER_OK: 6 modes x 3 viewports')
}catch(error){
  if(page){
    const diagnostics=await page.evaluate(()=>{const el=document.querySelector('[data-tn-carousel-track]');return {pageY:scrollY,pageMax:document.documentElement.scrollHeight-innerHeight,active:document.querySelector('[data-tn-carousel]')?.dataset.tnActive,left:el?.scrollLeft,max:el?el.scrollWidth-el.clientWidth:null,rect:el?.getBoundingClientRect().toJSON()}}).catch(()=>null)
    console.error('CAROUSEL_FAILURE',diagnostics)
    await fs.writeFile(path.join(report,'carousel-failure.json'),JSON.stringify({error:String(error),diagnostics},null,2))
    await page.screenshot({path:path.join(report,'carousel-failure.png')}).catch(()=>{})
  }
  throw error
}finally{
  if(browser)await browser.close()
  if(vite)vite.kill()
  for(const f of [html,entry,component])await fs.rm(f,{force:true})
}
