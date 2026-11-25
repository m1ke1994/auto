<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'

const props = defineProps({
  modelPath: { type: String, required: true },
  label: { type: String, required: true },
  shots: { type: Array, default: () => [] },
  exposure: { type: Number, default: 1.1 },
  accent: { type: String, default: '#d6b48a' },
  ground: { type: Boolean, default: true }
})
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
  const source = props.shots.length >= 2 && props.shots.length <= 8 ? props.shots : defaults
  const list=source.map((s,i)=>({
    at:clamp(finite(s?.at,i/(source.length-1)),0,1),
    yaw:clamp(finite(s?.yaw,38),-360,360),
    pitch:clamp(finite(s?.pitch,12),-50,65),
    distance:clamp(finite(s?.distance,1),.72,1.35),
    target:[0,1,2].map(j=>clamp(finite(s?.target?.[j],0),-.45,.45))
  })).sort((a,b)=>a.at-b.at)
  if(list[0].at>0) list.unshift({...list[0],at:0})
  if(list.at(-1).at<1) list.push({...list.at(-1),at:1})
  return list
}
let renderer, scene, camera, model, env, pmrem, observer, intersection, raf=0, disposed=false
let visible=true, motionQuery, current=0, radius=1, frameCount=0, shots
let corners=[], bounds, groundPlane, keyLight
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
  state.value='fallback'; cleanup()
}
function lost(e) { e.preventDefault(); fail('webgl-context-lost') }
function resize() {
  if(!renderer || !host.value) return
  const w=Math.max(1,host.value.clientWidth), h=Math.max(1,host.value.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,w<640?1.25:1.75))
  renderer.setSize(w,h,false)
  camera.aspect=w/h; camera.updateProjectionMatrix()
  schedule()
}
function schedule() { if(!disposed && renderer && !raf) raf=requestAnimationFrame(draw) }
function draw() {
  raf=0
  try { renderFrame() } catch { fail('render-frame') }
}
function renderFrame() {
  if(!renderer || !model || !host.value || !visible) return
  // Use the surrounding narrative chapter, not a nested scroll container.
  const chapter=host.value.closest('[data-tn-camera-track]') || host.value
  const rect=chapter.getBoundingClientRect()
  const progress=clamp(-rect.top/Math.max(innerHeight*.4,rect.height-innerHeight*.35),0,1)
  current=motionQuery.matches?0:progress
  let b=shots.findIndex(s=>s.at>=current)
  if(b<1)b=1
  const from=shots[b-1],to=shots[b]
  const t=clamp((current-from.at)/Math.max(.00001,to.at-from.at),0,1)
  const blend=(a,b)=>THREE.MathUtils.lerp(a,b,t*t*(3-2*t))
  let yaw=THREE.MathUtils.degToRad(blend(from.yaw,to.yaw))
  const pitch=THREE.MathUtils.degToRad(blend(from.pitch,to.pitch))
  // Avoid an end-on opening shot of elongated horizontal objects.
  const size=bounds.getSize(new THREE.Vector3())
  const opening=1-THREE.MathUtils.smoothstep(current,0,.25)
  if(size.z>size.x*1.5 && size.z>size.y*1.4 && Math.abs(Math.sin(yaw))<.5){
    yaw+=(Math.sin(yaw)<0?-1:1)*.65*opening
  } else if(size.x>size.z*1.5 && size.x>size.y*1.4 && Math.abs(Math.cos(yaw))<.5){
    yaw+=.65*opening
  }
  const direction=new THREE.Vector3(Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch))
  const target=new THREE.Vector3(...from.target.map((v,i)=>blend(v,to.target[i])*radius*(1-opening)))
  const halfV=THREE.MathUtils.degToRad(camera.fov/2)
  const tanV=Math.tan(halfV),tanH=tanV*camera.aspect
  const right=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),direction).normalize()
  const up=new THREE.Vector3().crossVectors(direction,right).normalize()
  // Solve perspective fit for all eight corners, taking depth into account.
  // A factor of 1 fits the box inside 84% of the limiting screen dimension.
  let fit=.15
  for(const corner of corners){
    const rel=corner.clone().sub(target)
    const depth=rel.dot(direction)
    fit=Math.max(fit,depth+Math.abs(rel.dot(right))/(tanH*.84),depth+Math.abs(rel.dot(up))/(tanV*.84),depth+.15)
  }
  const zoom=blend(from.distance,to.distance)
  const distance=fit*(opening>0?THREE.MathUtils.lerp(zoom,clamp(zoom,.98,1.08),opening):zoom)
  camera.position.copy(target).addScaledVector(direction,distance)
  camera.lookAt(target)
  camera.updateMatrixWorld()
  renderer.render(scene,camera)
  const projected=corners.map(v=>v.clone().project(camera))
  const xs=projected.map(v=>v.x),ys=projected.map(v=>v.y)
  const extentX=(Math.max(...xs)-Math.min(...xs))/2
  const extentY=(Math.max(...ys)-Math.min(...ys))/2
  host.value.dataset.tnModelCoverage=Math.max(extentX,extentY).toFixed(4)
  host.value.dataset.tnModelWidth=extentX.toFixed(4)
  host.value.dataset.tnModelHeight=extentY.toFixed(4)
  host.value.dataset.tnModelClipped=String(projected.some(v=>Math.abs(v.x)>1.02||Math.abs(v.y)>1.02||Math.abs(v.z)>1))
  host.value.dataset.tnCameraProgress=current.toFixed(4)
  host.value.dataset.tnCameraYaw=yaw.toFixed(4)
  host.value.dataset.tnCameraPose=[...camera.position.toArray(),...target.toArray()].map(x=>x.toFixed(4)).join(',')
  host.value.dataset.tnFrames=String(++frameCount)
}
onMounted(async()=>{
  try{
    if(!/^tn-models\/[A-Za-z0-9_-]+\/model\.gltf$/.test(props.modelPath)) throw new Error('Invalid local path')
    motionQuery=matchMedia('(prefers-reduced-motion: reduce)')
    shots=normalizedShots()
    loadStage='webgl-renderer'
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'})
    renderer.outputColorSpace=THREE.SRGBColorSpace
    renderer.toneMapping=THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure=clamp(finite(props.exposure,1.1),.5,2)
    renderer.setClearColor(0x000000,0)
    renderer.shadowMap.enabled=props.ground
    renderer.shadowMap.type=THREE.PCFSoftShadowMap
    renderer.domElement.style.cssText='display:block;width:100%;height:100%;pointer-events:none;'
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
    scene.environmentIntensity=1.0
    const key=new THREE.DirectionalLight(0xfff4e6,3)
    keyLight=key
    key.position.set(4,6,5); scene.add(key)
    if(props.ground){
      key.castShadow=true
      key.shadow.mapSize.set(1024,1024)
      Object.assign(key.shadow.camera,{left:-2.4,right:2.4,top:2.4,bottom:-2.4,near:.1,far:20})
      key.shadow.camera.updateProjectionMatrix()
      key.shadow.normalBias=.025
    }
    const rim=new THREE.DirectionalLight(props.accent,2.8)
    rim.position.set(-4,2,-5); scene.add(rim)
    const fill=new THREE.HemisphereLight(0xc3d8ff,0x28221d,1)
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
    model.position.sub(sphere.center)
    pivot.add(model); pivot.scale.setScalar(1/sphere.radius); scene.add(pivot)
    radius=1
    scene.updateMatrixWorld(true)
    bounds=new THREE.Box3().setFromObject(pivot)
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
  <div ref="host" class="tn-cinema-model" :data-tn-model="modelPath" :data-tn-model-state="state" role="img" :aria-label="label">
    <div v-if="state !== 'ready'" class="tn-cinema-fallback">
      <slot name="fallback"><span>{{ label }}</span></slot>
    </div>
  </div>
</template>
<style scoped>
.tn-cinema-model{position:relative;display:block;width:100%;height:100%;min-height:240px;overflow:hidden;isolation:isolate}
.tn-cinema-fallback{position:absolute;inset:0;display:grid;place-items:center;text-align:center}
.tn-cinema-fallback :deep(img){width:100%;height:100%;object-fit:cover}
</style>
