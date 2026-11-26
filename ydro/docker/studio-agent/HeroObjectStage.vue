<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'
const props=defineProps({
  preset:{type:String,default:'serum'},
  label:{type:String,default:'Предметная композиция'},
  brand:{type:String,default:''},
  accent:{type:String,default:'#c8a878'},
  tone:{type:String,default:'#79502d'}
})
const kind=computed(()=>['serum','jar','tube','perfume'].includes(props.preset)?props.preset:'serum')
const root=ref(null),surface=ref(null),ready=ref(false)
let runtime=null,observer,resize,media,visible=false,closed=false,loading=false,failed=false,frame=0,timer=0,last=-Infinity
const valid=(v,f)=>/^#[0-9a-f]{6}$/i.test(v)?v:f
function cancel(){
  if(frame)cancelAnimationFrame(frame)
  if(timer)clearTimeout(timer)
  frame=timer=0
}
function dispose(){
  cancel();runtime?.dispose();runtime=null;ready.value=false
}
function progress(){
  const r=(root.value.closest('section')||root.value).getBoundingClientRect()
  return Math.max(0,Math.min(1,-r.top/Math.max(1,Math.min(r.height*.65,innerHeight*.65))))
}
function schedule(){
  if(closed||!visible||!runtime||media.matches||document.hidden||frame||timer)return
  timer=setTimeout(()=>{
    timer=0
    if(closed||!visible||!runtime||media.matches||document.hidden)return
    frame=requestAnimationFrame(()=>{
      frame=0
      if(closed||!visible||!runtime||media.matches||document.hidden)return
      last=performance.now()
      try{runtime.draw(progress())}catch{failed=true;dispose()}
    })
  },Math.max(0,42-(performance.now()-last)))
}
async function init(){
  if(closed||!visible||media.matches||document.hidden||runtime||loading||failed)return
  loading=true
  let renderer=null
  const resources=new Set()
  try{
    const T=await import('three')
    if(closed||!visible||media.matches||document.hidden)return
    renderer=new T.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'})
    renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25))
    renderer.outputColorSpace=T.SRGBColorSpace
    renderer.toneMapping=T.ACESFilmicToneMapping
    renderer.toneMappingExposure=1.35
    surface.value.appendChild(renderer.domElement)
    const scene=new T.Scene(),object=new T.Group()
    scene.add(object)
    const camera=new T.PerspectiveCamera(34,1,.1,40)
    const material=(c,m,r)=>{const a=new T.MeshStandardMaterial({color:c,metalness:m,roughness:r});resources.add(a);return a}
    const body=material(valid(props.tone,'#79502d'),.25,.25)
    const gold=material(valid(props.accent,'#c8a878'),.6,.28),dark=material('#25201c',.08,.35),paper=material('#eadfc9',.02,.65)
    function mesh(g,m,y,parent=object){resources.add(g);const a=new T.Mesh(g,m);a.position.y=y;parent.add(a);return a}
    const cylinder=(a,b,h,m,y)=>mesh(new T.CylinderGeometry(a,b,h,40),m,y)
    const lathe=(points,y)=>mesh(new T.LatheGeometry(points.map(([x,y])=>new T.Vector2(x,y)),40),body,y)
    let labelZ=.62,labelY=-.2,labelW=.86
    if(kind.value==='jar'){
      lathe([[0,0],[.78,0],[.85,.1],[.85,.92],[.76,1],[0,1]],-.76)
      cylinder(.85,.85,.33,gold,.39);labelZ=.86;labelW=1.05
    }else if(kind.value==='tube'){
      lathe([[0,0],[.42,0],[.54,.14],[.62,1.8],[.62,1.96],[0,1.96]],-1)
      cylinder(.42,.42,.33,gold,-1.16);labelZ=.63;labelY=.12
    }else if(kind.value==='perfume'){
      lathe([[0,0],[.65,0],[.71,.1],[.71,1.45],[.58,1.62],[.28,1.72],[0,1.72]],-1.08)
      cylinder(.3,.3,.24,gold,.77);cylinder(.41,.41,.47,dark,1.1);labelZ=.72
    }else{
      lathe([[0,0],[.49,0],[.6,.1],[.6,1.47],[.52,1.64],[.3,1.77],[.28,1.82],[0,1.82]],-1.16)
      cylinder(.33,.33,.25,gold,.79);cylinder(.23,.23,.38,dark,1.08)
      mesh(new T.SphereGeometry(.23,24,12),dark,1.27)
    }
    const c=document.createElement('canvas');c.width=512;c.height=256
    const ctx=c.getContext('2d')
    if(ctx){
      ctx.fillStyle='#eadfc9';ctx.fillRect(0,0,512,256);ctx.fillStyle='#34291e';ctx.textAlign='center';ctx.font='42px Georgia';ctx.fillText(props.brand.slice(0,22),256,113,440)
      ctx.strokeStyle='#a78c6c';ctx.beginPath();ctx.moveTo(96,144);ctx.lineTo(416,144);ctx.stroke()
      ctx.font='19px Georgia';ctx.fillText(props.label.slice(0,34),256,187,440)
      const tex=new T.CanvasTexture(c);tex.colorSpace=T.SRGBColorSpace;resources.add(tex);paper.map=tex;paper.needsUpdate=true
    }
    mesh(new T.PlaneGeometry(labelW,.51),paper,labelY).position.z=labelZ
    const clothGeo=new T.PlaneGeometry(6,2.7,44,20),pos=clothGeo.attributes.position
    for(let i=0;i<pos.count;i++){const x=pos.getX(i),y=pos.getY(i);pos.setZ(i,.22*Math.sin(x*2.4+y*2)+.12*Math.cos(x*3-y))}
    clothGeo.computeVertexNormals()
    const clothMat=material(valid(props.accent,'#c8a878'),.25,.46);clothMat.side=T.DoubleSide
    const cloth=mesh(clothGeo,clothMat,-1.35,scene);cloth.rotation.x=-Math.PI*.42
    scene.add(new T.HemisphereLight('#fff0d9','#333036',2.2))
    const key=new T.DirectionalLight('#fff1d8',3.3);key.position.set(-3,4,5);scene.add(key)
    const rim=new T.DirectionalLight('#ffe1ac',3.7);rim.position.set(4,1,-3);scene.add(rim)
    const fill=new T.DirectionalLight('#bccddd',1.2);fill.position.set(2,3,4);scene.add(fill)
    let lastW=0,lastH=0
    function draw(p){
      const w=Math.max(1,surface.value.clientWidth),h=Math.max(1,surface.value.clientHeight)
      if(w!==lastW||h!==lastH){
        const scale=Math.min(1,1200/Math.max(w,h))
        renderer.setSize(Math.max(1,Math.floor(w*scale)),Math.max(1,Math.floor(h*scale)),false)
        camera.aspect=w/h;camera.updateProjectionMatrix();lastW=w;lastH=h
      }
      camera.position.set(.12+p*.2,.3,Math.max(5.8,6.9-.7*p,5.4/camera.aspect));camera.lookAt(0,0,0)
      object.rotation.y=-.25+p*.6;object.rotation.z=-.06+p*.045
      key.position.x=-3+5*p;rim.intensity=3.7+p*.8
      cloth.position.z=-.5-p*.65;cloth.position.y=-1.35-p*.12
      renderer.render(scene,camera)
    }
    const lost=e=>{e.preventDefault();failed=true;dispose()}
    renderer.domElement.addEventListener('webglcontextlost',lost)
    runtime={draw,dispose(){renderer.domElement.removeEventListener('webglcontextlost',lost);resources.forEach(x=>x.dispose());renderer.dispose();renderer.domElement.remove()}}
    draw(progress());ready.value=true
  }catch{
    failed=true
    if(runtime)dispose()
    else{resources.forEach(x=>x.dispose());renderer?.dispose();renderer?.domElement.remove()}
  }finally{loading=false}
}
function refresh(){
  if(!visible||media.matches||document.hidden){cancel();if(media.matches)dispose();return}
  if(runtime)schedule();else init()
}
onMounted(()=>{
  media=matchMedia('(max-width:760px), (prefers-reduced-motion: reduce)')
  observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;refresh()})
  observer.observe(root.value)
  resize=new ResizeObserver(refresh);resize.observe(root.value)
  window.addEventListener('scroll',schedule,{passive:true})
  media.addEventListener('change',refresh);document.addEventListener('visibilitychange',refresh)
})
onBeforeUnmount(()=>{
  closed=true;observer?.disconnect();resize?.disconnect()
  window.removeEventListener('scroll',schedule);media?.removeEventListener('change',refresh)
  document.removeEventListener('visibilitychange',refresh);dispose()
})
</script>
<template>
  <figure ref="root" class="tn-hero-object" data-tn-hero-object :data-tn-object-preset="kind" :data-tn-object-state="ready?'ready':'fallback'" :aria-label="label">
    <div class="tn-hero-object-glow" :style="{'--object-accent':accent}"></div>
    <div v-show="!ready" class="tn-product-fallback" :class="'is-'+kind" :style="{'--object-tone':tone,'--object-accent':accent}" role="img" :aria-label="label">
      <div class="tn-product-cap"></div><div class="tn-product-body"><span>{{ brand.slice(0,22) }}</span><small>{{ label.slice(0,34) }}</small></div>
    </div>
    <div ref="surface" class="tn-product-canvas" :class="{'is-ready':ready}" aria-hidden="true"></div>
  </figure>
