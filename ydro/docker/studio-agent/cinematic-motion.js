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
