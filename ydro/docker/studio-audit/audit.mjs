// Test only local build artifacts. Network is disabled by Docker and requests are intercepted.
import { chromium } from 'playwright';
import { readFile, writeFile, realpath, readdir } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
const root = await realpath('/site');
const origin = 'http://studio.invalid';
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.woff2':'font/woff2','.json':'application/json','.gltf':'model/gltf+json','.glb':'model/gltf-binary','.bin':'application/octet-stream','.jpeg':'image/jpeg'};
const report = { profile: process.argv[2] || 'cinema', checks: [], artistic_quality_verified: false };
const modelDirs=await readdir(resolve(root,'tn-models')).catch(()=>[]);
const expectedModels=modelDirs.map(dir=>'tn-models/'+dir+'/model.gltf');
report.expectedModels=expectedModels;
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
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
    if(expectedModels.length) await page.waitForFunction(()=>{const nodes=[...document.querySelectorAll('[data-tn-model]')];return nodes.length>0&&nodes.every(n=>n.dataset.tnModelState!=='loading');},{},{timeout:30000}).catch(()=>{});
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
      const models=await page.locator('[data-tn-model]').evaluateAll(nodes=>nodes.map(n=>({path:n.dataset.tnModel,state:n.dataset.tnModelState,frames:Number(n.dataset.tnFrames||0),pose:n.dataset.tnCameraPose||'',progress:Number(n.dataset.tnCameraProgress||0),canvas:!!n.querySelector('canvas')})));
      steps.push({...state,models});
      await page.screenshot({path:'/report/'+name+'-'+Math.round(fraction*100)+'.png',timeout:15000});
    }
    // Visit actual content sections individually; sample-based screenshots alone
    // can miss short sections and reveal-on-scroll content.
    const required=['home','about','services','benefits','contacts'];
    const sections=[];
    for(const id of required){
      const section=page.locator('main section[data-tn-section="'+id+'"][id="'+id+'"]');
      if(await section.count()!==1){sections.push({id,exists:false});continue;}
      await section.evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));
      await page.waitForTimeout(900);
      sections.push(await section.evaluate((e,id)=>{
        const visible=x=>{
          if(!x||!x.getClientRects().length)return false;
          for(let n=x;n;n=n.parentElement){
            const s=getComputedStyle(n);
            if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.05)return false;
          }
          const r=x.getBoundingClientRect();
          return r.width>0&&r.height>0;
        };
        const text=x=>(x?.innerText||'').trim();
        const heading=[...e.querySelectorAll(id==='home'?'h1':'h2,h3')].find(x=>visible(x)&&text(x).length>=3);
        const cards=[...e.querySelectorAll('[data-tn-service]')].filter(x=>visible(x)&&text(x).length>=30&&[...x.querySelectorAll('h2,h3,h4')].some(h=>visible(h)&&text(h).length>=3));
        const distinctCards=new Set(cards.map(x=>text(x).replace(/\s+/g,' '))).size;
        const cta=[...e.querySelectorAll('a[href="#contacts"],a[href="#services"]')].some(x=>visible(x)&&text(x).length>=2);
        const rect=e.getBoundingClientRect();
        return {id,exists:true,visible:visible(e),heading:!!heading,textLength:text(e).length,
          reachable:rect.bottom>0&&rect.top<innerHeight,
          distinctCards,cta,heroModel:!!e.querySelector('[data-tn-model]')};
      },id));
    }
    await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
    await page.waitForTimeout(900);
    const navState=()=>page.evaluate(()=>{
      const header=document.querySelector('header[data-tn-header]');
      const visible=x=>{
        if(!x||!x.getClientRects().length)return false;
        for(let n=x;n;n=n.parentElement){const s=getComputedStyle(n);if(s.visibility==='hidden'||s.display==='none'||Number(s.opacity)<.05)return false;}
        const r=x.getBoundingClientRect();
        return r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight;
      };
      const links=['home','about','services','contacts'].map(id=>({id,visible:[...(header?.querySelectorAll('nav a[href="#'+id+'"]')||[])].some(a=>visible(a)&&a.innerText.trim()&&document.getElementById(id))}));
      const toggle=header?.querySelector('[data-tn-menu-toggle]');
      return {header:visible(header),links,allLinks:links.every(x=>x.visible),toggleVisible:visible(toggle),expanded:toggle?.getAttribute('aria-expanded')};
    });
    let navigation=await navState();
    let menuOperable=true;
    if(name==='mobile'&&!navigation.allLinks){
      const toggle=page.locator('header[data-tn-header] button[data-tn-menu-toggle]');
      if(navigation.toggleVisible&&await toggle.count()===1){
        try{
          await toggle.click({timeout:3000});await page.waitForTimeout(400);
          navigation=await navState();
          const open=navigation.allLinks&&navigation.expanded==='true';
          await toggle.click({timeout:3000});await page.waitForTimeout(400);
          const closed=await navState();
          menuOperable=open&&closed.expanded==='false';
        }catch{menuOperable=false;}
      }else{menuOperable=false;}
    }
    const end=steps.at(-1);
    const brokenAfterScroll=await page.evaluate(()=>[...document.images].filter(i=>i.complete&&!i.naturalWidth).length);
    const motionChanged=steps.some((x,i)=>i>0&&JSON.stringify(x.layers)!==JSON.stringify(steps[i-1].layers));
    const progressOk=steps.every(x=>x.scale!==null&&Math.abs(x.scale-x.actual)<.08&&Math.abs(x.top)<2&&x.width>=x.viewport-24)&&end.actual>.95;
    const checks={rendered:result.bodyText>80,noHorizontalOverflow:result.overflow<=2,footer:result.footer&&result.footerLinks>0,progress:progressOk,noBrokenImages:Math.max(result.brokenImages,brokenAfterScroll)===0,noJsErrors:errors.length===0,noMissingAssets:missing.length===0,noExternalRequests:blocked.length===0};
    checks.completeSections=sections.every(x=>x.exists&&x.visible&&x.reachable&&x.heading&&x.textLength>=45);
    checks.headerNavigation=navigation.header&&navigation.allLinks&&menuOperable;
    checks.heroCTA=sections.some(x=>x.id==='home'&&x.cta);
    checks.serviceCards=sections.some(x=>x.id==='services'&&x.distinctCards>=3);
    if(expectedModels.length && report.profile==='cinema') checks.heroImportedModel=sections.some(x=>x.id==='home'&&x.heroModel);
    if(expectedModels.length){
      const observed=steps.flatMap(x=>x.models);
      checks.importedModelsReady=expectedModels.every(path=>observed.some(m=>m.path===path&&m.state==='ready'&&m.canvas&&m.frames>0));
      if(name==='desktop') checks.cameraChanges=expectedModels.every(path=>new Set(observed.filter(m=>m.path===path&&m.state==='ready'&&m.frames>0&&m.pose).map(m=>m.pose)).size>=2);
    }
    if(report.profile==='cinema') {checks.scenes=result.scenes>=3;if(name==='desktop') checks.scrollMotion=motionChanged;}
    report.checks.push({name,checks,metrics:result,sections,navigation,steps,errors:errors.slice(0,20),missing:missing.slice(0,20),blocked:blocked.slice(0,20)});
    await context.close();
  }
} catch(error){report.error=String(error).slice(0,500);}
finally { await browser.close(); }
report.passed=!report.error&&report.checks.length===2&&report.checks.every(c=>Object.values(c.checks).every(Boolean));
await writeFile('/report/quality-report.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,checks:report.checks.map(({name,checks})=>({name,checks})),error:report.error},null,2));
if(!report.passed) process.exitCode=1;
