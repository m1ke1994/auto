// Trusted candidate preview. Offline, no generated user website code.
import {chromium} from 'playwright';
import {readFile,writeFile,realpath} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
const root=await realpath('/site'),origin='http://studio.invalid';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.gltf':'model/gltf+json','.bin':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'};
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
  const context=await browser.newContext({viewport:{width:1000,height:750},reducedMotion:'reduce',serviceWorkers:'block',acceptDownloads:false});
  const errors=[];
  await context.route('**/*',async route=>{
    try{
      const u=new URL(route.request().url());
      if(u.origin!==origin||route.request().method()!=='GET')return await route.abort();
      const path=await realpath(resolve(root,decodeURIComponent(u.pathname).replace(/^\/+/,'')||'index.html'));
      if(!path.startsWith(root+sep))return await route.abort();
      await route.fulfill({status:200,contentType:types[extname(path)]||'application/octet-stream',body:await readFile(path)});
    }catch{errors.push('missing asset');await route.abort().catch(()=>{});}
  });
  const page=await context.newPage();
  page.on('pageerror',()=>errors.push('page error'));
  for(const yaw of [45,135,225]){
    await page.goto(origin+'/?yaw='+yaw,{waitUntil:'load',timeout:20000});
    await page.waitForFunction(()=>{const n=document.querySelector('[data-tn-model]');return n?.dataset.tnModelState==='ready'&&Number(n.dataset.tnFrames)>0;},{},{timeout:25000});
    await page.waitForTimeout(500);
    await page.locator('[data-tn-model]').screenshot({path:'/report/view-'+yaw+'.png',timeout:10000});
  }
  if(errors.length)throw Error('Preview errors');
  await writeFile('/report/render-ok.json',JSON.stringify({passed:true,angles:[45,135,225]}));
  await context.close();
}catch(e){console.error('ASSET_RENDER_FAILED: '+e.name);process.exitCode=1;}
finally{await browser.close();}
