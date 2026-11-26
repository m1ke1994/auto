import test from 'node:test'
import assert from 'node:assert/strict'
import { MOTION_PRESETS, LIGHTING_PRESETS, presetShots, heroMotionShots, cameraTrackProgress, heroFilmProgress, pinnedFilmFrame, centeredViewOffset } from './cinematic-motion.js'

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

test('film has an opening act and reversible motion',()=>{
  const at=y=>heroFilmProgress(-y,3000,1000)
  assert.deepEqual(at(0),{progress:0,motion:0,reveal:0})
  assert.equal(at(500).reveal,0)
  assert.ok(at(1000).reveal>0&&at(1000).motion<1)
  assert.deepEqual(at(2000),{progress:1,motion:1,reveal:1})
  assert.ok(at(500).motion<at(1000).motion)
})

test('full viewport pin, captions, half/full turn and release',()=>{
  const at=(y,turn=180)=>pinnedFilmFrame(-y,3600,900,turn)
  for(const y of [0,450,900,1350,1800,2250,2700])assert.equal(-y+at(y).offset,0)
  assert.equal(at(0).angle,0)
  assert.equal(at(0).title,0)
  assert.ok(at(900).title>0&&at(900).description===0)
  assert.ok(at(1800).description===1&&at(1800).actions<1)
  assert.equal(at(2700).angle,180)
  assert.equal(at(2700,360).angle,360)
  assert.equal(at(3000).offset,2700)
  assert.equal(-3000+at(3000).offset,-300)
  assert.ok(at(900).angle<at(1800).angle)
})

test('background turns 360 degrees in exact quarter steps without shifting captions',()=>{
  const at=f=>pinnedFilmFrame(-4500*f,5400,900)
  assert.deepEqual([0,.25,.5,.75,1].map(f=>at(f).angle),[0,90,180,270,360])
  assert.equal(at(.25).title,1);assert.equal(at(.25).description,0)
  assert.equal(at(.5).description,1);assert.equal(at(.5).actions,0)
  assert.equal(at(.75).actions,1)
  assert.deepEqual(centeredViewOffset([-.2,.8],[-.7,.3],1000,800).map(Math.round),[150,80])
  assert.deepEqual(centeredViewOffset([-.8,.8],[-.4,.4],1000,800),[0,-0])
})
