<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
const props=defineProps({
  items:{type:Array,required:true},
  mode:{type:String,default:'horizontal'},
  label:{type:String,default:'Галерея'},
  previousLabel:{type:String,default:'Предыдущий слайд'},
  nextLabel:{type:String,default:'Следующий слайд'}
})
const modes=['narrative','horizontal','stack','showcase','chapter','editorial']
const variant=computed(()=>modes.includes(props.mode)?props.mode:'horizontal')
const slides=computed(()=>props.items.slice(0,12))
const track=ref(null),active=ref(0)
let observer,raf=0,query
const children=()=>Array.from(track.value?.children||[]).filter(e=>e.hasAttribute('data-tn-slide'))
function measure(){
  raf=0
  const el=track.value
  if(!el)return
  const rect=el.getBoundingClientRect()
  const center=rect.left+el.clientWidth/2
  const list=children()
  if(!list.length)return
  if(el.scrollLeft<=2){active.value=0;return}
  if(el.scrollLeft>=el.scrollWidth-el.clientWidth-2){active.value=list.length-1;return}
  let closest=Infinity
  list.forEach((child,i)=>{
    const r=child.getBoundingClientRect(),d=Math.abs(r.left+r.width/2-center)
    if(d<closest){closest=d;active.value=i}
  })
}
function schedule(){if(!raf)raf=requestAnimationFrame(measure)}
function go(index){
  const el=track.value,list=children()
  if(!el||!list.length)return
  const i=Math.max(0,Math.min(list.length-1,index))
  const r=list[i].getBoundingClientRect(),t=el.getBoundingClientRect()
  const left=el.scrollLeft+r.left-t.left-(el.clientWidth-r.width)/2
  el.scrollTo({left:Math.max(0,Math.min(el.scrollWidth-el.clientWidth,left)),behavior:query?.matches?'instant':'smooth'})
}
function key(event){
  if(event.key==='ArrowRight'){event.preventDefault();go(active.value+1)}
  else if(event.key==='ArrowLeft'){event.preventDefault();go(active.value-1)}
  else if(event.key==='Home'){event.preventDefault();go(0)}
  else if(event.key==='End'){event.preventDefault();go(slides.value.length-1)}
}
onMounted(()=>{
  query=matchMedia('(prefers-reduced-motion: reduce)')
  observer=new ResizeObserver(schedule);observer.observe(track.value)
  schedule()
})
onBeforeUnmount(()=>{observer?.disconnect();cancelAnimationFrame(raf)})
</script>

<template>
  <div class="tn-carousel" :class="'tn-carousel--'+variant" data-tn-carousel :data-tn-carousel-mode="variant" :data-tn-active="active" :aria-label="label" role="region">
    <div ref="track" class="tn-carousel-track" data-tn-carousel-track tabindex="0" @scroll.passive="schedule" @keydown.self="key">
      <article v-for="(item,index) in slides" :key="index" class="tn-carousel-slide" data-tn-slide :data-active="index===active">
        <slot name="slide" :item="item" :index="index" :active="index===active">
          <div class="tn-carousel-copy">
            <img v-if="item.image" :src="item.image" :alt="item.alt||''" loading="lazy">
            <p v-if="item.kicker" class="tn-carousel-kicker">{{ item.kicker }}</p>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
          </div>
        </slot>
      </article>
    </div>
    <div v-if="slides.length>1" class="tn-carousel-controls">
      <span class="tn-carousel-count" aria-live="polite">{{ String(active+1).padStart(2,'0') }} / {{ String(slides.length).padStart(2,'0') }}</span>
      <div class="tn-carousel-dots">
        <button v-for="(_,index) in slides" :key="index" type="button" :aria-label="label+' '+(index+1)" :aria-current="active===index?'true':undefined" @click="go(index)"></button>
      </div>
      <button type="button" data-tn-carousel-prev :disabled="active===0" :aria-label="previousLabel" @click="go(active-1)">←</button>
      <button type="button" data-tn-carousel-next :disabled="active===slides.length-1" :aria-label="nextLabel" @click="go(active+1)">→</button>
    </div>
  </div>
</template>

