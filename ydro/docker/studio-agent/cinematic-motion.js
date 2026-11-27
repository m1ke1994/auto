// Trusted, deterministic scroll motion. No dependencies, timers or network.
export const MOTION_PRESETS = Object.freeze([
  'custom','orbit_soft','orbit_dramatic','turntable','front_reveal',
  'fly_by','detail_focus','parallax_massive','idle_float','edge_spin_soft','light_sweep','hero_turn'
])
export const LIGHTING_PRESETS = Object.freeze({
  studio: Object.freeze({key:3,rim:2.8,fill:1,environment:1}),
  softbox: Object.freeze({key:2.4,rim:1.5,fill:1.4,environment:1.15}),
  dramatic: Object.freeze({key:3.6,rim:3.4,fill:.55,environment:.75}),
  editorial: Object.freeze({key:2.8,rim:1.8,fill:1.2,environment:1.1}),
  silhouette: Object.freeze({key:1.4,rim:4,fill:.8,environment:.85})
})
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v))
const finite=(v,f)=>typeof v==='number'&&Number.isFinite(v)?v:f

// All offsets are relative to the inspected opening angle. No random per-frame motion.
export function presetShots(name, openingYaw=50, strength=1) {
  const yaw=clamp(finite(openingYaw,50),-360,360)
  const k=clamp(finite(strength,1),.25,1.25)
  const shot=(at,dy=0,pitch=14,distance=1,target=[0,0,0],modelYaw=0,lift=0,light=0)=>({
    at,yaw:yaw+dy*k,pitch:14+(pitch-14)*k,distance:1+(distance-1)*k,
    target:target.map(v=>v*k),modelYaw:modelYaw*k,lift:lift*k,light:light*k
  })
  switch(name){
    case 'hero_turn': return [shot(0),shot(.25,-8,12,1.04,[0,0,0],14,0,18),shot(.65,-22,10,1,[.035,0,0],42,0,48),shot(1,-32,15,1.04,[0,0,0],58,0,75)]
    case 'orbit_soft': return [shot(0),shot(.5,-35,17,.98),shot(1,-75,12,1.05)]
    case 'orbit_dramatic': return [shot(0),shot(.38,-50,8,1.08),shot(.72,-100,20,.98),shot(1,-155,14,1.05)]
    case 'turntable': return [shot(0),shot(.5,0,14,1,[0,0,0],180),shot(1,0,14,1,[0,0,0],360)]
    case 'front_reveal': return [shot(0),shot(.4,-18,10,1.05),shot(1,-62,12,1)]
    case 'fly_by': return [shot(0),shot(.42,22,9,1.08,[-.12,0,0]),shot(1,-36,17,1.12,[.12,0,0])]
    case 'detail_focus': return [shot(0,0,14,1.12),shot(.55,-25,18,.98,[0,.05,0]),shot(1,-48,12,1.1)]
    case 'parallax_massive': return [shot(0),shot(.5,-14,11,1.02,[-.06,0,0]),shot(1,-28,16,1.08,[.06,0,0])]
    case 'idle_float': return [shot(0),shot(.33,5,14,1,[0,0,0],12,.06),shot(.66,-5,14,1,[0,0,0],-8,.025),shot(1,0,14,1)]
    case 'edge_spin_soft': return [shot(0),shot(.5,0,16,1,[0,0,0],28),shot(1,0,12,1,[0,0,0],-18)]
    case 'light_sweep': return [shot(0),shot(.5,0,14,1,[0,0,0],0,0,65),shot(1,0,14,1,[0,0,0],0,0,-45)]
    default: return []
  }
}

/** A primary hero needs a visible change of relative view, not merely moving lights. */
export function heroMotionShots(shots,openingYaw=50) {
  const relative=s=>finite(s.yaw,openingYaw)-finite(s.modelYaw,0)
  const angles=shots.map(relative)
  if(angles.length>=2&&Math.max(...angles)-Math.min(...angles)>=60) return shots
  const start=shots[0]
  return presetShots('hero_turn',finite(start?.yaw,openingYaw),1).map(s=>({...s,modelYaw:s.modelYaw+finite(start?.modelYaw,0)}))
}
export function cameraTrackProgress(top,height,viewport,sticky=false,inset=0) {
  const travel=sticky&&height>=viewport*1.35
    ?Math.max(viewport*.35,height-(viewport-inset))
    :Math.max(viewport*.35,height*.48)
  return clamp((inset-top)/travel,0,1)
}

// One native-scroll track, reversible; reveal begins after the opening act.
export function heroFilmProgress(top,height,viewport) {
  const progress=clamp(-top/Math.max(1,height-viewport),0,1)
  const x=clamp((progress-.38)/.18,0,1)
  return {progress,motion:clamp(progress/.86,0,1),reveal:x*x*(3-2*x)}
}

