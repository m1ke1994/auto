<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import http from '../api/http'
import { BACKEND_URL } from '../config/env'

const projects=ref([]), current=ref(null), name=ref(''), prompt=ref(''), instruction=ref(''), selected=ref(null), busy=ref(false), error=ref(''), device=ref('100%')
const engine=ref('cinematic'), style=ref('cinema'), assetStyle=ref('realistic'), heroMode=ref('auto'), requireModel=ref(false)
const base='/api/studio/projects/'
const config=ref({provider:null,configured:false,cinematic_enabled:false,cinematic_max_cost_usd:2.5})
const styles=[['auto','Автоматический'],['business','Современный'],['premium','Премиальный'],['cinema','Кинематографический'],['3d','3D / объектная сцена']]
const heroModes=[['auto','Автовыбор композиции'],['immersive','Крупный объект на фоне'],['product','Предметная сцена'],['split','Разделённый Hero'],['cinematic','Полноэкранная сцена'],['editorial','Editorial-фотография'],['environment','Иммерсивное пространство']]
const revision=computed(()=>current.value?.revisions?.find(r=>r.id===selected.value))
const previewHtml=computed(()=>revision.value?.html.replaceAll('href="#page-', 'href="about:srcdoc#page-') || '')
const previewSrc=computed(()=>current.value?.preview_path ? BACKEND_URL+current.value.preview_path : '')
const cinematic=computed(()=>current.value?.engine==='cinematic')
const generating=computed(()=>['queued','running'].includes(current.value?.generation_status))

async function run(fn){if(busy.value)return;busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.response?.data?.detail||'Не удалось выполнить операцию. Проверьте локальную Studio.'}finally{busy.value=false}}
function apply(project){current.value=project;selected.value=project.revisions?.[0]?.id||null}
async function refresh(){
  const list=(await http.get(base)).data
  projects.value=list
  if(current.value){const updated=list.find(p=>p.id===current.value.id);if(updated)apply((await http.get(base+updated.id+'/')).data)}
}
onMounted(()=>run(async()=>{config.value=(await http.get('/api/studio/config/')).data;await refresh()}))
const poll=setInterval(()=>{if(projects.value.some(p=>['queued','running'].includes(p.generation_status)))refresh().catch(()=>{})},3000)
onBeforeUnmount(()=>clearInterval(poll))

function open(id){run(async()=>apply((await http.get(base+id+'/')).data))}
function create(){run(async()=>{
  const payload={name:name.value,prompt:prompt.value,style:style.value,engine:engine.value,asset_style:assetStyle.value,hero_mode:heroMode.value,require_model:requireModel.value}
  apply((await http.post(base,payload,{timeout:engine.value==='cinematic'?15000:105000})).data)
  await refresh();name.value='';prompt.value=''
})}
function edit(){run(async()=>{apply((await http.post(base+current.value.id+'/edit/',{instruction:instruction.value,revision:selected.value},{timeout:105000})).data);instruction.value=''})}
function publish(){run(async()=>{current.value=(await http.post(base+current.value.id+'/publish/'+selected.value+'/')).data})}
function download(){run(async()=>{
  const path=cinematic.value?base+current.value.id+'/cinematic-export/':base+current.value.id+'/export/'+selected.value+'/'
  const response=await http.get(path,{responseType:'blob'});const url=URL.createObjectURL(response.data);const a=document.createElement('a');a.href=url;a.download=cinematic.value?'tracknode-cinematic-site.zip':'tracknode-site.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
})}
function openPreview(){if(previewSrc.value)window.open(previewSrc.value,'_blank','noopener,noreferrer')}
</script>