<style scoped>
.tn-carousel{width:100%;min-width:0;--tn-slide-width:76%;--tn-slide-gap:clamp(12px,2.5vw,32px)}
.tn-carousel-track{display:flex;position:relative;direction:ltr;align-items:stretch;gap:var(--tn-slide-gap);overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;overscroll-behavior-inline:contain;scrollbar-width:thin;padding:8px 0 20px;box-sizing:border-box}
.tn-carousel-track::before,.tn-carousel-track::after{content:'';flex:0 0 max(0px,calc((100% - var(--tn-slide-width))/2 - var(--tn-slide-gap)))}
.tn-carousel-slide{flex:0 0 var(--tn-slide-width);min-width:0;box-sizing:border-box;scroll-snap-align:center;border-radius:var(--tn-slide-radius,22px);overflow:hidden;background:var(--tn-slide-bg,transparent)}
.tn-carousel-copy{padding:clamp(16px,3vw,36px)}
.tn-carousel-copy img{display:block;width:100%;height:clamp(180px,30vw,440px);object-fit:cover;border-radius:calc(var(--tn-slide-radius,22px)*.65)}
.tn-carousel-copy h3{font-size:clamp(1.35rem,3.4vw,3rem);line-height:1.08;margin:.6em 0 .35em;letter-spacing:-.035em}
.tn-carousel-copy p{max-width:58ch;line-height:1.6;margin:.4em 0}
.tn-carousel-kicker,.tn-carousel-count{font-size:.78rem;letter-spacing:.12em;font-variant-numeric:tabular-nums}
.tn-carousel-controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0}
.tn-carousel-dots{display:flex;gap:8px;flex:1;flex-wrap:wrap;justify-content:center}
.tn-carousel-controls button{font:inherit;color:inherit;border:1px solid currentColor;background:transparent;border-radius:999px;min-width:44px;min-height:44px;cursor:pointer}
.tn-carousel-controls button:disabled{opacity:.35;cursor:default}
.tn-carousel-dots button{min-width:24px;min-height:24px;border:0;position:relative}
.tn-carousel-dots button::after{content:'';position:absolute;inset:8px;border-radius:999px;background:currentColor;opacity:.35}
.tn-carousel-dots button[aria-current=true]::after{opacity:1}
.tn-carousel-track:focus-visible,.tn-carousel-controls button:focus-visible{outline:2px solid currentColor;outline-offset:2px}
.tn-carousel--narrative{--tn-slide-width:100%;--tn-slide-radius:0px}
.tn-carousel--narrative .tn-carousel-copy{min-height:clamp(280px,55vh,520px);display:flex;flex-direction:column;justify-content:center}
.tn-carousel--horizontal{--tn-slide-width:70%}
.tn-carousel--stack{--tn-slide-width:86%}
.tn-carousel--stack .tn-carousel-slide{border:1px solid color-mix(in srgb,currentColor 16%,transparent);box-shadow:0 8px 24px #0002;transform:scale(.94);transition:transform .45s ease}
.tn-carousel--stack .tn-carousel-slide[data-active=true]{transform:scale(1)}
.tn-carousel--showcase{--tn-slide-width:74%}
.tn-carousel--showcase .tn-carousel-slide{transform:scale(.90);transition:transform .5s ease}
.tn-carousel--showcase .tn-carousel-slide[data-active=true]{transform:scale(1)}
.tn-carousel--chapter{--tn-slide-width:100%;--tn-slide-radius:12px}
.tn-carousel--chapter .tn-carousel-copy{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center;gap:16px}
.tn-carousel--chapter .tn-carousel-copy img{grid-row:span 3;height:clamp(220px,40vw,520px)}
.tn-carousel--editorial{--tn-slide-width:62%;--tn-slide-radius:2px}
.tn-carousel--editorial .tn-carousel-copy{padding:clamp(12px,2vw,24px)}
@media(max-width:640px){.tn-carousel{--tn-slide-width:90%;--tn-slide-gap:12px}.tn-carousel--narrative,.tn-carousel--chapter{--tn-slide-width:100%}.tn-carousel--chapter .tn-carousel-copy{display:block}.tn-carousel-dots{order:3;flex-basis:100%}}
@media(prefers-reduced-motion:reduce){.tn-carousel-slide{transform:none!important;transition:none!important}}
</style>
