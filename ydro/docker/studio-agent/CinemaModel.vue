<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { MOTION_PRESETS, LIGHTING_PRESETS, presetShots, heroMotionShots, cameraTrackProgress, heroFilmProgress, pinnedFilmFrame, centeredViewOffset, smoothScrollProgress, scrollFrameElapsed, modelPixelRatio, needsTransformPin } from '../cinematic-motion.js'

const props = defineProps({
  modelPath: { type: String, required: true },
  label: { type: String, required: true },
  shots: { type: Array, default: () => [] },
  exposure: { type: Number, default: 1.1 },
  accent: { type: String, default: '#d6b48a' },
  ground: { type: Boolean, default: true },
  motionPreset: { type: String, default: 'custom' },
  openingYaw: { type: Number, default: 50 },
  motionStrength: { type: Number, default: 1 },
  lighting: { type: String, default: 'studio' },
  modelRole: { type: String, default: 'primary' }
})
const motionName = MOTION_PRESETS.includes(props.motionPreset) ? props.motionPreset : 'custom'
const role = props.modelRole === 'accent' ? 'accent' : 'primary'
const lightingName = Object.hasOwn(LIGHTING_PRESETS,props.lighting) ? props.lighting : 'studio'
const lighting = LIGHTING_PRESETS[lightingName]
const host = ref(null)
const state = ref('loading')
const defaults = [
  { at: 0, yaw: 50, pitch: 12, distance: 1.0, target: [0,0,0] },
  { at: .45, yaw: -38, pitch: 8, distance: .92, target: [0,.05,0] },
  { at: .76, yaw: -95, pitch: 18, distance: .82, target: [0,.08,0] },
  { at: 1, yaw: -142, pitch: 14, distance: 1.04, target: [0,0,0] }
]
const finite = (n, fallback) => typeof n === 'number' && Number.isFinite(n) ? n : fallback
const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi,n))
function normalizedShots() {
  const preset = presetShots(motionName,props.openingYaw,props.motionStrength)
  const source = props.shots.length >= 2 && props.shots.length <= 8 ? props.shots : (preset.length ? preset : defaults)
  const list=source.map((s,i)=>({
    at:clamp(finite(s?.at,i/(source.length-1)),0,1),
    yaw:clamp(finite(s?.yaw,38),-720,720),
    pitch:clamp(finite(s?.pitch,12),-50,65),
    distance:clamp(finite(s?.distance,1),.72,1.35),
    target:[0,1,2].map(j=>clamp(finite(s?.target?.[j],0),-.45,.45)),
    modelYaw:clamp(finite(s?.modelYaw,0),-720,720),
    lift:clamp(finite(s?.lift,0),-.12,.12),
    light:clamp(finite(s?.light,0),-90,90)
  })).sort((a,b)=>a.at-b.at)
  if(list[0].at>0) list.unshift({...list[0],at:0})
  if(list.at(-1).at<1) list.push({...list.at(-1),at:1})
  return list
}
let renderer, scene, camera, model, env, pmrem, observer, intersection, raf=0, disposed=false
let visible=true, motionQuery, current=0, radius=1, frameCount=0, shots, primaryHero=false
let corners=[], bounds, groundPlane, keyLight, modelPivot, filmRoot, pinnedFrame, filmTurn=360
let filmScreen, filmActions, smoothFilm=false, transformPin=false, modelSize
let renderWidth=0,renderHeight=0,renderRatio=0,lastRendered=null,lastFrameTime=null,resizeCount=0
let chapter, header
const filmValues=new Map()
function filmStyle(key,value) {
  if(filmValues.get(key)===value)return
  filmRoot.style.setProperty(key,value)
  filmValues.set(key,value)
}
function filmData(key,value) {
  if(filmRoot.dataset[key]!==value)filmRoot.dataset[key]=value
}
function updatePinMode() {
  if(!smoothFilm)return
  const modes=[]
  for(let n=filmRoot.parentElement;n&&n!==document.body&&n!==document.documentElement;n=n.parentElement){
    modes.push(getComputedStyle(n).overflowY)
  }
  transformPin=needsTransformPin(modes)
  filmData('tnFilmPin',transformPin?'transform':'native')
}
const yAxis=new THREE.Vector3(0,1,0)
function disposeModel(root) {
  const geometries=new Set(), materials=new Set(), textures=new Set()
  root?.traverse(o=>{
    if(o.geometry) geometries.add(o.geometry)
    for(const m of Array.isArray(o.material)?o.material:[o.material]){
      if(!m) continue
      materials.add(m)
      for(const v of Object.values(m)) if(v?.isTexture) textures.add(v)
    }
  })
  geometries.forEach(g=>g.dispose())
  textures.forEach(t=>t.dispose())
  materials.forEach(m=>m.dispose())
}
function cleanup() {
  cancelAnimationFrame(raf); raf=0
  observer?.disconnect(); intersection?.disconnect()
  window.removeEventListener('scroll',schedule)
  window.removeEventListener('resize',resize)
  motionQuery?.removeEventListener('change',schedule)
  disposeModel(model); model=null
  if(groundPlane){groundPlane.geometry.dispose();groundPlane.material.dispose();groundPlane=null}
  keyLight?.shadow?.dispose()
  env?.dispose(); pmrem?.dispose()
  if(renderer){
    renderer.domElement.removeEventListener('webglcontextlost',lost)
    renderer.dispose()
    renderer.domElement.remove()
    renderer=null
  }
}
let loadStage='initializing'
function fail(reason=loadStage) {
  if(host.value) host.value.dataset.tnModelFailure=reason
  if(filmRoot){filmRoot.dataset.tnFilmFallback='true';filmRoot.dataset.tnFilmPhase='reveal';filmRoot.style.setProperty('--tn-film-reveal','1');for(const key of ['title','description','actions'])filmRoot.style.setProperty('--tn-film-'+key,'1');const actions=filmRoot.querySelector('.hero-actions');if(actions)actions.inert=false}
  state.value='fallback'; cleanup()
}
function lost(e) { e.preventDefault(); fail('webgl-context-lost') }
function resize() {
  if(!renderer || !host.value) return
  updatePinMode()
  const w=Math.max(1,host.value.clientWidth), h=Math.max(1,host.value.clientHeight)
  const ratio=modelPixelRatio(w,h,window.devicePixelRatio||1,innerWidth<=760)
  if(w!==renderWidth||h!==renderHeight||ratio!==renderRatio){
    renderWidth=w;renderHeight=h;renderRatio=ratio
    // setDrawingBufferSize changes the GPU buffer once, without changing CSS.
    renderer.setDrawingBufferSize(w,h,ratio)
    camera.aspect=w/h; camera.updateProjectionMatrix()
    lastRendered=null
    host.value.dataset.tnModelBufferResizes=String(++resizeCount)
    host.value.dataset.tnModelPixelRatio=ratio.toFixed(3)
  }
  schedule()
}
function schedule() { if(!disposed && renderer && !raf) raf=requestAnimationFrame(draw) }
function draw(timestamp) {
  raf=0
  try { renderFrame(timestamp) } catch { fail('render-frame') }
}
function renderFrame(timestamp) {
  if(!renderer || !model || !host.value) return
  if(!visible&&!filmRoot){lastFrameTime=null;return}
  // Read layout once, before writes. The film height is CSS-owned (stable svh).
  const rect=chapter.getBoundingClientRect()
  const fullFilm=filmRoot?.dataset.tnFilmVersion==='2'
  let targetProgress=0
  let staticFilm=motionQuery.matches
  let inView=visible
  if(fullFilm){
    const viewport=Math.max(1,smoothFilm?renderHeight:innerHeight)
    pinnedFrame=pinnedFilmFrame(rect.top,rect.height,viewport,filmTurn,filmRoot.dataset.tnFilmPace==='compact')
    targetProgress=staticFilm?0:pinnedFrame.motion
    // Native sticky owns the pin; only an incompatible ancestor uses a compositor transform.
    if(!smoothFilm||transformPin)filmStyle('--tn-film-offset',(staticFilm?0:pinnedFrame.offset)+'px')
    for(const key of ['title','description','actions']){
      const value=(staticFilm?1:pinnedFrame[key]).toFixed(4)
      filmStyle('--tn-film-'+key,value)
      filmData('tnFilm'+key[0].toUpperCase()+key.slice(1),value)
    }
    if(filmActions){
      const inert=!staticFilm&&pinnedFrame.actions<.05
      if(filmActions.inert!==inert)filmActions.inert=inert
    }
    filmData('tnFilmReveal',String(staticFilm?1:pinnedFrame.title))
    filmData('tnFilmPhase',staticFilm||pinnedFrame.title>.01?'reveal':'opening')
    inView=rect.bottom>0&&rect.top<innerHeight
  } else if(filmRoot){
    const film=heroFilmProgress(rect.top,rect.height,innerHeight)
    staticFilm=staticFilm||matchMedia('(max-height: 600px)').matches
    targetProgress=staticFilm?0:film.motion
    const reveal=staticFilm?1:film.reveal
    filmStyle('--tn-film-reveal',reveal.toFixed(4))
    filmData('tnFilmReveal',reveal.toFixed(4))
    filmData('tnFilmPhase',reveal<.05?'opening':'reveal')
    inView=rect.bottom>0&&rect.top<innerHeight
  } else {
    const headerPosition=primaryHero&&header?getComputedStyle(header).position:''
    const inset=['sticky','fixed'].includes(headerPosition)?clamp(header.getBoundingClientRect().bottom,0,innerHeight*.2):0
    targetProgress=staticFilm?0:primaryHero?cameraTrackProgress(rect.top,rect.height,innerHeight,chapter!==host.value,inset):clamp(-rect.top/Math.max(innerHeight*.4,rect.height-innerHeight*.35),0,1)
  }
  if(!inView){current=targetProgress;lastFrameTime=null;return}
  const elapsed=scrollFrameElapsed(lastFrameTime,timestamp)
  current=staticFilm||lastRendered===null?targetProgress:smoothScrollProgress(current,targetProgress,elapsed)
  const settling=current!==targetProgress
  // Reset the timestamp only when actually idle, never during a slow active frame.
  lastFrameTime=settling?timestamp:null
  host.value.dataset.tnModelTargetProgress=targetProgress.toFixed(4)
  host.value.dataset.tnModelFrameElapsed=elapsed.toFixed(1)
  if(settling)schedule()
  if(lastRendered===current)return
  lastRendered=current
  let b=shots.findIndex(s=>s.at>=current)
  if(b<1)b=1
  const from=shots[b-1],to=shots[b]
  const t=clamp((current-from.at)/Math.max(.00001,to.at-from.at),0,1)
  const blend=(a,b)=>THREE.MathUtils.lerp(a,b,t*t*(3-2*t))
  let yaw=THREE.MathUtils.degToRad(blend(from.yaw,to.yaw))
  if(fullFilm) yaw=THREE.MathUtils.degToRad(shots[0].yaw)
  const modelYaw=THREE.MathUtils.degToRad(fullFilm?shots[0].modelYaw+filmTurn*current:blend(from.modelYaw,to.modelYaw))
  const lift=fullFilm||props.ground?0:blend(from.lift,to.lift)
  const lightAngle=THREE.MathUtils.degToRad(blend(from.light,to.light))
  modelPivot.rotation.y=modelYaw
  modelPivot.position.y=lift
  // Fit the transformed bounds, not the original unrotated box.
  const posedCorners=corners.map(c=>c.clone().applyAxisAngle(yAxis,modelYaw).addScaledVector(yAxis,lift))
  keyLight.position.set(4*Math.cos(lightAngle)+5*Math.sin(lightAngle),6,5*Math.cos(lightAngle)-4*Math.sin(lightAngle))
  const pitch=THREE.MathUtils.degToRad(blend(from.pitch,to.pitch))
  // Avoid an end-on opening shot of elongated horizontal objects.
  const size=modelSize
  const opening=1-THREE.MathUtils.smoothstep(current,0,.25)
  if(!fullFilm && motionName==='custom' && size.z>size.x*1.5 && size.z>size.y*1.4 && Math.abs(Math.sin(yaw))<.5){
    yaw+=(Math.sin(yaw)<0?-1:1)*.65*opening
  } else if(!fullFilm && motionName==='custom' && size.x>size.z*1.5 && size.x>size.y*1.4 && Math.abs(Math.cos(yaw))<.5){
    yaw+=.65*opening
  }
  const direction=new THREE.Vector3(Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch))
  const centeredFilm=fullFilm&&filmRoot.hasAttribute('data-tn-film-background')
  const target=centeredFilm?new THREE.Vector3():new THREE.Vector3(...from.target.map((v,i)=>blend(v,to.target[i])*radius*(1-opening)))
  // Shift only the camera composition, never the full viewport canvas.
  const captionShift=fullFilm&&!centeredFilm&&!motionQuery.matches ? .09*(pinnedFrame?.title||0) : 0
  if(fullFilm){
    const w=renderWidth,h=renderHeight
    if(captionShift>0)camera.setViewOffset(w,h,0,-h*captionShift,w,h)
    else if(camera.view?.enabled)camera.clearViewOffset()
  }
  const halfV=THREE.MathUtils.degToRad(camera.fov/2)
  const tanV=Math.tan(halfV),tanH=tanV*camera.aspect
  const right=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),direction).normalize()
  const up=new THREE.Vector3().crossVectors(direction,right).normalize()
  // Solve perspective fit for all eight corners, taking depth into account.
  // A factor of 1 fits the box inside 84% of the limiting screen dimension.
  let fit=.15
  for(const corner of posedCorners){
    const rel=corner.clone().sub(target)
    const depth=rel.dot(direction)
    fit=Math.max(fit,depth+Math.abs(rel.dot(right))/(tanH*.84),depth+Math.abs(rel.dot(up))/(tanV*(.84-2*captionShift)),depth+.15)
  }
  const zoom=centeredFilm?1:blend(from.distance,to.distance)
  const distance=fit*(primaryHero?clamp(zoom,1,1.08):(opening>0?THREE.MathUtils.lerp(zoom,clamp(zoom,.98,1.08),opening):zoom))
  const far=Math.max(100,distance+radius*8)
  if(camera.far!==far){camera.far=far;camera.updateProjectionMatrix()}
  camera.position.copy(target).addScaledVector(direction,distance)
  camera.lookAt(target)
  camera.updateMatrixWorld()
  if(centeredFilm){
    // Center the projected object, not just its canvas or its world-space pivot.
    // Recompute for each angle to handle asymmetric geometry and perspective.
    const initial=posedCorners.map(v=>v.clone().project(camera))
    const w=renderWidth,h=renderHeight
    const [x,y]=centeredViewOffset(initial.map(p=>p.x),initial.map(p=>p.y),w,h)
    camera.setViewOffset(w,h,x,y,w,h)
  }
  if(props.ground)renderer.shadowMap.needsUpdate=true
  renderer.render(scene,camera)
  const projected=posedCorners.map(v=>v.clone().project(camera))
  const xs=projected.map(v=>v.x),ys=projected.map(v=>v.y)
  const extentX=(Math.max(...xs)-Math.min(...xs))/2
  const extentY=(Math.max(...ys)-Math.min(...ys))/2
  // Projected AABB is a conservative diagnostic, not a pixel/silhouette mask.
  host.value.dataset.tnModelScreenBounds=[(Math.min(...xs)+1)/2,(1-Math.max(...ys))/2,(Math.max(...xs)+1)/2,(1-Math.min(...ys))/2].map(v=>v.toFixed(4)).join(',')
  host.value.dataset.tnModelCoverage=Math.max(extentX,extentY).toFixed(4)
  host.value.dataset.tnModelWidth=extentX.toFixed(4)
  host.value.dataset.tnModelHeight=extentY.toFixed(4)
  host.value.dataset.tnModelClipped=String(projected.some(v=>Math.abs(v.x)>1.02||Math.abs(v.y)>1.02||Math.abs(v.z)>1))
  host.value.dataset.tnCameraProgress=current.toFixed(4)
  host.value.dataset.tnCameraYaw=yaw.toFixed(4)
  host.value.dataset.tnCameraPose=[...camera.position.toArray(),...target.toArray()].map(x=>x.toFixed(4)).join(',')
  host.value.dataset.tnModelMotionPose=[...camera.position.toArray(),...target.toArray(),modelYaw,lift,...keyLight.position.toArray()].map(x=>x.toFixed(4)).join(',')
  host.value.dataset.tnObjectYaw=modelYaw.toFixed(4)
  host.value.dataset.tnRelativeYaw=THREE.MathUtils.radToDeg(yaw-modelYaw).toFixed(2)
  host.value.dataset.tnFrames=String(++frameCount)
}
onMounted(async()=>{
  try{
    if(!/^tn-models\/[A-Za-z0-9_-]+\/model\.gltf$/.test(props.modelPath)) throw new Error('Invalid local path')
    motionQuery=matchMedia('(prefers-reduced-motion: reduce)')
    primaryHero=role==='primary'&&Boolean(host.value.closest('[data-tn-section="home"]'))
    shots=normalizedShots()
    filmRoot=primaryHero?host.value.closest('[data-tn-hero-film]'):null
    chapter=filmRoot||host.value.closest('[data-tn-camera-track]')||host.value
    header=document.querySelector('[data-tn-header]')
    if(filmRoot){
      filmScreen=filmRoot.querySelector('.tn-film-screen')
      filmActions=filmRoot.querySelector('.hero-actions')
      smoothFilm=Boolean(filmScreen&&filmRoot.dataset.tnFilmEngine==='smooth')
      filmTurn=filmRoot.dataset.tnFilmTurn==='180'?180:360
      const start=shots[0]
      shots=presetShots('hero_turn',finite(start?.yaw,props.openingYaw),1).map(s=>({...s,modelYaw:s.modelYaw+finite(start?.modelYaw,0)}))
    } else if(primaryHero) shots=heroMotionShots(shots,props.openingYaw)
    loadStage='webgl-renderer'
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'})
    renderer.outputColorSpace=THREE.SRGBColorSpace
    renderer.toneMapping=THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure=clamp(finite(props.exposure,1.1),.5,2)
    renderer.setClearColor(0x000000,0)
    renderer.shadowMap.enabled=props.ground
    renderer.shadowMap.type=THREE.PCFSoftShadowMap
    renderer.shadowMap.autoUpdate=false
    renderer.domElement.style.cssText=filmRoot?.hasAttribute('data-tn-film-background')?'position:absolute;inset:0;display:block;width:100%;height:100%;margin:0;padding:0;pointer-events:none;transform:none;':'display:block;width:100%;height:100%;pointer-events:none;'
    renderer.domElement.setAttribute('aria-hidden','true')
    renderer.domElement.addEventListener('webglcontextlost',lost)
    host.value.append(renderer.domElement)
    scene=new THREE.Scene()
    camera=new THREE.PerspectiveCamera(38,1,.01,100)
    loadStage='studio-environment'
    pmrem=new THREE.PMREMGenerator(renderer)
    const room=new RoomEnvironment()
    try { env=pmrem.fromScene(room,.04); scene.environment=env.texture }
    finally { room.dispose() }
    scene.environmentIntensity=lighting.environment
    const key=new THREE.DirectionalLight(0xfff4e6,lighting.key)
    keyLight=key
    key.position.set(4,6,5); scene.add(key)
    if(props.ground){
      key.castShadow=true
      const shadowSize=innerWidth<=760?512:1024
      key.shadow.mapSize.set(shadowSize,shadowSize)
      Object.assign(key.shadow.camera,{left:-2.4,right:2.4,top:2.4,bottom:-2.4,near:.1,far:20})
      key.shadow.camera.updateProjectionMatrix()
      key.shadow.normalBias=.025
    }
    const rim=new THREE.DirectionalLight(props.accent,lighting.rim)
    rim.position.set(-4,2,-5); scene.add(rim)
    const fill=new THREE.HemisphereLight(0xc3d8ff,0x28221d,lighting.fill)
    scene.add(fill)
    resize()
    loadStage='gltf-load'
    const loader=new GLTFLoader()
    const gltf=await loader.loadAsync(import.meta.env.BASE_URL+props.modelPath)
    if(disposed || !renderer){disposeModel(gltf.scene);return}
    loadStage='model-bounds'
    model=gltf.scene
    const box=new THREE.Box3().setFromObject(model)
    if(box.isEmpty())throw new Error('Empty model')
    const sphere=box.getBoundingSphere(new THREE.Sphere())
    if(!Number.isFinite(sphere.radius)||sphere.radius<=0)throw new Error('Invalid model bounds')
    // Normalize without changing the source geometry or materials.
    const pivot=new THREE.Group()
    modelPivot=pivot
    model.position.sub(sphere.center)
    pivot.add(model); pivot.scale.setScalar(1/sphere.radius); scene.add(pivot)
    radius=1
    scene.updateMatrixWorld(true)
    bounds=new THREE.Box3().setFromObject(pivot)
    modelSize=bounds.getSize(new THREE.Vector3())
    corners=[]
    for(const x of [bounds.min.x,bounds.max.x])
      for(const y of [bounds.min.y,bounds.max.y])
        for(const z of [bounds.min.z,bounds.max.z]) corners.push(new THREE.Vector3(x,y,z))
    if(props.ground){
      model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true}})
      groundPlane=new THREE.Mesh(new THREE.PlaneGeometry(8,8),new THREE.ShadowMaterial({opacity:.35}))
      groundPlane.rotation.x=-Math.PI/2
      groundPlane.position.y=bounds.min.y-.012
      groundPlane.receiveShadow=true
      scene.add(groundPlane)
    }
    loadStage='ready'
    state.value='ready'
    observer=new ResizeObserver(resize); observer.observe(host.value)
    intersection=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;schedule()},{rootMargin:'120px'})
    intersection.observe(host.value)
    window.addEventListener('scroll',schedule,{passive:true})
    window.addEventListener('resize',resize,{passive:true})
    motionQuery.addEventListener('change',schedule)
    schedule()
  } catch { if(!disposed)fail() }
})
onBeforeUnmount(()=>{disposed=true;cleanup()})
</script>
<template>
  <div ref="host" class="tn-cinema-model" :class="{ 'tn-cinema-accent': role==='accent' }" :data-tn-model="modelPath" :data-tn-model-role="role" :data-tn-motion-preset="motionName" :data-tn-lighting="lightingName" :data-tn-model-state="state" role="img" :aria-label="label">
    <div v-if="state !== 'ready'" class="tn-cinema-fallback">
      <slot name="fallback"><span>{{ label }}</span></slot>
    </div>
  </div>
</template>
<style scoped>
.tn-cinema-model{position:relative;display:block;width:100%;height:100%;min-height:240px;overflow:hidden;isolation:isolate}
.tn-cinema-model.tn-cinema-accent{min-height:100px}
.tn-cinema-fallback{position:absolute;inset:0;display:grid;place-items:center;text-align:center}
.tn-cinema-fallback :deep(img){width:100%;height:100%;object-fit:cover}
</style>
