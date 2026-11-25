// Offline trusted candidate preview. Record actionable diagnostics, not just Error.
import {chromium} from 'playwright';
import {readFile,writeFile,realpath,unlink} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
const root=await realpath('/site'),origin='http://studio.invalid';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.gltf':'model/gltf+json','.bin':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.ico':'image/x-icon'};
const report={passed:false,views:[],missing:[],blocked:[],pageErrors:[],consoleErrors:[],requestFailures:[]};
const short=v=>String(v).slice(0,600);
let browser,page,stage='startup';
await unlink('/report/render-ok.json').catch(e=>{if(e.code!=='ENOENT')throw e;});
try{
  browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const context=await browser.newContext({viewport:{width:1000,height:750},reducedMotion:'reduce',serviceWorkers:'block',acceptDownloads:false});
  await context.route('**/*',async route=>{
    let pathname='unknown';
    try{
      const u=new URL(route.request().url());
      pathname=u.pathname;
      if(u.origin!==origin||route.request().method()!=='GET'){
        report.blocked.push(short(u.origin+pathname));
        return await route.abort();
      }
      // Chromium may request a favicon even when the trusted preview has none.
      // Missing cosmetic browser icons must not invalidate a model.
      if(pathname==='/favicon.ico')return await route.fulfill({status:204,body:''});
      const path=await realpath(resolve(root,decodeURIComponent(pathname).replace(/^\/+/,'')||'index.html'));
      if(!path.startsWith(root+sep))throw Error('Path outside preview root');
      await route.fulfill({status:200,contentType:types[extname(path)]||'application/octet-stream',body:await readFile(path)});
    }catch(e){
      report.missing.push({path:short(pathname),reason:short(e.code||e.name)});
      await route.fulfill({status:404,body:'Not found'}).catch(()=>{});
    }
  });
  page=await context.newPage();
  page.on('pageerror',e=>report.pageErrors.push(short(e.message)));
  page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(short(m.text()));});
  page.on('requestfailed',r=>report.requestFailures.push({path:short(r.url().split('?')[0]),reason:short(r.failure()?.errorText)}));
  for(const yaw of [45,135,225]){
    stage='navigate-'+yaw;
    await page.goto(origin+'/?yaw='+yaw,{waitUntil:'load',timeout:20000});
    stage='model-ready-'+yaw;
    await page.waitForFunction(()=>{const n=document.querySelector('[data-tn-model]');return n&&(n.dataset.tnModelState==='fallback'||(n.dataset.tnModelState==='ready'&&Number(n.dataset.tnFrames)>0));},{},{timeout:30000});
    await page.waitForTimeout(500);
    const state=await page.locator('[data-tn-model]').evaluate(n=>({state:n.dataset.tnModelState,frames:Number(n.dataset.tnFrames||0),coverage:Number(n.dataset.tnModelCoverage||0),yaw:n.dataset.tnCameraYaw,pose:n.dataset.tnCameraPose,canvas:!!n.querySelector('canvas'),width:n.clientWidth,height:n.clientHeight}));
    report.views.push({yaw,...state});
    stage='screenshot-'+yaw;
    await page.locator('[data-tn-model]').screenshot({path:'/report/view-'+yaw+'.png',timeout:15000});
    if(state.state!=='ready'||state.frames<1||!state.canvas||state.width<100||state.height<100)throw Error('Model did not render: '+state.state);
    console.log('ASSET_VIEW_READY: '+yaw+'; coverage='+state.coverage+'; frames='+state.frames);
  }
  stage='validate';
  if(report.missing.length||report.blocked.length||report.pageErrors.length||report.requestFailures.length)throw Error('Preview request or JavaScript errors');
  if(new Set(report.views.map(v=>v.pose)).size!==3)throw Error('Camera views are not distinct');
  report.passed=true;
  await writeFile('/report/render-ok.json',JSON.stringify({passed:true,angles:[45,135,225]}));
  console.log('ASSET_RENDER_PASSED');
}catch(e){
  report.stage=stage;
  report.error=short(e.message);
  if(page){
    report.lastState=await page.locator('[data-tn-model]').evaluateAll(nodes=>nodes.map(n=>({...n.dataset,canvas:!!n.querySelector('canvas')}))).catch(()=>[]);
    await page.screenshot({path:'/report/render-failure.png',timeout:5000}).catch(()=>{});
  }
  console.error('ASSET_RENDER_FAILED: '+stage+'; '+report.error);
  process.exitCode=1;
}finally{
  for(const key of ['missing','blocked','pageErrors','consoleErrors','requestFailures'])report[key]=report[key].slice(0,30);
  await writeFile('/report/render-diagnostics.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
  await browser?.close();
}
