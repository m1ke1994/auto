import test from 'node:test'
import assert from 'node:assert/strict'
import { MOTION_PRESETS, LIGHTING_PRESETS, presetShots, heroMotionShots, cameraTrackProgress, heroFilmProgress, pinnedFilmFrame, centeredViewOffset, smoothScrollProgress, scrollFrameElapsed, modelPixelRatio, needsTransformPin } from './cinematic-motion.js'

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

test('compact 180 film pins and releases over the shorter desktop and mobile tracks',()=>{
  for(const [viewport,ratio] of [[900,2.2],[844,1.8],[540,2.2]]){
    const height=viewport*ratio,travel=height-viewport
    const at=f=>pinnedFilmFrame(-travel*f,height,viewport,180,true)
    for(const f of [0,.25,.5,.75,1]){
      assert.ok(Math.abs(at(f).angle-180*f)<1e-8)
      assert.ok(Math.abs(at(f).offset-travel*f)<1e-8)
    }
    assert.equal(at(0).title,0);assert.equal(at(0).description,0);assert.equal(at(0).actions,0)
    assert.ok(at(.18).title>.999);assert.equal(at(.25).description,0)
    assert.ok(at(.38).description>.999);assert.equal(at(.375).actions,0)
    assert.ok(at(.58).actions>.999);assert.equal(at(.625).actions,1)
    assert.ok(Math.abs(at(1.2).offset-travel)<1e-8)
    assert.ok(Math.abs(at(1.2).angle-180)<1e-8)
    assert.deepEqual(at(.25),at(.25))
  }
})

test('scroll easing converges in both directions without overshoot or endless RAF',()=>{
  let x=0,frames=0
  while(x!==1&&frames++<100)x=smoothScrollProgress(x,1,16.67)
  assert.equal(x,1);assert.ok(frames<30)
  frames=0
  while(x!==0&&frames++<100)x=smoothScrollProgress(x,0,16.67)
  assert.equal(x,0);assert.ok(frames<30)
  assert.equal(smoothScrollProgress(.5,.5,16),.5)
  assert.ok(Math.abs(smoothScrollProgress(smoothScrollProgress(0,1,16),1,16)-smoothScrollProgress(0,1,32))<1e-10)
})
test('drawing buffer is bounded and CSS viewport is independent of DPR',()=>{
  for(const [w,h,dpr,mobile] of [[1440,900,2,false],[3840,2160,2,false],[390,844,3,true],[760,1000,3,true]]){
    const ratio=modelPixelRatio(w,h,dpr,mobile)
    assert.ok(w*h*ratio*ratio<=(mobile?900000:2000000)+1e-6)
    assert.ok(ratio<=(mobile?1.25:1.5))
  }
  assert.equal(modelPixelRatio(390,844,1,true),1)
})
test('native sticky is preferred unless a nested ancestor creates a scroll container',()=>{
  assert.equal(needsTransformPin(['visible','clip']),false)
  for(const mode of ['auto','scroll','hidden','overlay'])assert.equal(needsTransformPin(['visible',mode]),true)
})

test('slow active GPU frames use real elapsed time and settle within bounded wall time',()=>{
  assert.equal(scrollFrameElapsed(null,5000),16.67)
  assert.equal(scrollFrameElapsed(5000,5200),200)
  assert.equal(scrollFrameElapsed(5200,5600),400)
  for(const gap of [16.67,33,64,100,150,200,350,500]){
    for(const [start,target] of [[0,1],[1,0],[.25,.875]]){
      let current=start,elapsed=0,previous=null
      while(current!==target&&elapsed<2000){
        current=smoothScrollProgress(current,target,scrollFrameElapsed(previous,elapsed))
        previous=elapsed
        elapsed+=gap
      }
      assert.equal(current,target)
      assert.ok(elapsed<=350+2*gap,'slow active frames must not prolong easing')
    }
  }
})
