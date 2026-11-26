import test from 'node:test'
import assert from 'node:assert/strict'
import { MOTION_PRESETS, LIGHTING_PRESETS, presetShots, heroMotionShots, cameraTrackProgress } from './cinematic-motion.js'

test('all presets are bounded, deterministic and genuinely distinct',()=>{
  const signatures=new Set()
  for(const name of MOTION_PRESETS.filter(n=>n!=='custom')){
    const shots=presetShots(name,225)
    assert.equal(shots[0].yaw,225)
    assert.equal(shots[0].at,0)
    assert.equal(shots.at(-1).at,1)
    assert.ok(shots.every((s,i)=>i===0||s.at>shots[i-1].at))
    assert.ok(shots.every(s=>Number.isFinite(s.yaw)&&s.distance>=.72&&s.distance<=1.35))
    assert.equal(JSON.stringify(shots),JSON.stringify(presetShots(name,225)))
    signatures.add(JSON.stringify(shots))
  }
  assert.equal(signatures.size,11)
  assert.equal(Object.keys(LIGHTING_PRESETS).length,5)
})
test('object turn and light sweep need no camera yaw change',()=>{
  const turn=presetShots('turntable',135)
  assert.ok(turn.every(s=>s.yaw===135))
  assert.equal(turn.at(-1).modelYaw,360)
  const light=presetShots('light_sweep',45)
  assert.ok(light.every(s=>s.yaw===45&&s.modelYaw===0))
  assert.notEqual(light[0].light,light[1].light)
  assert.deepEqual(presetShots('custom'),[])
})
test('invalid inputs and intensity bounds',()=>{
  const shots=presetShots('orbit_soft',Infinity,NaN)
  assert.equal(shots[0].yaw,50)
  assert.equal(presetShots('turntable',0,100).at(-1).modelYaw,450)
  assert.equal(presetShots('turntable',0,-100).at(-1).modelYaw,90)
})

test('primary hero gets a readable relative turn even when camera and object cancel',()=>{
  const weak=[{at:0,yaw:135,modelYaw:0},{at:1,yaw:145,modelYaw:10}]
  const shots=heroMotionShots(weak,135)
  assert.equal(shots[0].yaw,135)
  assert.ok(Math.abs((shots.at(-1).yaw-shots.at(-1).modelYaw)-(shots[0].yaw-shots[0].modelYaw))>=60)
  assert.equal(heroMotionShots(presetShots('orbit_dramatic',135),135).at(-1).yaw,-20)
})
test('sticky track progresses across its actual visible travel',()=>{
  assert.equal(cameraTrackProgress(64,1600,900,true,64),0)
  assert.equal(cameraTrackProgress(-700,1600,900,true,64),1)
  assert.ok(cameraTrackProgress(-250,900,900,false,0)>.5)
})
