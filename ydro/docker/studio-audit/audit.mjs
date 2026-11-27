// Test only local build artifacts. Network is disabled by Docker and requests are intercepted.
import { chromium } from 'playwright';
import { createCapture, finalizeAudit } from './capture.mjs';
import { readFile, writeFile, realpath, readdir } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
const root = await realpath('/site');
const origin = 'http://studio.invalid';
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.woff2':'font/woff2','.json':'application/json','.gltf':'model/gltf+json','.glb':'model/gltf-binary','.bin':'application/octet-stream','.jpeg':'image/jpeg'};
const report = { profile: process.argv[2] || 'cinema', checks: [], artistic_quality_verified: false };
const modelDirs=await readdir(resolve(root,'tn-models')).catch(()=>[]);
const expectedModels=modelDirs.map(dir=>'tn-models/'+dir+'/model.gltf');
report.expectedModels=expectedModels;
const sceneContract=await readFile(resolve(root,'tn-scene-contract.json'),'utf8').then(JSON.parse).catch(()=>null);
report.sceneEngine=sceneContract?.version||0;
const contactContract=await readFile(resolve(root,'tn-contact-contract.json'),'utf8').then(JSON.parse).catch(()=>null);
const capture=createCapture(report);
let browser;
let stage='browser launch';
try {
  browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  for (const [name,width,height,reducedMotion] of [['desktop',1440,900,'no-preference'],['mobile',390,844,'reduce']]) {
    stage=name+' browser context';
    console.log('AUDIT_DEVICE: '+name);
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
    stage=name+' page load';
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
      stage=name+' scroll '+Math.round(fraction*100)+'%';
      await page.evaluate(f=>{const r=document.scrollingElement;window.scrollTo({top:(r.scrollHeight-r.clientHeight)*f,behavior:'instant'});},fraction);
      await page.waitForTimeout(1200);
      const state=await page.evaluate(()=>{
        const r=document.scrollingElement,host=document.querySelector('#tn-landing-progress'),fill=host?.shadowRoot?.querySelector('.fill');
        const actual=r.scrollHeight>r.clientHeight?r.scrollTop/(r.scrollHeight-r.clientHeight):0;
        const rect=host?.getBoundingClientRect();
        const scale=fill?new DOMMatrixReadOnly(getComputedStyle(fill).transform).a:null;
        const layers=[...document.querySelectorAll('[data-tn-motion]')].slice(0,20).map(e=>{const s=getComputedStyle(e);return [s.transform,s.opacity,s.clipPath,s.filter].join('|');});
        const horizontalOverflow=Math.max(0,r.scrollWidth-r.clientWidth);
        const overflowCandidates=horizontalOverflow>2?[...document.querySelectorAll('main *')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.right>r.clientWidth+2;}).slice(0,12).map(e=>({tag:e.tagName.toLowerCase(),id:e.id||'',className:typeof e.className==='string'?e.className.slice(0,100):''})):[]; 
        return {actual,scale,top:rect?.top??null,width:rect?.width??0,viewport:innerWidth,layers,horizontalOverflow,overflowCandidates};
      });
      const models=await page.locator('[data-tn-model]').evaluateAll(nodes=>nodes.map((n,index)=>({index,path:n.dataset.tnModel,state:n.dataset.tnModelState,frames:Number(n.dataset.tnFrames||0),pose:n.dataset.tnCameraPose||'',motionPose:n.dataset.tnModelMotionPose||n.dataset.tnCameraPose||'',nativeMotion:!!n.dataset.tnModelMotionPose,preset:n.dataset.tnMotionPreset||'custom',progress:Number(n.dataset.tnCameraProgress||0),canvas:!!n.querySelector('canvas')})));
      steps.push({...state,models});
      await capture(page,name+'-'+Math.round(fraction*100)+'.png');
    }
    // Visit actual content sections individually; sample-based screenshots alone
    // can miss short sections and reveal-on-scroll content.
    const required=['home','about','services','benefits','contacts'];
    const sections=[],sectionModelSamples=[];
    for(const id of required){
      stage=name+' section '+id;
      const section=page.locator('main section[data-tn-section="'+id+'"][id="'+id+'"]');
      if(await section.count()!==1){sections.push({id,exists:false});continue;}
      await section.evaluate(e=>{
        e.scrollIntoView({block:'start',behavior:'instant'});
        if(e.hasAttribute('data-tn-hero-film')&&!matchMedia('(prefers-reduced-motion: reduce),(max-height:600px)').matches){
          const r=e.getBoundingClientRect();window.scrollTo({top:scrollY+r.top+(r.height-innerHeight)*.75,behavior:'instant'});
        }
      });
      await page.waitForTimeout(900);
      if(id==='about'&&await section.locator('[data-tn-about-metrics]').count()){
        await page.waitForFunction(()=>document.querySelector('#about [data-tn-about-metrics]')?.dataset.tnMetricState==='complete',{}, {timeout:4000}).catch(()=>{});
      }
      await capture(page,name+'-section-'+id+'.png');
      sectionModelSamples.push(...await page.locator('[data-tn-model]').evaluateAll(nodes=>nodes.map((n,index)=>({index,path:n.dataset.tnModel,state:n.dataset.tnModelState,frames:Number(n.dataset.tnFrames||0),pose:n.dataset.tnCameraPose||'',motionPose:n.dataset.tnModelMotionPose||n.dataset.tnCameraPose||'',nativeMotion:!!n.dataset.tnModelMotionPose,preset:n.dataset.tnMotionPreset||'custom',canvas:!!n.querySelector('canvas')}))));
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
    const aboutMetrics=await page.evaluate(()=>{
      const root=document.querySelector('#about [data-tn-about-metrics]');
      if(!root)return {present:false,count:0,complete:false,values:[]};
      const items=[...root.querySelectorAll('[data-tn-metric]')];
      return {present:true,count:items.length,complete:root.dataset.tnMetricState==='complete',values:items.map(item=>item.dataset.tnMetricValue||'')};
    });
    await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
    await page.waitForTimeout(900);
    stage=name+' interaction checks';
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
    const heroFraming=await page.locator('#home [data-tn-model]').evaluateAll(nodes=>nodes.map(n=>{
      const r=n.getBoundingClientRect();
      const bounds=(n.dataset.tnModelScreenBounds||'').split(',').map(Number);
      // Bounding-box intersections are advisory. A transparent area or deliberate
      // text overlay may be harmless; use actual screenshots for artistic judgment.
      const overlap=[];
      if(bounds.length===4&&bounds.every(Number.isFinite)){
        const [x1,y1,x2,y2]=bounds;
        const box={left:r.left+x1*r.width,right:r.left+x2*r.width,top:r.top+y1*r.height,bottom:r.top+y2*r.height};
        for(const e of document.querySelectorAll('#home h1,#home a[href="#contacts"],#home a[href="#services"]')){
          const t=e.getBoundingClientRect();
          const area=Math.max(0,Math.min(t.right,box.right)-Math.max(t.left,box.left))*Math.max(0,Math.min(t.bottom,box.bottom)-Math.max(t.top,box.top));
          if(t.width*t.height>0&&area/(t.width*t.height)>.05) overlap.push({element:e.tagName.toLowerCase(),text:e.innerText.trim().slice(0,80),boxOverlap:Number((area/(t.width*t.height)).toFixed(3))});
        }
      }
      return {projectedBoxOverlap:overlap,path:n.dataset.tnModel,role:n.dataset.tnModelRole||'primary',state:n.dataset.tnModelState,coverage:Number(n.dataset.tnModelCoverage||0),
        clipped:n.dataset.tnModelClipped==='true',width:r.width,height:r.height,viewportWidth:innerWidth,viewportHeight:innerHeight};
    }));
    // Target the hero's own scroll track rather than relying only on whole-page quartiles.
    const targeted=[];
    if(name==='desktop'&&heroFraming.length){
      for(const f of [.18,.45]){
        await page.evaluate(f=>{
          const host=document.querySelector('#home [data-tn-model]');
          const track=host?.closest('[data-tn-camera-track]')||host;
          if(track){const r=track.getBoundingClientRect();window.scrollTo({top:scrollY+r.top+Math.max(innerHeight*.4,r.height-innerHeight*.35)*f,behavior:'instant'});}
        },f);
        await page.waitForTimeout(900);
        targeted.push(...await page.locator('[data-tn-model]').evaluateAll(nodes=>nodes.map((n,index)=>({index,path:n.dataset.tnModel,state:n.dataset.tnModelState,frames:Number(n.dataset.tnFrames||0),pose:n.dataset.tnCameraPose||'',motionPose:n.dataset.tnModelMotionPose||n.dataset.tnCameraPose||'',nativeMotion:!!n.dataset.tnModelMotionPose,preset:n.dataset.tnMotionPreset||'custom',canvas:!!n.querySelector('canvas')}))));
      }
    }
    const filmSamples=[];
    const isFilm=await page.locator('#home[data-tn-hero-film]').count()===1;
    const pinnedFilm=await page.locator('#home[data-tn-film-version="2"]').count()===1;
    const backgroundFilm=await page.locator('#home[data-tn-film-background]').count()===1;
    const compactFilm=await page.locator('#home[data-tn-film-pace="compact"]').count()===1;
    const smoothFilm=await page.locator('#home[data-tn-film-engine="smooth"]').count()===1;
    const stableCamera=await page.locator('#home[data-tn-film-camera="stable"]').count()===1;
    if(isFilm){
      if(name==='mobile'){await page.emulateMedia({reducedMotion:'no-preference'});await page.waitForTimeout(500);}
      for(const fraction of (pinnedFilm?[0,.125,.25,.375,.5,.625,.75,.875,1,.25]:[0,.25,.5,.75,1,.25])){
        stage=name+' hero film '+fraction;
        await page.evaluate(f=>{
          const root=document.querySelector('#home[data-tn-hero-film]'),r=root.getBoundingClientRect();
          window.scrollTo({top:scrollY+r.top+Math.max(0,r.height-innerHeight)*f,behavior:'instant'});
        },fraction);
        await page.waitForTimeout(1000);
        if(smoothFilm&&pinnedFilm){
          // Slow software WebGL may need extra frames to reach the scroll target.
          await page.waitForFunction(f=>{
            const host=document.querySelector('#home [data-tn-model][data-tn-model-role="primary"]');
            return host?.dataset.tnModelState==='ready'&&Math.abs(Number(host.dataset.tnCameraProgress)-f)<=.0025;
          },fraction,{timeout:3500}).catch(()=>{});
        }
        const sample=await page.evaluate(()=>{
          const root=document.querySelector('#home[data-tn-hero-film]'),host=root.querySelector('[data-tn-model][data-tn-model-role="primary"]');
          const h=root.querySelector('h1'),copy=root.querySelector('.hero-content');
          if(!host||!h||!copy)return {ok:false};
          const r=host.getBoundingClientRect(),hr=h.getBoundingClientRect();
          const bounds=(host.dataset.tnModelScreenBounds||'').split(',').map(Number);
          const range=document.createRange();range.selectNodeContents(h);
          const rects=[...range.getClientRects()];
          const framed=bounds.length===4&&bounds.every(Number.isFinite)&&r.left+bounds[0]*r.width>=-2&&r.left+bounds[2]*r.width<=innerWidth+2&&r.top+bounds[1]*r.height>=-2&&r.top+bounds[3]*r.height<=innerHeight+2;
          const textVisible=Number(getComputedStyle(copy).opacity)>=.95&&rects.length>0&&rects.every(x=>x.left>=-2&&x.right<=innerWidth+2&&x.top>=0&&x.bottom<=innerHeight);
          const screen=root.querySelector('.tn-film-screen')?.getBoundingClientRect()
          const opacity=el=>{if(!el)return null;let alpha=1;for(let n=el;n&&n!==root.parentElement;n=n.parentElement){const s=getComputedStyle(n);if(s.visibility==='hidden'||s.display==='none')return 0;alpha*=Number(s.opacity)}return alpha}
          const descriptionEl=root.querySelector('.hero-sub'),actionsEl=root.querySelector('.hero-actions')
          const canvas=host.querySelector('canvas')?.getBoundingClientRect()
          const layer=root.querySelector('[data-tn-film-background-layer]')
          const lr=layer?.getBoundingClientRect()
          const contentWidth=document.documentElement.clientWidth;
          const centerX=bounds.length===4?(r.left+(bounds[0]+bounds[2])*r.width/2)/contentWidth:null
          const centerY=bounds.length===4?(r.top+(bounds[1]+bounds[3])*r.height/2)/innerHeight:null
          const overlayAbove=Boolean(layer&&copy.parentElement===layer.parentElement&&Number(getComputedStyle(copy).zIndex)>Number(getComputedStyle(layer).zIndex))
          const backgroundLayer=Boolean(layer&&host.parentElement===layer&&layer.parentElement===screenElement()&&getComputedStyle(layer).position==='absolute'&&getComputedStyle(host).visibility==='visible'&&Number(getComputedStyle(host).opacity)>.95)
          function screenElement(){return root.querySelector('.tn-film-screen')}
          return {yaw:Number(host.dataset.tnRelativeYaw),objectYaw:Number(host.dataset.tnObjectYaw)*180/Math.PI,reveal:Number(root.dataset.tnFilmReveal),progress:Number(host.dataset.tnCameraProgress),framed,coverage:Number(host.dataset.tnModelCoverage),clipped:host.dataset.tnModelClipped==='true',width:r.width,height:r.height,textVisible,textBottom:hr.bottom,modelTop:r.top,viewportWidth:innerWidth,viewportHeight:innerHeight,
            cameraMode:host.dataset.tnModelCameraMode,cameraDistance:Number(host.dataset.tnModelCameraDistance||0),scrollBehavior:getComputedStyle(document.documentElement).scrollBehavior,targetProgress:Number(host.dataset.tnModelTargetProgress??host.dataset.tnCameraProgress),frameElapsed:Number(host.dataset.tnModelFrameElapsed||0),pinMode:root.dataset.tnFilmPin,screenPosition:getComputedStyle(root.querySelector('.tn-film-screen')||root).position,bufferResizes:Number(host.dataset.tnModelBufferResizes||0),bufferWidth:host.querySelector('canvas')?.width,bufferHeight:host.querySelector('canvas')?.height,frames:Number(host.dataset.tnFrames||0),trackHeight:root.getBoundingClientRect().height,screenTop:screen?.top,screenHeight:screen?.height,screenWidth:screen?.width,turn:Number(root.dataset.tnFilmTurn)||180,title:Number(root.dataset.tnFilmTitle),description:Number(root.dataset.tnFilmDescription),actions:Number(root.dataset.tnFilmActions),actualTitle:opacity(h),actualDescription:opacity(descriptionEl),actualActions:opacity(actionsEl),canvasHeight:canvas?.height,canvasWidth:canvas?.width,canvasLeft:canvas?.left,canvasTop:canvas?.top,contentWidth,centerX,centerY,overlayAbove,backgroundLayer,layerLeft:lr?.left,layerTop:lr?.top,layerWidth:lr?.width,layerHeight:lr?.height};
        });
        filmSamples.push({...sample,fraction});
        if([0,.5,1].includes(fraction))await capture(page,name+'-hero-film-'+Math.round(fraction*100)+'.png');
      }
    }
    let filmIdle=null;
    if(smoothFilm&&pinnedFilm){
      const model=page.locator('#home [data-tn-model][data-tn-model-role="primary"]');
      await page.waitForTimeout(700);
      const before=Number(await model.getAttribute('data-tn-frames')||0);
      await page.waitForTimeout(500);
      const after=Number(await model.getAttribute('data-tn-frames')||0);
      filmIdle={before,after,extraFrames:after-before};
    }
    let filmRelease=null;
    if(pinnedFilm){
      await page.evaluate(()=>{const root=document.querySelector('#home[data-tn-film-version="2"]'),r=root.getBoundingClientRect();window.scrollTo({top:scrollY+r.top+r.height-innerHeight+innerHeight*.35,behavior:'instant'});});
      await page.waitForTimeout(700);
      filmRelease=await page.evaluate(()=>{const screen=document.querySelector('#home .tn-film-screen').getBoundingClientRect();return {top:screen.top,bottom:screen.bottom,viewport:innerHeight}});
    }
    let shortFilm=null;
    if(pinnedFilm&&name==='desktop'){
      await page.setViewportSize({width:1100,height:540});
      await page.waitForTimeout(500);
      await page.evaluate(()=>{const root=document.querySelector('#home[data-tn-film-version="2"]'),r=root.getBoundingClientRect();window.scrollTo({top:scrollY+r.top+(r.height-innerHeight)*.5,behavior:'instant'});});
      await page.waitForTimeout(1000);
      shortFilm=await page.evaluate(()=>{const root=document.querySelector('#home[data-tn-film-version="2"]'),screen=root.querySelector('.tn-film-screen').getBoundingClientRect(),host=root.querySelector('[data-tn-model][data-tn-model-role="primary"]'),r=host.getBoundingClientRect();return {top:screen.top,height:screen.height,hostTop:r.top,hostHeight:r.height,viewport:innerHeight,progress:Number(host.dataset.tnCameraProgress),clipped:host.dataset.tnModelClipped==='true'}});
      await capture(page,'desktop-hero-film-short.png');
      await page.setViewportSize({width,height});
      await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(500);
    }
    if(isFilm&&name==='mobile'){await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(500);}
    const sceneDiagnostics={carousels:[],stories:[]};
    const carousels=page.locator('[data-tn-carousel]');
    const stories=page.locator('[data-tn-story]');
    // Test the actual trusted controls, independently of sampled whole-page screenshots.
    for(let i=0;i<Math.min(await carousels.count(),6);i++){
      const c=carousels.nth(i);
      const track=c.locator('[data-tn-carousel-track]');
      let ok=false;
      try {
        if(!await c.isVisible())throw Error('Carousel not visible');
        await c.scrollIntoViewIfNeeded({timeout:3000});
        const count=await c.locator('[data-tn-slide]').count();
        await track.evaluate(el=>el.scrollTo({left:0,behavior:'instant'}));
        await page.waitForTimeout(150);
        const before=await track.evaluate(el=>el.scrollLeft);
        const button=c.locator('[data-tn-carousel-next]');
        if(count>=3&&await button.isEnabled()){
          await button.click({timeout:3000});
          await page.waitForFunction(({i,before})=>{
            const node=document.querySelectorAll('[data-tn-carousel]')[i];
            return Number(node?.dataset.tnActive)>0&&(node?.querySelector('[data-tn-carousel-track]')?.scrollLeft||0)>before+5;
          },{i,before},{timeout:3500});
          ok=true;
        }
        await track.evaluate(el=>el.scrollTo({left:0,behavior:'instant'}));
      }catch{}
      sceneDiagnostics.carousels.push({index:i,ok});
    }
    for(let i=0;i<Math.min(await stories.count(),6);i++){
      const story=stories.nth(i),chapters=story.locator('[data-tn-story-chapter]');
      let ok=false;
      try{
        if(!await story.isVisible())throw Error('Story not visible');
        const count=await chapters.count();
        if(count>=2){
          await chapters.first().evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}));
          await page.waitForTimeout(250);
          const first=await story.getAttribute('data-tn-active');
          await chapters.last().evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}));
          await page.waitForTimeout(250);
          const last=await story.getAttribute('data-tn-active');
          ok=first==='0'&&Number(last)===count-1;
        }
      }catch{}
      sceneDiagnostics.stories.push({index:i,ok});
    }
    const storyVisualLayouts=await page.locator('[data-tn-story]').evaluateAll(nodes=>nodes.map((story,index)=>{
      const chapters=[...story.querySelectorAll('[data-tn-story-chapter]')];
      const compact=matchMedia('(max-width:760px), (prefers-reduced-motion: reduce)').matches;
      if(compact){
        const visuals=chapters.map(chapter=>chapter.querySelector('.tn-story-mobile-visual'));
        const visualsOk=visuals.length===chapters.length&&visuals.length>0&&visuals.every(visual=>{
          if(!visual||getComputedStyle(visual).display==='none')return false;
          const child=visual.firstElementChild;
          if(!child)return false;
          const a=visual.getBoundingClientRect(),b=child.getBoundingClientRect();
          return a.width>0&&a.height>0&&b.width>0&&b.height>0&&child.scrollHeight<=child.clientHeight+4;
        });
        const captionsOk=chapters.length>0&&chapters.every(chapter=>{
          const caption=chapter.querySelector('.tn-story-caption');
          const heading=caption?.querySelector('h3');
          const paragraph=caption?.querySelector('p');
          return !!heading&&!!paragraph&&heading.getBoundingClientRect().height>0&&paragraph.getBoundingClientRect().height>0;
        });
        return {index,mode:'mobile',chapters:chapters.length,visualsOk,captionsOk,ok:visualsOk&&captionsOk};
      }
      const stage=story.querySelector('.tn-story-stage');
      const visual=story.querySelector('.tn-story-visual');
      const child=visual?.firstElementChild;
      const a=stage?.getBoundingClientRect(),b=visual?.getBoundingClientRect(),c=child?.getBoundingClientRect();
      const sticky=!!stage&&getComputedStyle(stage).position==='sticky';
      const visualOk=!!child&&!!b&&!!c&&b.width>0&&b.height>innerHeight*.35&&c.width>0&&c.height>0&&c.height<=b.height+4;
      return {index,mode:'desktop',chapters:chapters.length,sticky,visualOk,ok:chapters.length>=2&&sticky&&visualOk&&a.height>innerHeight*.4};
    }));
    let heroObject=null;
    if(sceneContract?.heroPreset){
      stage=name+' procedural hero checks';
      await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
      const object=page.locator('#home [data-tn-hero-object]');
      if(name==='desktop') await page.waitForFunction(()=>document.querySelector('#home [data-tn-hero-object]')?.dataset.tnObjectState==='ready',{},{timeout:12000}).catch(()=>{});
      if(await object.count()===1){
        const inspect=()=>object.evaluate(el=>{
          const r=el.getBoundingClientRect(),home=el.closest('#home'),h=home.getBoundingClientRect();
          const shown=node=>{if(!node)return false;const b=node.getBoundingClientRect();const s=getComputedStyle(node);return b.width>0&&b.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>.05;};
          const primary=el.dataset.tnObjectState==='ready'?el.querySelector('canvas'):el.querySelector('.tn-product-fallback');
          const overlap=[...home.querySelectorAll('h1,a[href="#contacts"],a[href="#services"]')].some(n=>{
            const b=n.getBoundingClientRect(),area=Math.max(0,Math.min(r.right,b.right)-Math.max(r.left,b.left))*Math.max(0,Math.min(r.bottom,b.bottom)-Math.max(r.top,b.top));
            return b.width*b.height>0&&area/(b.width*b.height)>.05;
          });
          const desktop=innerWidth>760;
          return {preset:el.dataset.tnObjectPreset,state:el.dataset.tnObjectState,pose:el.dataset.tnObjectPose||null,width:r.width,height:r.height,viewportWidth:innerWidth,viewportHeight:innerHeight,overlap,layoutOk:shown(el)&&shown(primary)&&!overlap&&r.width>=Math.min(h.width,innerWidth)*(desktop?.28:.65)&&r.height>=innerHeight*(desktop?.38:.24)&&r.left>=-2&&r.right<=innerWidth+2};
        });
        await page.waitForTimeout(500);
        const first=await inspect();
        let second=null;
        if(name==='desktop'){
          await page.evaluate(()=>{const h=document.querySelector('#home').getBoundingClientRect();window.scrollTo({top:Math.min(h.height*.22,innerHeight*.25),behavior:'instant'});});
          await page.waitForTimeout(900);
          second=await inspect();
          await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
          await page.waitForTimeout(300);
        }
        heroObject={first,second,layoutOk:first.preset===sceneContract.heroPreset&&first.layoutOk,motionOk:name!=='desktop'||(first.state==='ready'&&second?.state==='ready'&&first.pose!==null&&second.pose!==null&&Math.abs(Number(first.pose)-Number(second.pose))>=.05)};
      }else heroObject={layoutOk:false,motionOk:false,count:await object.count()};
    }
    const heroLayout=await page.locator('#home').evaluate(hero=>{
      const image=hero.querySelector('.hero-photo');
      const heading=hero.querySelector('h1');
      const cta=hero.querySelector('a[href="#contacts"],a[href="#services"]');
      const content=hero.querySelector('.hero-content')||hero;
      if(!heading||!cta)return false;
      const b=content.getBoundingClientRect(),h=heading.getBoundingClientRect(),c=cta.getBoundingClientRect();
      const within=(inner,outer)=>inner.left>=outer.left-2&&inner.right<=outer.right+2&&inner.top>=outer.top-2&&inner.bottom<=outer.bottom+2;
      let noOverlap=true;
      if(image){
        const a=image.getBoundingClientRect();
        noOverlap=a.right<=b.left+2||a.left>=b.right-2||a.bottom<=b.top+2||a.top>=b.bottom-2;
      }
      const mobile=innerWidth<=760;
      return noOverlap&&within(h,b)&&within(c,b)&&c.height>0&&(mobile?c.bottom<=hero.getBoundingClientRect().bottom+2:true);
    });
    const end=steps.at(-1);
    const brokenAfterScroll=await page.evaluate(()=>[...document.images].filter(i=>i.complete&&!i.naturalWidth).length);
    const motionChanged=steps.some((x,i)=>i>0&&JSON.stringify(x.layers)!==JSON.stringify(steps[i-1].layers))||filmSamples.some((x,i)=>i>0&&x.yaw!==filmSamples[i-1].yaw);
    const progressOk=steps.every(x=>x.scale!==null&&Math.abs(x.scale-x.actual)<.08&&Math.abs(x.top)<2&&x.width>=x.viewport-24)&&end.actual>.95;
    const checks={rendered:result.bodyText>80,noHorizontalOverflow:result.overflow<=2&&steps.every(s=>s.horizontalOverflow<=2),footer:result.footer&&result.footerLinks>0,progress:progressOk,noBrokenImages:Math.max(result.brokenImages,brokenAfterScroll)===0,noJsErrors:errors.length===0,noMissingAssets:missing.length===0,noExternalRequests:blocked.length===0};
    checks.completeSections=sections.every(x=>x.exists&&x.visible&&x.reachable&&x.heading&&x.textLength>=45);
    checks.headerNavigation=navigation.header&&navigation.allLinks&&menuOperable;
    if(contactContract?.length) checks.publicContacts=await page.evaluate(entries=>['#contacts','footer[data-tn-footer]'].every(selector=>{
      const target=document.querySelector(selector);
      return entries.every(entry=>[...(target?.querySelectorAll('[data-tn-contact]')||[])].some(n=>{
        const r=n.getBoundingClientRect(),s=getComputedStyle(n);
        return n.dataset.tnContact===entry.key&&n.textContent.includes(entry.value)&&(!entry.href||n.getAttribute('href')===entry.href)&&r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
      }));
    }),contactContract);
    checks.heroCTA=sections.some(x=>x.id==='home'&&x.cta);
    checks.heroLayout=heroLayout;
    if(pinnedFilm){
      const first=filmSamples[0],last=filmSamples[8],reverse=filmSamples[9],quarter=filmSamples[2],middle=filmSamples[4],late=filmSamples[7];
      const forward=filmSamples.slice(0,9);
      const earlyDescription=filmSamples[3],earlyActions=filmSamples[5];
      const captionsReady=compactFilm
        ? earlyDescription.description>.5&&(earlyDescription.actualDescription===null||earlyDescription.actualDescription>.5)&&earlyDescription.actions<=.01&&earlyActions.actions>=.99&&(earlyActions.actualActions===null||earlyActions.actualActions>=.95)
        : middle.description>.5&&(middle.actualDescription===null||middle.actualDescription>.5)&&middle.actions<=.01&&late.actions>=.99&&(late.actualActions===null||late.actualActions>=.95);
      const compactTrackOk=!compactFilm||(backgroundFilm&&filmSamples.every(s=>s.turn===180&&Math.abs(s.trackHeight-s.viewportHeight*(s.viewportWidth<=760?1.8:2.2))<=3));
      const smoothOk=!smoothFilm||(filmIdle&&filmIdle.before>0&&filmIdle.extraFrames>=0&&filmIdle.extraFrames<=1&&filmSamples.every(s=>((s.pinMode==='native'&&s.screenPosition==='sticky')||(s.pinMode==='transform'&&s.screenPosition==='absolute'))&&s.bufferResizes===first.bufferResizes&&s.bufferResizes>0&&s.bufferWidth===first.bufferWidth&&s.bufferHeight===first.bufferHeight));
      checks.heroFilm=filmSamples.length===10&&filmSamples.every(s=>s.framed&&!s.clipped&&s.coverage>=.55&&s.coverage<=.98&&Math.abs(s.screenTop)<=3&&Math.abs(s.screenHeight-s.viewportHeight)<=3&&s.screenWidth>=s.viewportWidth*.97&&Math.abs(s.modelTop)<=3&&s.height>=s.viewportHeight*.97&&s.width>=s.viewportWidth*.97&&s.canvasHeight>=s.viewportHeight*.97&&s.canvasWidth>=s.viewportWidth*.97&&Number.isFinite(s.objectYaw))&&
        first.title<=.01&&first.description<=.01&&first.actions<=.01&&first.actualTitle<=.01&&first.actualDescription<=.01&&first.actualActions<=.01&&quarter.title>.5&&quarter.actualTitle>.5&&quarter.description<=.01&&captionsReady&&compactTrackOk&&smoothOk&&(!stableCamera||filmSamples.every(s=>s.scrollBehavior==='auto'&&['fixed','track'].includes(s.cameraMode)&&s.cameraDistance>0))&&last.textVisible&&
        Math.abs(last.objectYaw-first.objectYaw-last.turn)<=1&&forward.every((s,i)=>i===0||s.objectYaw>forward[i-1].objectYaw+5)&&Math.abs(reverse.objectYaw-quarter.objectYaw)<=1&&
        filmRelease?.top < -filmRelease?.viewport*.25&&(name!=='desktop'||(shortFilm&&Math.abs(shortFilm.top)<=3&&Math.abs(shortFilm.height-shortFilm.viewport)<=3&&Math.abs(shortFilm.hostTop)<=3&&shortFilm.hostHeight>=shortFilm.viewport*.97&&shortFilm.progress>.4&&shortFilm.progress<.7&&!shortFilm.clipped));
      if(backgroundFilm){
        const origin=first.objectYaw
        checks.heroBackgroundCenter=filmSamples.every(s=>s.backgroundLayer&&s.overlayAbove&&Math.abs(s.layerLeft)<=3&&Math.abs(s.layerTop)<=3&&Math.abs(s.layerWidth-s.contentWidth)<=3&&Math.abs(s.layerHeight-s.viewportHeight)<=3&&Math.abs(s.canvasLeft)<=3&&Math.abs(s.canvasTop)<=3&&Math.abs(s.canvasWidth-s.contentWidth)<=3&&Number.isFinite(s.centerX)&&Number.isFinite(s.centerY)&&Math.abs(s.centerX-.5)<=.035&&Math.abs(s.centerY-.5)<=.035)
        const expectedTurn=compactFilm?180:360;
        checks.heroFullTurn=filmSamples.every(s=>s.turn===expectedTurn)&&[0,2,4,6,8].every((index,i)=>Math.abs(filmSamples[index].objectYaw-origin-i*expectedTurn/4)<=1.5)
        if(!checks.heroFilm||!checks.heroFullTurn){
          console.log('FILM_DIAGNOSTICS: '+JSON.stringify({device:name,captionsReady,compactTrackOk,smoothOk,filmIdle,filmRelease,shortFilm,samples:filmSamples.map(s=>({fraction:s.fraction,progress:s.progress,targetProgress:s.targetProgress,angle:s.objectYaw,expectedAngle:origin+s.fraction*expectedTurn,frameElapsed:s.frameElapsed,cameraMode:s.cameraMode,cameraDistance:s.cameraDistance,screenTop:s.screenTop,pinMode:s.pinMode,bufferResizes:s.bufferResizes,coverage:s.coverage,clipped:s.clipped}))}))
        }
      }
    } else if(isFilm){
      const [start,q,mid,late,end,reverse]=filmSamples;
      checks.heroFilm=filmSamples.length===6&&filmSamples.every(s=>s.framed&&!s.clipped&&s.coverage>=.62&&s.coverage<=.98&&s.width>=s.viewportWidth*.7&&s.height>=s.viewportHeight*(name==='desktop'?.38:.25)&&Number.isFinite(s.yaw))&&
        start.reveal<=.05&&start.progress<=.05&&q.reveal<=.05&&mid.progress>q.progress+.1&&late.reveal>=.95&&late.textVisible&&end.textVisible&&
        Math.abs(end.yaw-start.yaw)>=60&&Math.abs(mid.yaw-start.yaw)>=20&&Math.abs(end.yaw-mid.yaw)>=15&&Math.abs(reverse.yaw-q.yaw)<=5;
    }
    if(sceneContract?.heroPreset){checks.heroObjectLayout=heroObject?.layoutOk===true;if(name==="desktop")checks.heroObjectMotion=heroObject?.motionOk===true;}
    checks.serviceCards=sections.some(x=>x.id==='services'&&x.distinctCards>=3);
    if(aboutMetrics.present) checks.aboutMetrics=aboutMetrics.count>0&&aboutMetrics.complete&&aboutMetrics.values.every(Boolean);
    if(report.profile==='cinema'||storyVisualLayouts.length) checks.storyVisuals=storyVisualLayouts.length>0&&storyVisualLayouts.every(x=>x.ok);
    if(expectedModels.length && report.profile==='cinema') checks.heroImportedModel=sections.some(x=>x.id==='home'&&x.heroModel);
    if(expectedModels.length){
      const observed=[...steps.flatMap(x=>x.models),...sectionModelSamples,...targeted];
      if(report.profile==='cinema') checks.heroFraming=heroFraming.length>0&&heroFraming.every(m=>m.state==='ready'&&m.coverage>=.62&&m.coverage<=.98&&!m.clipped&&(m.role==='accent'?(m.width>=m.viewportWidth*(name==='desktop'?.12:.25)&&m.height>=100):(m.width>=m.viewportWidth*(name==='desktop'?.32:.70)&&m.height>=m.viewportHeight*(name==='desktop'?.38:.25))));
      checks.importedModelsReady=expectedModels.every(path=>observed.some(m=>m.path===path&&m.state==='ready'&&m.canvas&&m.frames>0));
      if(name==='desktop') {
        // Require a changed pose within the SAME DOM instance. Distinct static
        // models of the same path cannot masquerade as movement.
        const varied=(path,field)=>{
          const matching=observed.filter(m=>m.path===path&&m.state==='ready'&&m.frames>0&&m[field]);
          const instances=new Set(matching.map(m=>m.index));
          return [...instances].some(i=>new Set(matching.filter(m=>m.index===i).map(m=>m[field])).size>=2);
        };
        if(observed.some(m=>m.nativeMotion)) checks.modelMotionChanges=expectedModels.every(path=>varied(path,'motionPose'));
        else checks.cameraChanges=expectedModels.every(path=>varied(path,'pose'));
      }
    }
    if(report.profile==='cinema') {checks.scenes=result.scenes>=3;if(name==='desktop') checks.scrollMotion=motionChanged;}
    if(sceneContract?.version===1||sceneDiagnostics.carousels.length||sceneDiagnostics.stories.length){
      if(sceneContract?.version===1) {
        const middle='section[data-tn-section="about"],section[data-tn-section="services"],section[data-tn-section="benefits"]';
        checks.sceneComponents=await page.evaluate(selector=>{
          const sections=[...document.querySelectorAll(selector)];
          return sections.some(s=>s.querySelector('[data-tn-carousel]'))&&sections.some(s=>s.querySelector('[data-tn-story]'));
        },middle);
      }
      if(sceneContract?.version===1||sceneDiagnostics.carousels.length) checks.carouselControls=sceneDiagnostics.carousels.length>0&&sceneDiagnostics.carousels.every(x=>x.ok);
      if(sceneContract?.version===1||sceneDiagnostics.stories.length) checks.storyProgress=sceneDiagnostics.stories.length>0&&sceneDiagnostics.stories.every(x=>x.ok);
    }
    report.checks.push({name,checks,film:{enabled:isFilm,pinned:pinnedFilm,compact:compactFilm,smooth:smoothFilm,stableCamera},metrics:result,sections,navigation,heroFraming,heroObject,aboutMetrics,steps,filmSamples,filmIdle,filmRelease,shortFilm,sceneDiagnostics,storyVisualLayouts,errors:errors.slice(0,20),missing:missing.slice(0,20),blocked:blocked.slice(0,20)});
    await context.close();
  }
} catch(error){report.error=String(error).slice(0,700);report.errorStage=stage;}
finally { if(browser) await browser.close().catch(error=>{if(!report.error){report.error=String(error).slice(0,700);report.errorStage='browser close';}}); }
finalizeAudit(report);
await writeFile('/report/quality-report.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,functionalPassed:report.functionalPassed,screenshotsComplete:report.screenshotsComplete,screenshotFailures:report.screenshotFailures,missingScreenshots:report.missingScreenshots,unexpectedScreenshots:report.unexpectedScreenshots,duplicateScreenshots:report.duplicateScreenshots,checks:report.checks.map(({name,checks})=>({name,checks})),error:report.error,errorStage:report.errorStage},null,2));
if(!report.passed) process.exitCode=1;
