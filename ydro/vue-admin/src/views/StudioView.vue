<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../api/http'
const projects=ref([]), current=ref(null), name=ref(''), prompt=ref(''), instruction=ref(''), selected=ref(null), busy=ref(false), error=ref(''), device=ref('100%')
const base='/api/studio/projects/'
const style=ref('auto'), config=ref({provider:null,configured:false})
const styles=[['auto','Автоматический'],['business','Современный'],['premium','Премиальный'],['cinema','Кинематографический'],['3d','3D-концепция (без 3D-движка)']]
const revision=computed(()=>current.value?.revisions.find(r=>r.id===selected.value))
const previewHtml=computed(()=>revision.value?.html.replaceAll('href="#page-', 'href="about:srcdoc#page-') || '')
async function run(fn){ if(busy.value)return; busy.value=true; error.value=''; try{await fn()}catch(e){error.value=e.response?.data?.detail || 'Не удалось выполнить операцию. Проверьте настройки локального Studio.'}finally{busy.value=false}}
function apply(p){current.value=p;selected.value=p.revisions[0]?.id}
async function refresh(){projects.value=(await http.get(base)).data}
onMounted(()=>run(async()=>{config.value=(await http.get('/api/studio/config/')).data;await refresh()}))
function open(id){run(async()=>apply((await http.get(base+id+'/')).data))}
function create(){run(async()=>{apply((await http.post(base,{name:name.value,prompt:prompt.value,style:style.value},{timeout:105000})).data);await refresh();name.value='';prompt.value=''})}
function edit(){run(async()=>{apply((await http.post(base+current.value.id+'/edit/',{instruction:instruction.value,revision:selected.value},{timeout:105000})).data);instruction.value=''})}
function publish(){run(async()=>{const p=(await http.post(base+current.value.id+'/publish/'+selected.value+'/')).data;current.value=p})}
function download(){run(async()=>{const r=await http.get(base+current.value.id+'/export/'+selected.value+'/',{responseType:'blob'});const url=URL.createObjectURL(r.data);const a=document.createElement('a');a.href=url;a.download='tracknode-site.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)})}
</script>
<template>
<section class="studio">
<header><div><small>TRACKNODE 2.0</small><h1>Studio</h1></div><span class="badge">{{!config.provider?'Проверка AI-провайдера':config.provider==='demo'?'Локальный демо-режим':'AI: '+config.provider+(config.configured?' (настроен)':' (не настроен)')}}</span></header>
<p>Создавайте проекты с индивидуальной дизайн-спецификацией, проверяйте версии и экспортируйте Vue. GitHub, Vercel и внешний хостинг пока не подключены.</p>
<p v-if="busy" role="status">Выполняем операцию…</p><p v-if="config.provider&&!config.configured" class="error">AI-провайдер не настроен.</p><p v-if="error" role="alert" class="error">{{error}}</p>
<div class="projects"><button v-for="p in projects" :key="p.id" :disabled="busy" @click="open(p.id)">{{p.name}}</button><button :disabled="busy" @click="current=null">+ Новый проект</button></div>
<form v-if="!current" class="panel" @submit.prevent="create">
<h2>Что будем создавать?</h2><label>Название<input v-model="name" required maxlength="120"></label><label>Описание<textarea v-model="prompt" required maxlength="8000" rows="5" placeholder="Создай сайт для моего бизнеса..."></textarea></label><label>Стиль<select v-model="style"><option v-for="s in styles" :key="s[0]" :value="s[0]">{{s[1]}}</option></select></label><button :disabled="busy||!config.configured">{{config.provider==='demo'?'Создать демо-сайт':'Создать с ИИ'}}</button>
</form>
<div v-else class="workspace"><aside class="panel"><h2>{{current.name}}</h2><p>{{current.prompt}}</p><h3>История изменений</h3><button v-for="r in current.revisions" :key="r.id" :disabled="busy" :class="{active:r.id===selected}" @click="selected=r.id">{{r.instruction}} {{r.id===current.published_revision?'· локально утверждена':''}}</button><form @submit.prevent="edit"><label>Изменение<textarea v-model="instruction" required maxlength="8000" placeholder="Например: сделай темный дизайн"></textarea></label><button :disabled="busy||!config.configured||!revision">Создать версию</button></form><small>В режиме AI изменяется выбранная дизайн-спецификация. В демо доступны смена темы и тематические примеры.</small></aside>
<main class="panel"><p v-if="revision" class="provenance"><strong>Источник версии №{{revision.id}}: {{revision.provider==='demo'?'Демо — без нейросети':revision.provider==='deepseek'?'DeepSeek API — дизайн и контент':revision.provider==='yandex'?'Yandex AI — дизайн и контент':revision.provider}}</strong><br><small>{{revision.design?'HTML-предпросмотр и Vue-экспорт через встроенный движок':'Старый HTML'}} · {{new Date(revision.created_at).toLocaleString('ru-RU')}}</small></p><div class="toolbar"><button @click="device='100%'">Компьютер</button><button @click="device='390px'">Телефон</button><button :disabled="busy||!revision" @click="publish">Утвердить локально</button><button :disabled="busy||!revision" @click="download">Скачать ZIP</button></div><p v-if="current.published_revision">Утверждённая версия: {{current.published_revision}}. Публичный сайт не развёрнут.</p><iframe v-if="revision" title="Предпросмотр сайта" sandbox="" :srcdoc="previewHtml" :style="{width:device,maxWidth:'100%'}"></iframe></main></div>
</section>
</template>
<style scoped>
.studio{padding:32px 24px;max-width:1500px;margin:auto;color:inherit}.studio header,.toolbar,.projects{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between}.studio h1{font-size:36px;font-weight:700}.studio h2{font-size:22px;font-weight:600}.studio p{margin:12px 0;overflow-wrap:anywhere}.badge{border:1px solid #8174ef;border-radius:20px;padding:6px 12px}.panel{border:1px solid #73738a55;border-radius:16px;padding:20px;min-width:0}.workspace{display:grid;grid-template-columns:minmax(220px,300px) minmax(0,1fr);gap:16px}.studio button{padding:10px 14px;border:1px solid #8174ef88;border-radius:9px;text-align:left;overflow-wrap:anywhere}.studio button:hover,.studio button.active{background:#7462e533}.studio button:disabled{opacity:.5}.studio label{display:block;margin:14px 0}.studio input,.studio textarea,.studio select{display:block;width:100%;padding:12px;background:transparent;color:inherit;border:1px solid #73738a88;border-radius:8px}.studio aside button{display:block;width:100%;margin:8px 0}.studio iframe{height:650px;border:1px solid #8885;display:block;margin:12px auto;background:white}.error{color:#d65a5a}.provenance{padding:12px;border:1px solid #8174ef88;border-radius:9px}.projects{justify-content:flex-start;margin:20px 0}@media(max-width:800px){.workspace{grid-template-columns:1fr}.studio{padding:12px}}
</style>
