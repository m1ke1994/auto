<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'

const PRESETS=['serum','jar','tube','perfume','cup','vase','watch','ring','microphone']
const PALETTES={
  serum:{tone:'#a85b27',accent:'#d5b47a'},
  jar:{tone:'#e9dfcf',accent:'#c9a66c'},
  tube:{tone:'#e8dfd1',accent:'#b99a70'},
  perfume:{tone:'#654127',accent:'#c8a36b'},
  cup:{tone:'#eee5d7',accent:'#b88d5b'},
  vase:{tone:'#9aa99a',accent:'#c8a36b'},
  watch:{tone:'#263846',accent:'#c8a36b'},
  ring:{tone:'#e9dfcf',accent:'#c8a36b'},
  microphone:{tone:'#292a2d',accent:'#c8a36b'}
}
const props=defineProps({
  preset:{type:String,default:'serum'},
  label:{type:String,default:'Предметная композиция'},
  brand:{type:String,default:''},
  accent:{type:String,default:''},
  tone:{type:String,default:''}
})
const kind=computed(()=>PRESETS.includes(props.preset)?props.preset:'serum')
const toneColor=computed(()=>/^#[0-9a-f]{6}$/i.test(props.tone)?props.tone:PALETTES[kind.value].tone)
const accentColor=computed(()=>/^#[0-9a-f]{6}$/i.test(props.accent)?props.accent:PALETTES[kind.value].accent)
const root=ref(null),surface=ref(null),ready=ref(false)
let runtime=null,observer=null,resize=null,media=null
let visible=false,closed=false,loading=false,failed=false,frame=0,timer=0,last=-Infinity

const clamp=(n,a,b)=>Math.max(a,Math.min(b,n))
function cancel(){
  if(frame)cancelAnimationFrame(frame)
  if(timer)clearTimeout(timer)
  frame=timer=0
}
function dispose(){
  cancel()
  const active=runtime
  runtime=null
  ready.value=false
  active?.dispose()
}
function progress(){
  if(!root.value)return 0
  const section=root.value.closest('[data-tn-section="home"]')||root.value.closest('section')||root.value
  const rect=section.getBoundingClientRect()
  const travel=Math.max(1,Math.min(rect.height*.9,innerHeight*.95))
  return clamp(-rect.top/travel,0,1)
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
function makeLabelMaterial(T,resources){
  const canvas=document.createElement('canvas')
  canvas.width=768;canvas.height=320
  const ctx=canvas.getContext('2d')
  if(ctx){
    const gradient=ctx.createLinearGradient(0,0,768,320)
    gradient.addColorStop(0,'#f6f0e5')
    gradient.addColorStop(.5,'#e9ddc8')
    gradient.addColorStop(1,'#f7f1e7')
    ctx.fillStyle=gradient;ctx.fillRect(0,0,768,320)
    ctx.strokeStyle='#b69a70';ctx.lineWidth=3;ctx.strokeRect(22,22,724,276)
    ctx.fillStyle='#30271f';ctx.textAlign='center';ctx.textBaseline='middle'
    ctx.font='600 48px Georgia, serif'
    ctx.fillText((props.brand||'ATELIER').slice(0,24).toUpperCase(),384,116,680)
    ctx.fillStyle='#927653';ctx.fillRect(250,166,268,2)
    ctx.fillStyle='#4a3b2c';ctx.font='28px Georgia, serif'
    ctx.fillText((props.label||'OBJECT').slice(0,36).toUpperCase(),384,224,680)
    ctx.fillStyle='#927653';ctx.font='16px Arial, sans-serif'
    ctx.fillText('FORM  /  MATERIAL  /  LIGHT',384,270,680)
  }
  const texture=new T.CanvasTexture(canvas)
  texture.colorSpace=T.SRGBColorSpace
  texture.anisotropy=4
  resources.add(texture)
  const material=new T.MeshPhysicalMaterial({map:texture,roughness:.48,metalness:.02,clearcoat:.12,side:T.DoubleSide})
  resources.add(material)
  return material
}
async function init(){
  if(closed||!visible||media.matches||document.hidden||runtime||loading||failed)return
  loading=true
  let renderer=null,pmrem=null
  const resources=new Set()
  try{
    const [T,environmentModule]=await Promise.all([
      import('three'),
      import('three/addons/environments/RoomEnvironment.js')
    ])
    if(closed||!visible||media.matches||document.hidden)return
    const {RoomEnvironment}=environmentModule
    renderer=new T.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power',premultipliedAlpha:false})
    renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.35))
    renderer.outputColorSpace=T.SRGBColorSpace
    renderer.toneMapping=T.ACESFilmicToneMapping
    renderer.toneMappingExposure=1.2
    renderer.transmissionResolutionScale=.65
    renderer.setClearColor(0x000000,0)
    renderer.shadowMap.enabled=true
    renderer.shadowMap.type=T.PCFSoftShadowMap
    surface.value.appendChild(renderer.domElement)

    const scene=new T.Scene()
    const object=new T.Group()
    scene.add(object)
    const camera=new T.PerspectiveCamera(36,1,.1,40)
    pmrem=new T.PMREMGenerator(renderer)
    const room=new RoomEnvironment()
    const environment=pmrem.fromScene(room,.04)
    room.dispose()
    resources.add(environment)
    scene.environment=environment.texture
    scene.environmentIntensity=1.18

    const physical=(color,options={})=>{
      const material=new T.MeshPhysicalMaterial({color,...options})
      resources.add(material)
      return material
    }
    const addMesh=(geometry,material,parent=object)=>{
      resources.add(geometry)
      const item=new T.Mesh(geometry,material)
      item.castShadow=true
      item.receiveShadow=true
      parent.add(item)
      return item
    }
    const cylinder=(top,bottom,height,material,x=0,y=0,z=0,parent=object)=>{
      const item=addMesh(new T.CylinderGeometry(top,bottom,height,64,1,false),material,parent)
      item.position.set(x,y,z)
      return item
    }
    const box=(w,h,d,material,x=0,y=0,z=0,parent=object)=>{
      const item=addMesh(new T.BoxGeometry(w,h,d),material,parent)
      item.position.set(x,y,z)
      return item
    }
    const sphere=(radius,material,x=0,y=0,z=0,parent=object)=>{
      const item=addMesh(new T.SphereGeometry(radius,32,20),material,parent)
      item.position.set(x,y,z)
      return item
    }
    const lathe=(points,material,y=0)=>{
      const geometry=new T.LatheGeometry(points.map(([x,v])=>new T.Vector2(x,v)),64)
      const item=addMesh(geometry,material)
      item.position.y=y
      return item
    }
    const ring=(radius,tube,material,y=0,x=0,z=0,parent=object)=>{
      const item=addMesh(new T.TorusGeometry(radius,tube,16,72),material,parent)
      item.rotation.x=Math.PI/2
      item.position.set(x,y,z)
      return item
    }
    const wrapLabel=(radius,height,y,labelMaterial)=>{
      const geometry=new T.CylinderGeometry(radius,radius,height,72,1,true,-.92,1.84)
      const item=addMesh(geometry,labelMaterial)
      item.position.y=y
      return item
    }
    const gold=physical(accentColor.value,{metalness:.82,roughness:.2,clearcoat:1,clearcoatRoughness:.08})
    const darkMetal=physical('#202124',{metalness:.72,roughness:.24,clearcoat:.9})
    const labelMaterial=makeLabelMaterial(T,resources)

    function glassMaterial(tint){
      return physical('#ffffff',{
        metalness:0,roughness:.035,transmission:.96,thickness:.62,ior:1.46,
        clearcoat:1,clearcoatRoughness:.035,attenuationColor:tint,
        attenuationDistance:1.65,envMapIntensity:1.4
      })
    }
    function satinTexture(){
      const canvas=document.createElement('canvas')
      canvas.width=512;canvas.height=512
      const ctx=canvas.getContext('2d')
      const gradient=ctx.createLinearGradient(0,0,512,512)
      gradient.addColorStop(0,'#806343')
      gradient.addColorStop(.24,'#d8c19a')
      gradient.addColorStop(.48,'#f1e2c5')
      gradient.addColorStop(.72,'#b5966e')
      gradient.addColorStop(1,'#71563a')
      ctx.fillStyle=gradient;ctx.fillRect(0,0,512,512)
      for(let i=0;i<2200;i++){
        const x=(i*73)%512,y=(i*137)%512
        ctx.fillStyle=i%2?'rgba(255,255,255,.035)':'rgba(50,32,16,.025)'
        ctx.fillRect(x,y,1,2)
      }
      const texture=new T.CanvasTexture(canvas)
      texture.colorSpace=T.SRGBColorSpace
      texture.wrapS=texture.wrapT=T.RepeatWrapping
      texture.repeat.set(1,1)
      texture.anisotropy=4
      resources.add(texture)
      return texture
    }

    if(kind.value==='serum'){
      const glass=glassMaterial('#d79a52')
      const liquid=physical('#a95219',{roughness:.14,metalness:.02,clearcoat:1,clearcoatRoughness:.06})
      lathe([[0,0],[.43,0],[.52,.06],[.54,.16],[.54,1.16],[.49,1.3],[.28,1.47],[.27,1.58],[0,1.58]],glass,-.82)
      lathe([[0,.06],[.42,.06],[.49,.15],[.49,1.02],[.42,1.08],[0,1.08]],liquid,-.76)
      cylinder(.3,.3,.17,gold,0,.83)
      ring(.3,.025,gold,.76)
      cylinder(.235,.235,.39,darkMetal,0,1.11)
      cylinder(.22,.22,.055,gold,0,1.33)
      sphere(.205,darkMetal,0,1.42)
      wrapLabel(.548,.42,-.18,labelMaterial)
    }else if(kind.value==='jar'){
      const ceramic=physical(toneColor.value,{roughness:.2,metalness:.025,clearcoat:.92,clearcoatRoughness:.1,sheen:.45,sheenColor:'#fff2dd'})
      const lid=physical(accentColor.value,{metalness:.76,roughness:.2,clearcoat:1})
      lathe([[0,0],[.68,0],[.79,.05],[.82,.13],[.82,.77],[.78,.84],[0,.84]],ceramic,-.58)
      lathe([[0,0],[.79,0],[.86,.035],[.86,.22],[.81,.28],[0,.28]],lid,.25)
      ring(.82,.035,gold,.22)
      ring(.77,.018,gold,.52)
      wrapLabel(.827,.43,-.08,labelMaterial)
    }else if(kind.value==='tube'){
      const plastic=physical(toneColor.value,{roughness:.3,metalness:.025,clearcoat:.75,clearcoatRoughness:.13,sheen:.35,sheenColor:'#fff1dc'})
      const shape=new T.Shape()
      shape.moveTo(-.43,-.83)
      shape.lineTo(-.36,.7)
      shape.quadraticCurveTo(0,.88,.36,.7)
      shape.lineTo(.43,-.83)
      shape.quadraticCurveTo(0,-.98,-.43,-.83)
      const geometry=new T.ExtrudeGeometry(shape,{depth:.16,bevelEnabled:true,bevelSegments:5,steps:1,bevelSize:.035,bevelThickness:.035,curveSegments:20})
      geometry.translate(0,0,-.08)
      addMesh(geometry,plastic)
      cylinder(.22,.22,.22,gold,0,-1.02)
      box(.72,.055,.035,gold,0,.76,.08)
      const flatLabel=addMesh(new T.PlaneGeometry(.57,.62),labelMaterial)
      flatLabel.position.set(0,.03,.17)
    }else if(kind.value==='perfume'){
      const glass=glassMaterial('#d2a16a')
      const liquid=physical('#8b4b23',{roughness:.12,clearcoat:1,clearcoatRoughness:.05})
      lathe([[0,0],[.56,0],[.68,.08],[.7,.18],[.7,1.1],[.65,1.27],[.45,1.45],[.25,1.52],[0,1.52]],glass,-.82)
      lathe([[0,.05],[.54,.05],[.62,.16],[.62,.98],[.56,1.05],[0,1.05]],liquid,-.77)
      cylinder(.25,.25,.2,gold,0,.83)
      ring(.25,.025,gold,.73)
      cylinder(.32,.32,.47,darkMetal,0,1.15)
      cylinder(.34,.34,.07,gold,0,.91)
      wrapLabel(.704,.48,-.13,labelMaterial)
    }else if(kind.value==='cup'){
      const porcelain=physical(toneColor.value,{roughness:.16,metalness:.015,clearcoat:1,clearcoatRoughness:.08,sheen:.55,sheenColor:'#fff7eb'})
      const coffee=physical('#3a2115',{roughness:.16,clearcoat:.65})
      cylinder(.83,.83,.09,porcelain,0,-.84)
      ring(.72,.025,gold,-.78)
      cylinder(.52,.42,.78,porcelain,0,-.37)
      ring(.515,.035,porcelain,-.01)
      cylinder(.42,.42,.06,porcelain,0,-.77)
      const surface=addMesh(new T.CircleGeometry(.485,72),coffee)
      surface.rotation.x=-Math.PI/2
      surface.position.y=.005
      const handle=addMesh(new T.TorusGeometry(.31,.075,20,56),porcelain)
      handle.position.set(.57,-.32,0)
      handle.scale.set(1.05,1.25,.72)
      const crema=physical('#b77c43',{roughness:.24})
      const swirl=addMesh(new T.TorusGeometry(.13,.012,8,48),crema)
      swirl.rotation.x=-Math.PI/2
      swirl.position.set(-.08,.014,.02)
    }else if(kind.value==='vase'){
      const ceramic=physical(toneColor.value,{roughness:.18,metalness:.025,clearcoat:1,clearcoatRoughness:.08,sheen:.7,sheenColor:'#f7f1df'})
      const stem=physical('#536d4d',{roughness:.55})
      const petal=physical('#eee1cf',{roughness:.34,sheen:.55})
      lathe([[0,0],[.34,0],[.45,.12],[.46,.3],[.31,.62],[.22,1.02],[.24,1.3],[.34,1.48],[.35,1.56],[0,1.56]],ceramic,-.78)
      ring(.35,.025,gold,.73)
      for(const [x,lean] of [[-.18,-.22],[0,.02],[.18,.24]]){
        const branch=cylinder(.018,.025,.92,stem,x,.93,0)
        branch.rotation.z=lean
        const leaf=sphere(.13,stem,x+lean*.36,1.02,0)
        leaf.scale.set(.18,.55,.08)
        leaf.rotation.z=lean-.55
        for(let i=0;i<5;i++){
          const angle=i*Math.PI*2/5
          const bloom=sphere(.085,petal,x+Math.cos(angle)*.12,1.48+Math.sin(angle)*.12,0)
          bloom.scale.set(.72,1.18,.55)
        }
        sphere(.065,gold,x,1.48,0)
      }
    }else if(kind.value==='watch'){
      const strap=physical(toneColor.value,{roughness:.48,metalness:.08,clearcoat:.3})
      const face=physical('#17242d',{roughness:.3,metalness:.18,clearcoat:.85})
      box(.42,.82,.13,strap,0,.96,-.025)
      box(.42,.82,.13,strap,0,-.96,-.025)
      const caseBody=cylinder(.69,.69,.2,gold,0,0,0)
      caseBody.rotation.x=Math.PI/2
      const dial=addMesh(new T.CircleGeometry(.59,72),face)
      dial.position.z=.112
      const bezel=addMesh(new T.TorusGeometry(.64,.052,16,72),gold)
      bezel.position.z=.13
      for(let i=0;i<12;i++){
        const a=i*Math.PI/6
        const marker=box(i%3===0?.035:.018,i%3===0?.105:.07,.018,gold,Math.sin(a)*.48,Math.cos(a)*.48,.15)
        marker.rotation.z=-a
      }
      const hourMat=physical('#eee4d4',{metalness:.15,roughness:.25})
      const hour=box(.045,.3,.022,hourMat,0,.12,.165)
      hour.rotation.z=-.4
      const minute=box(.026,.42,.022,hourMat,.08,.19,.17)
      minute.rotation.z=.22
      sphere(.055,gold,0,0,.18)
      const crown=cylinder(.09,.09,.18,gold,.76,0,0)
      crown.rotation.z=Math.PI/2
    }else if(kind.value==='ring'){
      const band=physical(accentColor.value,{metalness:.88,roughness:.16,clearcoat:1})
      const stone=physical('#c9e4ed',{metalness:.02,roughness:.045,transmission:.82,thickness:.42,ior:2.05,clearcoat:1,attenuationColor:'#9ac8d8',attenuationDistance:1.2})
      const setting=physical(accentColor.value,{metalness:.9,roughness:.14})
      const shank=addMesh(new T.TorusGeometry(.48,.085,20,96),band)
      shank.rotation.x=.08
      const gem=addMesh(new T.OctahedronGeometry(.23,1),stone)
      gem.position.set(0,.49,.02)
      gem.rotation.y=.2
      for(let i=0;i<4;i++){
        const a=i*Math.PI/2+Math.PI/4
        sphere(.035,setting,Math.cos(a)*.2,.48+Math.sin(a)*.2,.04)
      }
    }else if(kind.value==='microphone'){
      const body=physical(toneColor.value,{metalness:.68,roughness:.24,clearcoat:.85})
      const grille=physical('#55575b',{metalness:.82,roughness:.32})
      const stand=physical('#242528',{metalness:.74,roughness:.24})
      cylinder(.36,.36,.1,stand,0,-.9)
      cylinder(.045,.045,.72,stand,0,-.48)
      cylinder(.2,.22,.9,body,0,.25)
      const head=sphere(.22,grille,0,.79,0)
      head.scale.set(1,1.18,1)
      ring(.205,.025,gold,.62)
      ring(.215,.022,gold,.83)
      ring(.205,.02,grille,.99)
      for(let i=0;i<18;i++){
        const a=i*Math.PI*2/18
        cylinder(.006,.006,.28,grille,Math.sin(a)*.205,.79,Math.cos(a)*.205)
      }
      const yoke=addMesh(new T.TorusGeometry(.34,.025,12,56),gold)
      yoke.rotation.x=Math.PI/2
      yoke.position.y=.28
      box(.055,.3,.055,gold,-.34,.12,0)
      box(.055,.3,.055,gold,.34,.12,0)
    }

    const fabric=new T.PlaneGeometry(7.4,4.1,104,56)
    const vertices=fabric.attributes.position
    for(let i=0;i<vertices.count;i++){
      const x=vertices.getX(i),y=vertices.getY(i)
      const fold1=.22*Math.sin(x*1.22+y*.38)
      const fold2=.105*Math.sin(x*3.1-y*1.35)
      const fold3=.045*Math.cos(x*6.4+y*2.2)
      const ridge=.12*Math.exp(-Math.pow((x-.85)/.42,2))*Math.cos(y*2.3)
      vertices.setZ(i,fold1+fold2+fold3+ridge)
    }
    fabric.computeVertexNormals()
    const fabricMaterial=physical('#ffffff',{
      map:satinTexture(),metalness:.08,roughness:.3,clearcoat:.32,
      clearcoatRoughness:.22,sheen:1,sheenRoughness:.24,
      sheenColor:'#fff0d5',side:T.DoubleSide
    })
    const cloth=addMesh(fabric,fabricMaterial,scene)
    cloth.position.set(0,-.98,-1.62)
    cloth.rotation.x=-Math.PI*.385
    cloth.rotation.y=-.045

    const floorMaterial=new T.ShadowMaterial({opacity:.22})
    resources.add(floorMaterial)
    const floor=addMesh(new T.PlaneGeometry(8,8),floorMaterial,scene)
    floor.rotation.x=-Math.PI/2
    floor.position.y=-1.36
    floor.receiveShadow=true

    scene.add(new T.HemisphereLight('#fff0dc','#29232a',1.65))
    const key=new T.DirectionalLight('#fff0dc',3.5)
    key.position.set(-3.8,4.8,4.5)
    key.castShadow=true
    key.shadow.mapSize.set(1024,1024)
    Object.assign(key.shadow.camera,{left:-3.5,right:3.5,top:3.5,bottom:-3.5,near:.1,far:18})
    key.shadow.camera.updateProjectionMatrix()
    key.shadow.normalBias=.025
    key.shadow.radius=5
    scene.add(key)
    const rimLight=new T.DirectionalLight(accentColor.value,3.2)
    rimLight.position.set(4,1,-3)
    scene.add(rimLight)
    const fill=new T.DirectionalLight('#c8d8e7',1.05)
    fill.position.set(2,3,5)
    scene.add(fill)

    let lastW=0,lastH=0
    function draw(p){
      const w=Math.max(1,surface.value.clientWidth),h=Math.max(1,surface.value.clientHeight)
      if(w!==lastW||h!==lastH){
        const scale=Math.min(1,1120/Math.max(w,h))
        renderer.setSize(Math.max(1,Math.floor(w*scale)),Math.max(1,Math.floor(h*scale)),false)
        camera.aspect=w/h
        camera.updateProjectionMatrix()
        lastW=w;lastH=h
      }
      const orbit=p*p*(3-2*p)
      const framingScale={serum:1,jar:1.12,tube:1,perfume:1,cup:1.28,vase:1,watch:1,ring:1.72,microphone:1.04}[kind.value]||1
      camera.position.set(.12+.48*orbit,.34+.18*Math.sin(p*Math.PI),Math.max(5.35,6.55-1.05*orbit,5.25/camera.aspect))
      camera.lookAt(0,-.04+.08*p,0)
      object.rotation.y=-.38+1.42*orbit
      object.rotation.x=.025+.09*Math.sin(p*Math.PI)
      object.rotation.z=-.035-.075*p
      object.scale.setScalar(framingScale*(.94+.12*orbit))
      key.position.set(-3.8+7.4*p,4.8,4.5)
      key.intensity=3.35+1.15*Math.sin(p*Math.PI)
      rimLight.position.x=4-6*p
      rimLight.intensity=3.05+.85*Math.sin(p*Math.PI)
      scene.environmentIntensity=1.08+.24*Math.sin(p*Math.PI)
      cloth.position.z=-1.62-.88*p
      cloth.position.y=-.98-.12*p
      cloth.rotation.y=-.045+.13*p
      renderer.render(scene,camera)
      root.value.dataset.tnObjectPose=p.toFixed(3)
    }
    const lost=event=>{event.preventDefault();failed=true;dispose()}
    renderer.domElement.addEventListener('webglcontextlost',lost)
    runtime={
      draw,
      dispose(){
        renderer.domElement.removeEventListener('webglcontextlost',lost)
        resources.forEach(item=>item.dispose?.())
        pmrem.dispose()
        renderer.dispose()
        renderer.domElement.remove()
      }
    }
    draw(progress())
    ready.value=true
  }catch{
    failed=true
    if(runtime)dispose()
    else{
      resources.forEach(item=>item.dispose?.())
      pmrem?.dispose()
      renderer?.dispose()
      renderer?.domElement?.remove()
    }
  }finally{loading=false}
}
function refresh(){
  if(!visible||media.matches||document.hidden){
    cancel()
    if(media.matches)dispose()
    return
  }
  if(runtime)schedule()
  else init()
}
onMounted(()=>{
  media=matchMedia('(max-width:760px), (prefers-reduced-motion: reduce)')
  observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;refresh()},{rootMargin:'100px'})
  observer.observe(root.value)
  resize=new ResizeObserver(refresh)
  resize.observe(root.value)
  window.addEventListener('scroll',schedule,{passive:true})
  media.addEventListener('change',refresh)
  document.addEventListener('visibilitychange',refresh)
})
onBeforeUnmount(()=>{
  closed=true
  observer?.disconnect();resize?.disconnect()
  window.removeEventListener('scroll',schedule)
  media?.removeEventListener('change',refresh)
  document.removeEventListener('visibilitychange',refresh)
  dispose()
})
</script>
<template>
  <figure ref="root" class="tn-hero-object" data-tn-hero-object :data-tn-object-preset="kind" :data-tn-object-state="ready?'ready':'fallback'" :aria-label="label">
    <div class="tn-hero-object-glow" :style="{'--object-accent':accentColor}"></div>
    <div v-show="!ready" class="tn-product-fallback" :class="'is-'+kind" :style="{'--object-tone':toneColor,'--object-accent':accentColor}" role="img" :aria-label="label">
      <div class="tn-product-cap"></div>
      <div class="tn-product-body"><span>{{ brand.slice(0,22) || 'ATELIER' }}</span><small>{{ label.slice(0,34) }}</small></div>
    </div>
    <div ref="surface" class="tn-product-canvas" :class="{'is-ready':ready}" aria-hidden="true"></div>
  </figure>