</template>
<style scoped>
.tn-hero-object{position:relative;isolation:isolate;display:grid;place-items:center;width:100%;min-width:0;min-height:clamp(340px,65svh,760px);margin:0;overflow:clip}
.tn-hero-object-glow{position:absolute;inset:0;background:radial-gradient(ellipse,color-mix(in srgb,var(--object-accent) 25%,transparent),transparent 66%);pointer-events:none}
.tn-product-fallback{position:relative;width:clamp(100px,27%,200px);aspect-ratio:1/2.15;filter:drop-shadow(16px 22px 20px #0005)}
.tn-product-body{position:absolute;inset:24% 0 0;border-radius:14% 14% 12% 12%;background:linear-gradient(100deg,#252019,var(--object-tone) 23%,#c5a677 38%,var(--object-tone) 58%,#30251d 95%);display:grid;align-content:center;text-align:center;padding:12%;color:#34291e}
.tn-product-body span,.tn-product-body small{display:block;background:#eadfc9;padding:8% 2%;overflow-wrap:anywhere;font-family:Georgia,serif}
.tn-product-body small{font-size:clamp(8px,1vw,13px);padding-top:0}
.tn-product-cap{position:absolute;left:30%;width:40%;top:5%;height:25%;border-radius:15% 15% 4% 4%;background:linear-gradient(90deg,#7e6649,var(--object-accent),#e2ceaa,#8c7151)}
.tn-product-cap:before{content:"";position:absolute;inset:-18% 15% 42%;background:#26211e;border-radius:30%}
.is-jar{width:clamp(145px,43%,290px);aspect-ratio:1.1}.is-jar .tn-product-cap{left:0;width:100%;top:12%;height:25%}.is-jar .tn-product-cap:before{display:none}
.is-tube .tn-product-body{inset:0 0 15%;clip-path:polygon(0 0,100% 0,80% 100%,20% 100%)}.is-tube .tn-product-cap{top:auto;bottom:0;left:25%;width:50%;height:20%}.is-tube .tn-product-cap:before{display:none}
.is-perfume .tn-product-cap:before{inset:-18% -15% 25%;border-radius:12%}
.tn-product-canvas{position:absolute;inset:0;opacity:0;pointer-events:none}.tn-product-canvas.is-ready{opacity:1}.tn-product-canvas :deep(canvas){display:block;width:100%;height:100%}
@media(max-width:760px){.tn-hero-object{min-height:300px;max-height:440px}}
</style>
