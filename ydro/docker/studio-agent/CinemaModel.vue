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
  accent: { type: String, default: '#d6b48a' }
})
const host = ref(null)
const state = ref('loading')
const defaults = [
  { at: 0, yaw: 38, pitch: 12, distance: 1.25, target: [0,0,0] },
  { at: .45, yaw: -38, pitch: 8, distance: .92, target: [0,.05,0] },
  { at: .76, yaw: -95, pitch: 18, distance: .82, target: [0,.08,0] },
  { at: 1, yaw: -142, pitch: 14, distance: 1.25, target: [0,0,0] }
]
const finite = (n, fallback) => typeof n === 'number' && Number.isFinite(n) ? n : fallback
const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi,n))
function normalizedShots() {
  const source = props.shots.length >= 2 && props.shots.length <= 8 ? props.shots : defaults
  const list=source.map((s,i)=>({
    at:clamp(finite(s?.at,i/(source.length-1)),0,1),
    yaw:clamp(finite(s?.yaw,38),-360,360),
    pitch:clamp(finite(s?.pitch,12),-50,65),
    distance:clamp(finite(s?.distance,1.2),.65,3),
    target:[0,1,2].map(j=>clamp(finite(s?.target?.[j],0),-.45,.45))
  })).sort((a,b)=>a.at-b.at)
  if(list[0].at>0) list.unshift({...list[0],at:0})
  if(list.at(-1).at<1) list.push({...list.at(-1),at:1})
  return list
}
let renderer, scene, camera, model, env, pmrem, observer, intersection, raf=0, disposed=false
let visible=true, motionQuery, current=0, radius=1, frameCount=0, shots
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
  env?.dispose(); pmrem?.dispose()
  if(renderer){
    renderer.domElement.removeEventListener('webglcontextlost',lost)
    renderer.dispose()
    renderer.domElement.remove()
    renderer=null
  }
}
function fail() { state.value='fallback'; cleanup() }
function lost(e) { e.preventDefault(); fail() }
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
  if(!renderer || !model || !host.value || !visible) return
  // Use the surrounding narrative chapter, not a nested scroll container.
  const chapter=host.value.closest('[data-tn-camera-track]') || host.value
  const rect=chapter.getBoundingClientRect()
  const progress=clamp((innerHeight-rect.top)/Math.max(1,rect.height+innerHeight),0,1)
  current=motionQuery.matches?0:progress
  let b=shots.findIndex(s=>s.at>=current)
  if(b<1)b=1
  const from=shots[b-1],to=shots[b]
  const t=clamp((current-from.at)/Math.max(.00001,to.at-from.at),0,1)
  const blend=(a,b)=>THREE.MathUtils.lerp(a,b,t*t*(3-2*t))
  const yaw=THREE.MathUtils.degToRad(blend(from.yaw,to.yaw))
  const pitch=THREE.MathUtils.degToRad(blend(from.pitch,to.pitch))
  const target=new THREE.Vector3(...from.target.map((v,i)=>blend(v,to.target[i])*radius))
  const halfV=THREE.MathUtils.degToRad(camera.fov/2)
  const halfH=Math.atan(Math.tan(halfV)*camera.aspect)
  const fit=radius/Math.sin(Math.min(halfV,halfH))
  const distance=fit*blend(from.distance,to.distance)
  camera.position.copy(target).add(new THREE.Vector3(Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)).multiplyScalar(distance))
  camera.lookAt(target)
  renderer.render(scene,camera)
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
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'})
    renderer.outputColorSpace=THREE.SRGBColorSpace
    renderer.toneMapping=THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure=clamp(finite(props.exposure,1.1),.5,2)
    renderer.setClearColor(0x000000,0)
    renderer.domElement.style.cssText='display:block;width:100%;height:100%;pointer-events:none;'
    renderer.domElement.setAttribute('aria-hidden','true')
    renderer.domElement.addEventListener('webglcontextlost',lost)
    host.value.append(renderer.domElement)
    scene=new THREE.Scene()
    camera=new THREE.PerspectiveCamera(38,1,.01,100)
    pmrem=new THREE.PMREMGenerator(renderer)
    const room=new RoomEnvironment()
    try { env=pmrem.fromScene(room,.04); scene.environment=env.texture }
    finally { room.dispose() }
    scene.environmentIntensity=.85
    const key=new THREE.DirectionalLight(0xfff4e6,3)
    key.position.set(4,6,5); scene.add(key)
    const rim=new THREE.DirectionalLight(props.accent,2.8)
    rim.position.set(-4,2,-5); scene.add(rim)
    const fill=new THREE.HemisphereLight(0xc3d8ff,0x28221d,1)
    scene.add(fill)
    resize()
    const loader=new GLTFLoader()
    const gltf=await loader.loadAsync(import.meta.env.BASE_URL+props.modelPath)
    if(disposed || !renderer){disposeModel(gltf.scene);return}
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