<template>
<section class="studio">
  <header><div><small>TRACKNODE 2.0</small><h1>Studio</h1></div><span class="badge">{{config.cinematic_enabled?'Cinematic Engine готов':!config.provider?'Проверка AI-провайдера':config.provider==='demo'?'Локальный демо-режим':'AI: '+config.provider+(config.configured?' (настроен)':' (не настроен)')}}</span></header>
  <p>Создавайте быстрые дизайн-концепции или полноценные кинематографические сайты с индивидуальной арт-дирекцией, сценами, анимацией и проверенным локальным превью.</p>
  <p v-if="busy" role="status">Выполняем операцию…</p><p v-if="error" role="alert" class="error">{{error}}</p>
  <div class="projects"><button v-for="p in projects" :key="p.id" :disabled="busy" @click="open(p.id)">{{p.name}} <small v-if="p.engine==='cinematic'">· {{p.generation_status==='complete'?'готов':p.generation_status==='failed'?'ошибка':'в работе'}}</small></button><button :disabled="busy" @click="current=null">+ Новый проект</button></div>

  <form v-if="!current" class="panel create-form" @submit.prevent="create">
    <h2>Что будем создавать?</h2>
    <div class="choice-grid"><label>Движок<select v-model="engine"><option value="cinematic">Cinematic — полный сайт</option><option value="quick">Quick — быстрая концепция</option></select></label><label>Стиль<select v-model="style"><option v-for="s in styles" :key="s[0]" :value="s[0]">{{s[1]}}</option></select></label></div>
    <label>Название<input v-model="name" required maxlength="120"></label>
    <label>Описание<textarea v-model="prompt" required maxlength="8000" rows="7" placeholder="Опишите бизнес, аудиторию, характер бренда, обязательные разделы и известные ограничения. Движок сам выберет арт-дирекцию и композицию."></textarea></label>
    <template v-if="engine==='cinematic'">
      <div class="choice-grid"><label>Hero<select v-model="heroMode"><option v-for="h in heroModes" :key="h[0]" :value="h[0]">{{h[1]}}</option></select></label><label>Стиль ассета<select v-model="assetStyle"><option value="realistic">Реалистичный</option><option value="stylized">Стилизованный</option></select></label></div>
      <label class="check"><input v-model="requireModel" type="checkbox"> Обязательно подобрать настоящую скачиваемую модель Sketchfab; если качество не пройдёт preflight, остановить генерацию.</label>
      <p class="cost-note">Один контролируемый запуск, без автоматических платных повторов. Максимальный бюджет OpenHands для одного задания — ${{Number(config.cinematic_max_cost_usd).toFixed(2)}}. Preflight и Visual Critic выполняются отдельно и не запускают повторную генерацию.</p>
    </template>
    <button :disabled="busy||(engine==='cinematic'?!config.cinematic_enabled:!config.configured)">{{engine==='cinematic'?'Запустить Cinematic Engine':'Создать быструю концепцию'}}</button>
  </form>

  <div v-else class="workspace">
    <aside class="panel"><h2>{{current.name}}</h2><p>{{current.prompt}}</p>
      <template v-if="cinematic">
        <p class="status-card"><strong>{{current.generation_status==='complete'?'Визуально и технически проверено':current.generation_status==='failed'?'Генерация остановлена':current.generation_status==='running'?'Генерация выполняется':'Задание в очереди'}}</strong><br><small>{{current.generation_stage}}</small></p>
        <p v-if="current.generation_error" class="error">{{current.generation_error}}</p>
        <p v-if="generating">Можно оставить страницу открытой: статус обновляется автоматически. Повторный платный запуск заблокирован до завершения текущего.</p>
      </template>
      <template v-else><h3>История изменений</h3><button v-for="r in current.revisions" :key="r.id" :disabled="busy" :class="{active:r.id===selected}" @click="selected=r.id">{{r.instruction}}</button><form @submit.prevent="edit"><label>Изменение<textarea v-model="instruction" required maxlength="8000" placeholder="Например: сделай тёмный дизайн"></textarea></label><button :disabled="busy||!config.configured||!revision">Создать версию</button></form></template>
    </aside>
    <main class="panel preview-panel">
      <div class="toolbar"><button @click="device='100%'">Компьютер</button><button @click="device='390px'">Телефон</button><button v-if="cinematic" :disabled="!previewSrc" @click="openPreview">Открыть отдельно</button><button v-else :disabled="busy||!revision" @click="publish">Утвердить локально</button><button :disabled="busy||(cinematic?!previewSrc:!revision)" @click="download">Скачать ZIP</button></div>
      <div v-if="cinematic&&generating" class="waiting"><span class="spinner"/>OpenHands создаёт исходники, затем сайт будет собран и проверен настоящим Chromium.</div>
      <iframe v-else-if="cinematic&&previewSrc" title="Кинематографический предпросмотр сайта" sandbox="allow-scripts allow-same-origin" :src="previewSrc" :style="{width:device,maxWidth:'100%'}"></iframe>
      <iframe v-else-if="!cinematic&&revision" title="Предпросмотр сайта" sandbox="" :srcdoc="previewHtml" :style="{width:device,maxWidth:'100%'}"></iframe>
      <p v-else-if="current.generation_status==='failed'" class="error">Неудачный результат не принят. Исходный checkpoint и диагностические журналы сохранены локально.</p>
    </main>
  </div>
</section>
</template>

<style scoped>
.studio{padding:32px 24px;max-width:1500px;margin:auto;color:inherit}.studio header,.toolbar,.projects{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between}.studio h1{font-size:36px;font-weight:700}.studio h2{font-size:22px;font-weight:600}.studio p{margin:12px 0;overflow-wrap:anywhere}.badge{border:1px solid #8174ef;border-radius:20px;padding:6px 12px}.panel{border:1px solid #73738a55;border-radius:16px;padding:20px;min-width:0}.workspace{display:grid;grid-template-columns:minmax(240px,320px) minmax(0,1fr);gap:16px}.studio button{padding:10px 14px;border:1px solid #8174ef88;border-radius:9px;text-align:left;overflow-wrap:anywhere}.studio button:hover,.studio button.active{background:#7462e533}.studio button:disabled{opacity:.5}.studio label{display:block;margin:14px 0}.studio input,.studio textarea,.studio select{display:block;width:100%;padding:12px;background:#0d1726;color:inherit;border:1px solid #73738a88;border-radius:8px}.studio aside button{display:block;width:100%;margin:8px 0}.studio iframe{height:min(76vh,900px);min-height:650px;border:1px solid #8885;display:block;margin:12px auto;background:white}.error{color:#fb7185}.projects{justify-content:flex-start;margin:20px 0}.choice-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.check{display:flex!important;align-items:flex-start;gap:10px}.check input{width:auto;margin-top:4px}.cost-note,.status-card{padding:12px;border:1px solid #8174ef88;border-radius:9px}.waiting{min-height:520px;display:grid;place-content:center;text-align:center;gap:16px}.spinner{width:34px;height:34px;margin:auto;border:3px solid #8174ef44;border-top-color:#8174ef;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:800px){.workspace,.choice-grid{grid-template-columns:1fr}.studio{padding:12px}.studio iframe{min-height:620px}.toolbar{justify-content:flex-start}}
</style>
