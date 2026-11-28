import {createApp,h} from 'vue'
import Carousel from './__carousel_test.vue'
const items=Array.from({length:4},(_,i)=>({title:'Slide '+(i+1),text:'Example content'}))
createApp({render:()=>h('main',{style:'max-width:100%;padding:12px;box-sizing:border-box'},[h('div',{style:'height:500px'},'Before'),h(Carousel,{items,mode:new URLSearchParams(location.search).get('mode')||'horizontal'}),h('div',{style:'height:1100px'},'After')])}).mount('#app')