</template>
<style scoped>
.tn-hero-object{position:relative;isolation:isolate;display:grid;place-items:center;width:100%;min-width:0;min-height:clamp(380px,68svh,760px);margin:0;overflow:clip}
.tn-hero-object-glow{position:absolute;inset:4%;background:radial-gradient(ellipse at 50% 52%,color-mix(in srgb,var(--object-accent) 32%,transparent),transparent 68%);filter:blur(12px);pointer-events:none}
.tn-product-fallback{position:relative;width:clamp(132px,38%,250px);aspect-ratio:1/2.12;filter:drop-shadow(18px 26px 26px #0007);transform:translateY(2%)}
.tn-product-body{position:absolute;inset:24% 0 0;border:1px solid #ffffff55;border-radius:14% 14% 12% 12%;background:linear-gradient(100deg,#211b17,var(--object-tone) 18%,#fff2d5 34%,var(--object-tone) 54%,#30251d 96%);display:grid;align-content:center;text-align:center;padding:12%;color:#34291e;box-shadow:inset 9px 0 15px #ffffff30,inset -10px 0 18px #0003}
.tn-product-body span,.tn-product-body small{display:block;background:linear-gradient(110deg,#f8f1e5,#e8dcc6);padding:8% 2%;overflow-wrap:anywhere;font-family:Georgia,serif}
.tn-product-body span{font-size:clamp(10px,1.1vw,15px);letter-spacing:.12em}
.tn-product-body small{font-size:clamp(8px,1vw,12px);padding-top:0}
.tn-product-cap{position:absolute;left:30%;width:40%;top:5%;height:25%;border-radius:14% 14% 4% 4%;background:linear-gradient(90deg,#574633,var(--object-accent),#f0dcb6,#8c7151);box-shadow:inset 5px 0 8px #fff5,inset -5px 0 8px #0004}
.tn-product-cap:before{content:"";position:absolute;inset:-18% 15% 42%;background:linear-gradient(90deg,#171615,#55504b,#171615);border-radius:30%}
.is-jar{width:clamp(155px,42%,290px);aspect-ratio:1.1}.is-jar .tn-product-body{inset:28% 0 0;border-radius:10% 10% 18% 18%}.is-jar .tn-product-cap{left:0;width:100%;top:12%;height:25%;border-radius:9%}.is-jar .tn-product-cap:before{display:none}
.is-tube .tn-product-body{inset:0 0 15%;border-radius:22% 22% 9% 9%;clip-path:polygon(4% 0,96% 0,80% 100%,20% 100%)}.is-tube .tn-product-cap{top:auto;bottom:0;left:25%;width:50%;height:20%}.is-tube .tn-product-cap:before{display:none}
.is-perfume .tn-product-body{border-radius:18% 18% 14% 14%}.is-perfume .tn-product-cap:before{inset:-18% -15% 25%;border-radius:12%}
.is-cup{width:clamp(170px,42%,280px);aspect-ratio:1.35}.is-cup .tn-product-body{inset:22% 18% 10%;border-radius:12% 12% 26% 26%}.is-cup .tn-product-cap{left:25%;width:50%;top:12%;height:10%;border-radius:50%}.is-cup .tn-product-cap:before{display:none}.is-cup .tn-product-body:after{content:"";position:absolute;right:-34%;top:22%;width:38%;height:48%;border:12px solid var(--object-tone);border-left:0;border-radius:0 50% 50% 0}
.is-vase{width:clamp(150px,36%,250px);aspect-ratio:.72/1.65}.is-vase .tn-product-body{inset:10% 18% 4%;border-radius:42% 42% 28% 28% / 18% 18% 42% 42%}.is-vase .tn-product-cap{left:35%;width:30%;top:0;height:18%}.is-vase .tn-product-cap:before{display:none}
.is-watch{width:clamp(145px,34%,230px);aspect-ratio:.8/1.65}.is-watch .tn-product-body{inset:24% 5%;border-radius:50%;aspect-ratio:1;background:radial-gradient(circle at 35% 30%,#596c78,#17242d 65%);border:10px solid var(--object-accent);padding:0}.is-watch .tn-product-body span,.is-watch .tn-product-body small{display:none}.is-watch .tn-product-cap{left:35%;width:30%;top:0;height:36%;border-radius:12%}.is-watch .tn-product-cap:before{display:none}
.is-ring{width:clamp(170px,38%,250px);aspect-ratio:1.2}.is-ring .tn-product-cap{left:38%;width:24%;top:4%;height:25%;border-radius:35%;background:linear-gradient(90deg,#8b6b3d,#f4dfad,#9e7845)}.is-ring .tn-product-cap:before{display:none}.is-ring .tn-product-body{inset:38% 13% 5%;border:20px solid var(--object-accent);border-radius:50%;background:transparent;box-shadow:inset 0 0 10px #fff7,0 0 14px #0005;padding:0}.is-ring .tn-product-body span,.is-ring .tn-product-body small{display:none}
.is-microphone{width:clamp(135px,32%,220px);aspect-ratio:.72/1.8}.is-microphone .tn-product-body{inset:26% 27% 12%;border-radius:20% 20% 12% 12%;background:linear-gradient(90deg,#17191b,#6b6c6d,#242527)}.is-microphone .tn-product-cap{left:22%;width:56%;top:5%;height:32%;border-radius:48% 48% 25% 25%;background:repeating-linear-gradient(90deg,#252628 0 3px,#737477 4px 5px)}.is-microphone .tn-product-cap:before{display:none}
.tn-product-canvas{position:absolute;inset:0;opacity:0;pointer-events:none}.tn-product-canvas.is-ready{opacity:1}.tn-product-canvas :deep(canvas){display:block;width:100%;height:100%}
@media(max-width:760px){.tn-hero-object{min-height:300px;max-height:440px}.tn-hero-object-glow{inset:2%;filter:blur(8px)}}
</style>
