import assert from 'node:assert/strict'
import { sampleStory } from '../src/components/landing/storyMotion.js'
import * as THREE from 'three'
let previous = sampleStory(0)
const visited = new Set()
for(let step=0;step<=1000;step++) {
  const state=sampleStory(step/1000)
  for(const key of ['progress','explode','resolve','orbit']) {
    assert.ok(Number.isFinite(state[key]) && state[key]>=0 && state[key]<=1,key)
    assert.ok(state[key]>=previous[key],key+' must move forward continuously')
    assert.ok(Math.abs(state[key]-previous[key])<.02,key+' must not jump')
  }
  visited.add(state.active);previous=state
}
assert.deepEqual([...visited],[-1,0,1,2,3])
assert.equal(sampleStory(-1).progress,0)
assert.equal(sampleStory(2).progress,1)
// Verify the four final service modules fit the available scene at the requested widths.
for(const width of [360,390,768,1024,1440]) {
  const height=width<768?800:900
  const sceneWidth=width<768?width*1.06:width*(width<1024?.69:.66)
  const sceneHeight=height*(width<768?.55:.87)
  const aspect=sceneWidth/sceneHeight
  const distance=12.8*Math.max(1,1.05/aspect)
  const camera=new THREE.PerspectiveCamera(32,aspect,.1,50)
  camera.position.set(Math.sin(-.06)*distance,.5,Math.cos(-.06)*distance)
  camera.lookAt(0,0,0);camera.updateMatrixWorld(true)
  for(const x of [-2,2]) for(const y of [-1.35,1.25]) for(const dx of [-.75,.75]) for(const dy of [-.75,.75]) {
    const point=new THREE.Vector3(x+dx,y+dy,.9).project(camera)
    assert.ok(Math.abs(point.x)<.99 && Math.abs(point.y)<.99,`service module clipped at ${width}px`)
  }
}
console.log('Story checks passed: continuous scroll phases, four service stages, camera framing at 360/390/768/1024/1440px.')

// Film edit points must always show a scene, including crossfades and reverse scrolling.
const {filmScenes,filmSceneAt,filmCubeAt,filmSceneStyle}=await import('../src/components/landing/filmTimeline.js')
const chapters=new Set()
let lastCube=filmCubeAt(0)
for(let step=0;step<=2000;step++) {
 const progress=step/2000
 chapters.add(filmSceneAt(progress))
 const weights=filmScenes.map((_,i)=>filmSceneStyle(i,progress).opacity)
 assert.ok(Math.abs(weights.reduce((a,b)=>a+b,0)-1)<.00001,'a film edit must not leave an empty frame')
 assert.ok(weights.every(weight=>weight>=0&&weight<=1))
 const cube=filmCubeAt(progress)
 assert.ok(Number.isFinite(cube)&&cube>=0&&cube<=1)
 assert.ok(Math.abs(cube-lastCube)<.015,'cube must not jump at an edit')
 lastCube=cube
}
assert.equal(chapters.size,8)
assert.equal(filmCubeAt(0),0)
assert.equal(filmCubeAt(.5),1)
assert.equal(filmCubeAt(1),0)
console.log('Film checks passed: 8 connected scenes, no empty crossfade frames, cube disassembly and final reconstruction.')

// Portrait shots keep the enlarged service cube visible throughout each camera arc.
for (const width of [360,390,768,1024,1440]) {
 const height=width<768?800:900
 const aspect=width<768?width*1.5/(height*.72):width/height
 for(const index of [0,1,2,3]) for(const take of [0,.5,1]) {
  const target=new THREE.Vector3(index%2===0?-2:2,index<2?1.25:-1.35,[.2,-.1,.1,.2][index])
  const angle=[-.36,.44,-.24,.32][index]+take*.3
  const distance=8.2*Math.max(1,1.15/aspect)
  const camera=new THREE.PerspectiveCamera(32,aspect,.1,50)
  camera.position.copy(target).add(new THREE.Vector3(Math.sin(angle)*distance,1.05+Math.sin(take*Math.PI)*.3,Math.cos(angle)*distance))
  camera.lookAt(target);camera.updateMatrixWorld(true)
  for(const x of [-1.1,1.1])for(const y of [-1.1,1.1])for(const z of [-.4,1.8]) {
   const projected=target.clone().add(new THREE.Vector3(x,y,z)).project(camera)
   assert.ok(Math.abs(projected.x)<1&&Math.abs(projected.y)<1,`portrait clipped at ${width}px, module ${index}`)
  }
 }
}
console.log('Portrait checks passed: four camera arcs and enlarged module framing at all five widths.')
