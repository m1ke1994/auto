// Test only local build artifacts. Network is disabled by Docker and requests are intercepted.
import { chromium } from 'playwright';
import { readFile, writeFile, realpath } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
const root = await realpath('/site');
const origin = 'http://studio.invalid';
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.woff2':'font/woff2','.json':'application/json'};
const report = { profile: process.argv[2] || 'cinema', checks: [], artistic_quality_verified: false };
const browser=await chromium.launch({headless:true});
try {
  for (const [name,width,height,reducedMotion] of [['desktop',1440,900,'no-preference'],['mobile',390,844,'reduce']]) {
    const context=await browser.newContext({viewport:{width,height},reducedMotion,serviceWorkers:'block',acceptDownloads:false});
    const errors=[], blocked=[], missing=[];
    await context.route('**/*',async route=>{
      try {
        const url=new URL(route.request().url());
        if(url.origin!==origin) { blocked.push(url.origin); return await route.abort(); }
        if(route.request().method()!=='GET') return await route.abort();
        const relative=decodeURIComponent(url.pathname).replace(/^\/+/,'') || 'index.html';
        const path=await realpath(resolve(root,relative));
        if(!path.startsWith(root+sep)) return await route.abort();
        const body=await readFile(path);
        await route.fulfill({status:200,contentType:types[extname(path)] || 'application/octet-stream',body});
      } catch { missing.push(route.request().url().slice(0,200)); await route.fulfill({status:404,body:'Not found'}).catch(()=>{}); }
    });
    const page=await context.newPage();
    page.on('pageerror',e=>errors.push(String(e).slice(0,400)));
    await page.goto(origin+'/',{waitUntil:'load',timeout:30000});
    await page.waitForTimeout(1500);
    const result=await page.evaluate(()=>{
      const root=document.scrollingElement;
      const visible=e=>{if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&Number(s.opacity)>0;};
      const footer=document.querySelector('footer[data-tn-footer]');
      return {title:document.title,bodyText:(document.body.innerText||'').trim().length,overflow:Math.max(0,root.scrollWidth-root.clientWidth),scrollHeight:root.scrollHeight,viewport:root.clientHeight,footer:visible(footer)&&footer.innerText.trim().length>15,footerLinks:footer?.querySelectorAll('a[href]').length||0,scenes:[...document.querySelectorAll('[data-tn-scene]')].filter(visible).length,brokenImages:[...document.images].filter(i=>i.complete&&!i.naturalWidth).length};
    });
    const steps=[];
    for (const fraction of [0,.25,.5,.75,1]) {
      await page.evaluate(f=>{const r=document.scrollingElement;window.scrollTo({top:(r.scrollHeight-r.clientHeight)*f,behavior:'instant'});},fraction);
      await page.waitForTimeout(1200);
      const state=await page.evaluate(()=>{
        const r=document.scrollingElement,host=document.querySelector('#tn-landing-progress'),fill=host?.shadowRoot?.querySelector('.fill');
        const actual=r.scrollHeight>r.clientHeight?r.scrollTop/(r.scrollHeight-r.clientHeight):0;
        const rect=host?.getBoundingClientRect();
        const scale=fill?new DOMMatrixReadOnly(getComputedStyle(fill).transform).a:null;
        const layers=[...document.querySelectorAll('[data-tn-motion]')].slice(0,20).map(e=>{const s=getComputedStyle(e);return [s.transform,s.opacity,s.clipPath,s.filter].join('|');});
        return {actual,scale,top:rect?.top??null,width:rect?.width??0,viewport:innerWidth,layers};
      });
      steps.push(state);
      await page.screenshot({path:'/report/'+name+'-'+Math.round(fraction*100)+'.png',timeout:15000});
    }
    const end=steps.at(-1);
    const brokenAfterScroll=await page.evaluate(()=>[...document.images].filter(i=>i.complete&&!i.naturalWidth).length);
    const motionChanged=steps.some((x,i)=>i>0&&JSON.stringify(x.layers)!==JSON.stringify(steps[i-1].layers));
    const progressOk=steps.every(x=>x.scale!==null&&Math.abs(x.scale-x.actual)<.08&&Math.abs(x.top)<2&&x.width>=x.viewport-24)&&end.actual>.95;
    const checks={rendered:result.bodyText>80,noHorizontalOverflow:result.overflow<=2,footer:result.footer&&result.footerLinks>0,progress:progressOk,noBrokenImages:Math.max(result.brokenImages,brokenAfterScroll)===0,noJsErrors:errors.length===0,noMissingAssets:missing.length===0,noExternalRequests:blocked.length===0};
    if(report.profile==='cinema') {checks.scenes=result.scenes>=3;if(name==='desktop') checks.scrollMotion=motionChanged;}
    report.checks.push({name,checks,metrics:result,steps,errors:errors.slice(0,20),missing:missing.slice(0,20),blocked:blocked.slice(0,20)});
    await context.close();
  }
} catch(error){report.error=String(error).slice(0,500);}
finally { await browser.close(); }
report.passed=!report.error&&report.checks.length===2&&report.checks.every(c=>Object.values(c.checks).every(Boolean));
await writeFile('/report/quality-report.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,checks:report.checks.map(({name,checks})=>({name,checks})),error:report.error},null,2));
if(!report.passed) process.exitCode=1;
