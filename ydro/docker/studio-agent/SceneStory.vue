<script setup>
import {computed,ref,onMounted,onBeforeUnmount} from 'vue'
const props=defineProps({
  chapters:{type:Array,required:true},
  mode:{type:String,default:'split'},
  label:{type:String,default:'История'}
})
const items=computed(()=>props.chapters.slice(0,8))
const variant=computed(()=>['split','overlay','reverse'].includes(props.mode)?props.mode:'split')
const root=ref(null),active=ref(0)
let raf=0,observer
function update(){
  raf=0
  if(!root.value)return
  const list=Array.from(root.value.querySelectorAll('[data-tn-story-chapter]'))
  if(!list.length)return
  const line=window.innerHeight*.5
  let closest=Infinity,index=0
  list.forEach((node,i)=>{
    const r=node.getBoundingClientRect(),d=Math.abs(r.top+r.height*.5-line)
    if(d<closest){closest=d;index=i}
  })
  active.value=index
}
function schedule(){if(!raf)raf=requestAnimationFrame(update)}
onMounted(()=>{
  window.addEventListener('scroll',schedule,{passive:true})
  window.addEventListener('resize',schedule,{passive:true})
  observer=new ResizeObserver(schedule);observer.observe(root.value)
  schedule()
})
onBeforeUnmount(()=>{
  window.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule)
  observer?.disconnect();cancelAnimationFrame(raf)
})
</script>

<template>
  <div ref="root" class="tn-story" :class="'tn-story--'+variant" data-tn-story :data-tn-active="active" data-tn-camera-track role="region" :aria-label="label">
    <div class="tn-story-stage">
      <div class="tn-story-visual">
        <slot name="visual" :item="items[active]" :index="active">
          <img v-if="items[active]?.image" :src="items[active].image" :alt="items[active].alt||''" loading="lazy">
        </slot>
      </div>
      <span class="tn-story-counter" aria-hidden="true">{{ String(active+1).padStart(2,'0') }} / {{ String(items.length).padStart(2,'0') }}</span>
    </div>
    <div class="tn-story-chapters">
      <article v-for="(item,index) in items" :key="index" data-tn-story-chapter :data-active="index===active" class="tn-story-chapter">
        <div class="tn-story-caption">
          <slot name="chapter" :item="item" :index="index" :active="index===active">
            <p v-if="item.kicker" class="tn-story-kicker">{{ item.kicker }}</p>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
            <img v-if="item.image" class="tn-story-inline-image" :src="item.image" :alt="item.alt||''" loading="lazy">
          </slot>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.tn-story{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:clamp(20px,5vw,80px);position:relative;min-width:0;isolation:isolate}
.tn-story-stage{position:sticky;top:var(--tn-story-top,100px);height:min(72vh,760px);align-self:start;min-width:0;display:grid;grid-template-rows:minmax(0,1fr) auto}
.tn-story-visual{position:relative;min-height:0;min-width:0;border-radius:var(--tn-story-radius,20px);overflow:clip;background:var(--tn-story-bg,transparent)}
.tn-story-visual>img{width:100%;height:100%;display:block;object-fit:cover}
.tn-story-counter,.tn-story-kicker{font-size:.78rem;letter-spacing:.15em;font-variant-numeric:tabular-nums}
.tn-story-counter{padding:12px 0}
.tn-story-chapters{min-width:0}
.tn-story-chapter{min-height:65vh;display:flex;align-items:center;min-width:0}
.tn-story-caption{max-width:56ch;padding:24px 0;transition:transform .45s ease;transform:translateY(12px)}
.tn-story-chapter[data-active=true] .tn-story-caption{transform:translateY(0)}
.tn-story-caption h3{font-size:clamp(1.8rem,4.8vw,4.5rem);line-height:1.02;letter-spacing:-.05em;margin:.35em 0}
.tn-story-caption p{line-height:1.65;margin:.5em 0}
.tn-story-inline-image{display:none;width:100%;height:auto;margin:20px 0 0;border-radius:var(--tn-story-radius,20px)}
.tn-story--reverse{grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr)}
.tn-story--reverse .tn-story-stage{grid-column:2;grid-row:1}
.tn-story--reverse .tn-story-chapters{grid-column:1;grid-row:1}
.tn-story--overlay{grid-template-columns:minmax(0,1fr);gap:0}
.tn-story--overlay .tn-story-stage,.tn-story--overlay .tn-story-chapters{grid-column:1;grid-row:1}
.tn-story--overlay .tn-story-stage{height:min(82vh,860px)}
.tn-story--overlay .tn-story-chapters{position:relative;z-index:1;pointer-events:none;padding:0 clamp(16px,4vw,64px)}
.tn-story--overlay .tn-story-caption{padding:clamp(16px,3vw,32px);color:var(--tn-caption-color,#fff);background:var(--tn-caption-bg,rgba(15,17,22,.90));border-radius:var(--tn-story-radius,20px);pointer-events:auto}
@media(max-width:760px),(prefers-reduced-motion:reduce){
  .tn-story,.tn-story--reverse,.tn-story--overlay{display:block}
  .tn-story .tn-story-stage{position:relative;top:auto;height:auto;min-height:0}
  .tn-story .tn-story-visual{height:clamp(220px,55vw,480px)}
  .tn-story .tn-story-chapters{padding:0;pointer-events:auto}
  .tn-story .tn-story-chapter{min-height:0;display:block;padding:20px 0}
  .tn-story .tn-story-caption{transform:none;transition:none;max-width:none}
  .tn-story-inline-image{display:block}
}
</style>
