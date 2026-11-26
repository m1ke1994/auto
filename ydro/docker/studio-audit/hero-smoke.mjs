// Browser smoke test of the exact shipped HeroObjectStage, no AI or external network.
import {chromium} from 'playwright';
import {readFile,writeFile,realpath} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
import {createHash} from 'node:crypto';
const root=await realpath('/site');
const origin='http://studio.invalid';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css'};
const report={passed:false,tests:[],errors:[]};
let browser;
const assert=(v,msg)=>{if(!v)throw Error(msg)};
const hash=b=>createHash('sha256').update(b).digest('hex');
try{
  browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  for(const preset of ['serum','jar','tube','perfume','cup','vase','watch','ring','microphone']){
    for(const mode of ['desktop','mobile']){
      const row={preset,mode,passed:false};
      report.tests.push(row);
      let context;
      const errors=[];
      try{
        context=await browser.newContext({viewport:mode==='desktop'?{width:1440,height:900}:{width:390,height:844},reducedMotion:mode==='mobile'?'reduce':'no-preference',serviceWorkers:'block',acceptDownloads:false});
        await context.route('**/*',async route=>{
          try{
            const url=new URL(route.request().url());
            if(url.origin!==origin||route.request().method()!=='GET'){errors.push('External or unsupported request');return await route.abort()}
            const file=await realpath(resolve(root,decodeURIComponent(url.pathname).replace(/^\/+/, '')||'index.html'));
            if(!file.startsWith(root+sep))throw Error('Invalid path');
            await route.fulfill({status:200,contentType:types[extname(file)]||'application/octet-stream',body:await readFile(file)});
          }catch{errors.push('Missing resource');await route.fulfill({status:404,body:'Not found'}).catch(()=>{})}
        });
        const page=await context.newPage();
        page.on('pageerror',e=>errors.push(String(e).slice(0,300)));
        await page.goto(origin+'/?preset='+preset,{waitUntil:'load',timeout:30000});
        const stage=page.locator('[data-tn-hero-object]');
        await stage.waitFor({state:'visible',timeout:10000});
        assert(await stage.getAttribute('data-tn-object-preset')===preset,'Wrong preset');
        const initial=await stage.evaluate(el=>({width:el.clientWidth,height:el.clientHeight,overflow:document.documentElement.scrollWidth-innerWidth}));
        assert(initial.overflow<=2&&initial.width>200&&initial.height>=250,'Layout overflow or small stage');
        if(mode==='desktop'){
          await page.waitForFunction(()=>document.querySelector('[data-tn-hero-object]')?.dataset.tnObjectState==='ready',null,{timeout:15000});
          const before=Number(await stage.getAttribute('data-tn-object-pose'));
          const a=await stage.screenshot({path:'/report/'+preset+'-desktop-opening.png',timeout:20000});
          await page.evaluate(()=>window.scrollTo(0,180));
          await page.waitForFunction(p=>Number(document.querySelector('[data-tn-hero-object]')?.dataset.tnObjectPose)>p+.05,before,{timeout:8000});
          const after=Number(await stage.getAttribute('data-tn-object-pose'));
          const b=await stage.screenshot({path:'/report/'+preset+'-desktop-scroll.png',timeout:20000});
          assert(hash(a)!==hash(b),'No visible pixel change');
          row.poses=[before,after];row.pixelChange=true;
          await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
          await page.waitForTimeout(600);
          const offscreenPose=await stage.getAttribute('data-tn-object-pose');
          await page.evaluate(()=>window.scrollBy(0,-100));
          await page.waitForTimeout(600);
          assert(await stage.getAttribute('data-tn-object-pose')===offscreenPose,'Offscreen pose changed');
          await page.screenshot({path:'/report/'+preset+'-desktop-end.png',timeout:20000});
          row.offscreenStable=true;
        }else{
          await page.waitForTimeout(700);
          assert(await stage.getAttribute('data-tn-object-state')==='fallback','Mobile fallback not active');
          assert(await stage.locator('canvas').count()===0,'Unexpected mobile WebGL canvas');
          assert(await stage.locator('.tn-product-fallback').isVisible(),'Mobile product missing');
          await stage.screenshot({path:'/report/'+preset+'-mobile.png',timeout:20000});
          row.fallback=true;
        }
        assert(errors.length===0,errors.join('; '));
        row.passed=true;
      }catch(e){row.error=String(e).slice(0,1000)}
      finally{if(context)await context.close().catch(()=>{});}
      console.log(JSON.stringify(row));
    }
  }
  report.passed=report.tests.length===18&&report.tests.every(t=>t.passed);
}catch(e){report.errors.push(String(e).slice(0,1000))}
finally{
  if(browser)await browser.close().catch(()=>{});
  await writeFile('/report/hero-smoke.json',JSON.stringify(report,null,2));
  console.log('HERO_SMOKE_PASSED: '+report.passed);
  if(!report.passed)process.exitCode=1;
}