export function pinnedFilmFrame(top,height,viewport,turn=360,compact=false) {
  const travel=Math.max(0,height-viewport)
  const offset=clamp(-top,0,travel)
  const progress=travel>0?offset/travel:0
  const motion=progress
  const fade=(a,b)=>{const x=clamp((progress-a)/(b-a),0,1);return x*x*(3-2*x)}
  return {offset,progress,motion,angle:(turn===180?180:360)*motion,title:compact?fade(.10,.18):fade(.16,.25),description:compact?fade(.28,.38):fade(.40,.50),actions:compact?fade(.48,.58):fade(.65,.75)}
}

/** Center the projected bounding box in both axes; units are viewport pixels. */
export function centeredViewOffset(xs,ys,width,height) {
  if(xs.length===0||ys.length===0||!xs.every(Number.isFinite)||!ys.every(Number.isFinite))return [0,0]
  return [(Math.min(...xs)+Math.max(...xs))*width/4,-(Math.min(...ys)+Math.max(...ys))*height/4]
}

/** Frame-rate independent, bounded scroll easing. Exact endpoints after settling. */
export function smoothScrollProgress(current,target,elapsedMs) {
  const end=clamp(finite(target,0),0,1)
  const start=clamp(finite(current,end),0,1)
  if(Math.abs(end-start)<=.0008)return end
  const next=start+(end-start)*(1-Math.exp(-clamp(finite(elapsedMs,16.67),1,350)/45))
  return Math.abs(end-next)<=.0008?end:next
}

export function scrollFrameElapsed(previousTimestamp,timestamp) {
  // The first frame after idle uses one nominal interval; a slow active frame
  // must use real elapsed time, not masquerade as a 60 Hz frame.
  return previousTimestamp===null?16.67:Math.max(1,finite(timestamp-previousTimestamp,16.67))
}

/** Limit drawing-buffer cost without reducing CSS size or camera framing. */
export function modelPixelRatio(width,height,deviceRatio=1,mobile=false) {
  const pixels=Math.max(1,width)*Math.max(1,height)
  return Math.min(Math.max(1,finite(deviceRatio,1)),mobile?1.25:1.5,Math.sqrt((mobile?900000:2000000)/pixels))
}

/** A nested scrolling/clipping ancestor breaks native viewport sticky. */
export function needsTransformPin(overflowModes) {
  return overflowModes.some(mode=>/^(auto|scroll|hidden|overlay)$/.test(mode))
}

/** Camera distance is planned once per viewport, never fitted afresh on scroll. */
export function stableFilmCameraTrack(corners,yaw,pitch,start,turn,aspect,fov=38){
  const radians=Math.PI/180,cy=Math.cos(yaw*radians),sy=Math.sin(yaw*radians)
  const cp=Math.cos(pitch*radians),sp=Math.sin(pitch*radians)
  const tv=Math.tan(fov*radians/2),th=tv*aspect
  const count=Math.ceil(Math.abs(turn))+1
  const samples=Array.from({length:count},(_,i)=>{
    const angle=(start+turn*i/(count-1))*radians,c=Math.cos(angle),s=Math.sin(angle)
    const points=corners.map(([x,y,z])=>{
      const rx=x*c+z*s,rz=z*c-x*s
      return [rx*cy-rz*sy,-rx*sy*sp+y*cp-rz*cy*sp,rx*sy*cp+y*sp+rz*cy*cp]
    })
    const fit=Math.max(.15,...points.map(([x,y,z])=>z+Math.max(Math.abs(x)/(th*.84),Math.abs(y)/(tv*.84),.15)))
    return {points,fit}
  })
  const coverage=(sample,distance)=>{
    const x=sample.points.map(p=>p[0]/((distance-p[2])*th))
    const y=sample.points.map(p=>p[1]/((distance-p[2])*tv))
    return Math.max(Math.max(...x)-Math.min(...x),Math.max(...y)-Math.min(...y))/2
  }
  const peak=Math.max(...samples.map(s=>s.fit))*1.005
  // Prefer one constant distance. For unusually narrow silhouettes, retain
  // enough coverage using a smoothly varying, conservative distance envelope.
  const base=samples.map((s,i)=>{
    const window=samples.slice(Math.max(0,i-5),i+6)
    return Math.max(s.fit,window.reduce((n,x)=>n+x.fit,0)/window.length)*1.005
  })
  let blend=1
  for(let i=0;i<samples.length;i++){
    const s=samples[i]
    if(coverage(s,peak)>=.58)continue
    let lo=s.fit*1.005,hi=peak
    for(let k=0;k<24;k++){const mid=(lo+hi)/2;if(coverage(s,mid)>=.58)lo=mid;else hi=mid}
    base[i]=Math.min(base[i],lo)
    if(peak>base[i])blend=Math.min(blend,clamp((lo-base[i])/(peak-base[i]),0,1))
  }
  const distances=base.map(x=>x+(peak-x)*blend)
  return {distances,mode:blend===1?'fixed':'track',minCoverage:Math.min(...samples.map((s,i)=>coverage(s,distances[i])))}
}

export function filmCameraDistance(track,progress){
  const index=clamp(progress,0,1)*(track.distances.length-1)
  const a=Math.floor(index),b=Math.min(a+1,track.distances.length-1)
  return track.distances[a]+(track.distances[b]-track.distances[a])*(index-a)
}
