<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import http from '../api/http'
import { BACKEND_URL } from '../config/env'

const projects=ref([]), current=ref(null), name=ref(''), prompt=ref(''), instruction=ref(''), selected=ref(null), busy=ref(false), error=ref(''), device=ref('100%')
const engine=ref('cinematic'), style=ref('auto'), assetStyle=ref('realistic'), heroMode=ref('auto'), requireModel=ref(false)
const base='/api/studio/projects/'
const emptyContacts=()=>({phone:'',email:'',address:'',telegram:'',vk:'',whatsapp:'',website:''})
const contacts=ref(emptyContacts()), noContacts=ref(false)
const contactFields=[['phone','Телефон','tel','+7 (___) ___-__-__'],['email','Email','email','info@example.com'],['address','Адрес','text','Город, улица, дом'],['telegram','Telegram','url','https://t.me/...'],['vk','ВКонтакте','url','https://vk.com/...'],['whatsapp','WhatsApp','url','https://wa.me/...'],['website','Сайт','url','https://example.com']]
const hasContacts=computed(()=>Object.values(contacts.value).some(v=>v.trim()))
const config=ref({provider:null,configured:false,cinematic_enabled:false,cinematic_max_cost_usd:2.5})
const styles=[['auto','Автоматический'],['business','Современный'],['cinema','Кинематографический']]
const heroModes=[['auto','Автовыбор композиции'],['immersive','Крупный объект на фоне'],['product','Предметная сцена'],['split','Разделённый Hero'],['cinematic','Полноэкранная сцена'],['editorial','Editorial-фотография'],['environment','Иммерсивное пространство']]
const revision=computed(()=>current.value?.revisions?.find(r=>r.id===selected.value))
const previewHtml=computed(()=>revision.value?.html.replaceAll('href="#page-', 'href="about:srcdoc#page-') || '')
const blockOptions=[['home','Главная'],['header','Шапка'],['about','О компании'],['services','Услуги'],['benefits','Преимущества'],['contacts','Контакты'],['footer','Подвал']]
const inspectorTab=ref('edit')
const targetBlock=ref('home'), blockInstruction=ref(''), upgradeMotion=ref(true), compareVersion=ref('candidate')
const blockEdit=computed(()=>current.value?.block_edit)
const editingBlock=computed(()=>['queued','running'].includes(blockEdit.value?.status))
const candidateReady=computed(()=>blockEdit.value?.status==='complete'&&blockEdit.value?.decision==='pending')
const blockPhaseNames={queued:'В очереди',preparing:'Подготовка',read_job:'Проверка задания',read_archive:'Чтение исходного сайта',generating:'Подготовка новой версии блока',ai_request:'ИИ редактирует выбранный блок',decode_response:'Получение ответа ИИ',decode_patch:'Обработка изменений',validate_patch:'Проверка безопасности изменений',write_archive:'Сохранение новой версии',building:'Сборка новой версии',auditing:'Проверка сайта',finalizing:'Сохранение результата'}
const blockStages=['queued','preparing','read_job','read_archive','generating','ai_request','decode_response','decode_patch','validate_patch','write_archive','building','auditing','finalizing']
const blockStep=computed(()=>Math.max(0,blockStages.indexOf(blockEdit.value?.stage)))
const blockProgress=computed(()=>blockEdit.value?.status==='complete'?100:Math.min(96,Math.round((blockStep.value/(blockStages.length-1))*100)))
const blockEventAge=computed(()=>formatDuration(now.value-Date.parse(blockEdit.value?.updated_at||blockEdit.value?.created_at||'')))
const blockEventStale=computed(()=>!!blockEdit.value?.updated_at&&now.value-Date.parse(blockEdit.value.updated_at)>180000)
const previewSrc=computed(()=>{
  const path=candidateReady.value&&compareVersion.value==='candidate'?blockEdit.value.preview_path:current.value?.preview_path
  if(!path)return ''
  return BACKEND_URL+path
})
const previewKey=computed(()=>previewSrc.value+'|'+(current.value?.preview_version||''))
function submitBlock(){run(async()=>{
  const id=current.value.id
  apply((await http.post(base+id+'/blocks/'+targetBlock.value+'/regenerate/',{instruction:blockInstruction.value,upgrade_motion:targetBlock.value==='home'&&upgradeMotion.value})).data)
  compareVersion.value='candidate';blockInstruction.value='';await refresh()
})}
function applyHeroFilm(){run(async()=>{
  apply((await http.post(base+current.value.id+'/blocks/home/regenerate/',{instruction:'Full-screen two-act Hero film',local_hero_film:true,upgrade_motion:true})).data)
  compareVersion.value='candidate';await refresh()
})}
function decideBlock(editId,action){run(async()=>{
  apply((await http.post(base+current.value.id+'/block-edits/'+editId+'/'+action+'/')).data)
  compareVersion.value='candidate';await refresh()
})}
const cinematic=computed(()=>current.value?.engine==='cinematic')
const generating=computed(()=>['queued','running'].includes(current.value?.generation_status))
const visualReview=computed(()=>current.value?.visual_review || {status:'unverified',score:null,threshold:85})
const visualLabel=computed(()=>({passed:'Технически проверен · премиальная оценка пройдена',needs_revision:'Сайт готов к просмотру · дизайн требует улучшения',unavailable:'Сайт готов к просмотру · критик недоступен',skipped:'Сайт готов к просмотру · визуальная оценка пропущена',unverified:'Сайт готов к просмотру · премиальность не подтверждена'})[visualReview.value.status])

async function run(fn){if(busy.value)return;busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.response?.data?.detail||'Не удалось выполнить операцию. Проверьте локальную Studio.'}finally{busy.value=false}}
function apply(project){const same=current.value?.id===project.id;current.value=project;if(!same||!project.revisions?.some(r=>r.id===selected.value))selected.value=project.revisions?.[0]?.id||null}

const phases=[
  ['preparing','Подготовка среды','Проверка контейнеров и инструментов'],
  ['assets','Арт-дирекция и материалы','Поиск Sketchfab, проверка моделей и ракурсов'],
  ['generating','Создание сайта','OpenHands пишет компоненты и анимации'],
  ['building','Сборка проекта','Компиляция Vue и локальных ресурсов'],
  ['auditing','Браузерная проверка','Chromium проверяет desktop и mobile'],
  ['visual-review','Визуальная оценка','Критик оценивает композицию'],
  ['finalizing','Сохранение результата','Подготовка предпросмотра и ZIP']
]
const now=ref(Date.now()), lastPoll=ref(null), pollError=ref(false), showPrompt=ref(false)
const activeJob=computed(()=>projects.value.some(p=>['queued','running'].includes(p.generation_status)||['queued','running'].includes(p.block_edit?.status)))
const phaseIndex=computed(()=>current.value?.generation_status==='complete'?phases.length:phases.findIndex(p=>p[0]===current.value?.generation_stage))
const progressKnown=computed(()=>phaseIndex.value>=0||current.value?.generation_status==='queued')
const completedSteps=computed(()=>Math.max(0,phaseIndex.value))
const elapsed=computed(()=>formatDuration(now.value-Date.parse(current.value?.created_at||'')))
const eventAge=computed(()=>formatDuration(now.value-Date.parse(current.value?.generation_event_at||'')))
const oldEvent=computed(()=>current.value?.generation_event_at && now.value-Date.parse(current.value.generation_event_at)>180000)
const pollingLabel=computed(()=>pollError.value?'Связь с API прервана — повторяем запрос':lastPoll.value?'API обновлён '+formatDuration(now.value-lastPoll.value)+' назад':'Ожидаем первый ответ API')
function formatDuration(ms){if(!Number.isFinite(ms))return '—';const s=Math.max(0,Math.floor(ms/1000));return Math.floor(s/60)+' мин '+String(s%60).padStart(2,'0')+' сек'}
function projectStatus(p){return p.engine!=='cinematic'?'Макет':({complete:'Готов',failed:'Ошибка',queued:'В очереди',running:'В работе'})[p.generation_status]||'—'}
let polling=false,disposed=false
async function refresh(){
  if(polling||disposed)return
  polling=true
  try{
    const list=(await http.get(base)).data
    if(disposed)return
    projects.value=list
    const id=current.value?.id
    if(id&&list.some(p=>p.id===id)){
      const detail=(await http.get(base+id+'/')).data
      if(!disposed&&current.value?.id===id)apply(detail)
    }
    lastPoll.value=Date.now();pollError.value=false
  }catch(e){pollError.value=true;throw e}
  finally{polling=false}
}
onMounted(()=>run(async()=>{config.value=(await http.get('/api/studio/config/')).data;await refresh()}))
const poll=setInterval(()=>{if(!busy.value&&(activeJob.value||generating.value||editingBlock.value||pollError.value))refresh().catch(()=>{})},3000)
const clock=setInterval(()=>{now.value=Date.now()},1000)
onBeforeUnmount(()=>{disposed=true;clearInterval(poll);clearInterval(clock)})

function open(id){inspectorTab.value='edit';showPrompt.value=false;targetBlock.value='home';blockInstruction.value='';upgradeMotion.value=true;compareVersion.value='candidate';run(async()=>apply((await http.get(base+id+'/')).data))}
function newProject(from=null){
  engine.value='cinematic';style.value='auto';assetStyle.value='realistic';heroMode.value='auto';requireModel.value=false
  name.value=from?from.name+' — Cinema':''
  name.value=name.value.slice(0,120)
  prompt.value=from?.prompt||''
  contacts.value={...emptyContacts(),...from?.contacts};noContacts.value=false
  current.value=null;selected.value=null;error.value='';showPrompt.value=false
}
function create(){if(engine.value==='cinematic'&&activeJob.value)return;if(engine.value==='cinematic'&&!hasContacts.value&&!noContacts.value){error.value='Укажите хотя бы один публичный контакт или выберите «Без контактов». ';return}run(async()=>{
  const payload={name:name.value,prompt:prompt.value,style:style.value,engine:engine.value,asset_style:assetStyle.value,hero_mode:heroMode.value,require_model:requireModel.value,contacts:engine.value==='cinematic'&&!noContacts.value?Object.fromEntries(Object.entries(contacts.value).filter(([,v])=>v.trim())):{}}
  apply((await http.post(base,payload,{timeout:engine.value==='cinematic'?15000:105000})).data)
  showPrompt.value=false;await refresh();name.value='';prompt.value='';contacts.value=emptyContacts();noContacts.value=false
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
  <header class="studio-head"><h1>Studio</h1><button class="primary compact" :disabled="busy" @click="newProject()">+ Новый проект</button></header>
  <div v-if="error" role="alert" class="notice error">{{error}}</div>
  <div class="project-strip">
    <div class="section-heading"><span>Мои проекты <small>{{projects.length}}</small></span></div>
    <div v-if="projects.length" class="projects">
      <button v-for="p in projects" :key="p.id" :disabled="busy" :class="{active:current?.id===p.id}" @click="open(p.id)"><span class="project-name">{{p.name}}</span><small :class="['project-state',p.generation_status]">{{projectStatus(p)}}</small></button>
    </div>
    <p v-else class="muted">Здесь появятся созданные сайты.</p>
  </div>

  <form v-if="!current" class="panel create-form" @submit.prevent="create">
    <div class="form-heading"><span class="eyebrow">НОВЫЙ ПРОЕКТ</span><h2>Расскажите о своей идее</h2><p class="muted">Движок сам разработает композицию, подберёт материалы и создаст сайт.</p></div>
    <div class="choice-grid"><label>Тип сайта<select v-model="engine"><option value="cinematic">Полноценный сайт</option><option value="quick">Быстрый макет</option></select></label><label>Стиль<select v-model="style"><option v-for="s in styles" :key="s[0]" :value="s[0]">{{s[1]}}</option></select></label></div>
    <label>Название<input v-model="name" required maxlength="120" placeholder="Например, NOIR CHRONOS"></label>
    <label>Описание<textarea v-model="prompt" required maxlength="8000" rows="6" placeholder="Опишите бизнес, аудиторию, настроение и нужные разделы."></textarea><small class="field-count">{{prompt.length}} / 8000</small></label>
    <template v-if="engine==='cinematic'">
      <fieldset class="contact-fields"><legend>Контакты бизнеса</legend><p class="muted">Укажите публичные контакты бизнеса. Они будут добавлены в раздел «Контакты» и футер готового сайта. Не вводите личные или закрытые данные.</p>
        <label class="check"><input v-model="noContacts" type="checkbox" data-testid="no-contacts"> Без контактов (демонстрационный сайт)</label>
        <div v-if="!noContacts" class="choice-grid"><label v-for="field in contactFields" :key="field[0]">{{field[1]}}<input v-model="contacts[field[0]]" :type="field[2]" :placeholder="field[3]" :maxlength="field[0]==='phone'?32:field[0]==='email'?180:250" :data-testid="'contact-'+field[0]"></label></div>
        <p v-if="!noContacts&&!hasContacts" class="muted">Заполните хотя бы одно поле.</p>
      </fieldset>
      <details class="advanced"><summary>Дополнительные настройки <span>Композиция</span></summary>
        <div class="choice-grid"><label>Первый экран<select v-model="heroMode"><option v-for="h in heroModes" :key="h[0]" :value="h[0]">{{h[1]}}</option></select></label><label>Стиль изображений<select v-model="assetStyle"><option value="realistic">Реалистичный</option><option value="stylized">Стилизованный</option></select></label></div>
        <label class="check"><input v-model="requireModel" type="checkbox"> Обязательно использовать 3D-модель.</label>
      </details>
      
      <div class="cost-note">Бюджет генерации — <strong>&#36;{{Number(config.cinematic_max_cost_usd).toFixed(2)}}</strong>. Подбор материалов и оценка дизайна оплачиваются отдельно.</div>
      <p v-if="activeJob" class="notice">У вас уже выполняется генерация. Откройте её в списке проектов.</p>
    </template>
    <p v-if="engine==='quick'" class="cost-note">Быстрый макет без фотографий и 3D.</p>
    <p v-if="engine==='cinematic'&&!config.cinematic_enabled" class="notice error">Создание полноценных сайтов временно недоступно.</p>
    <button class="primary launch" :disabled="busy||(engine==='cinematic'?(!config.cinematic_enabled||activeJob):!config.configured)">{{busy?'Отправляем запрос…':engine==='cinematic'?'Создать сайт':'Создать быструю концепцию'}}</button>
  </form>

  <div v-else class="workspace">
    <aside class="panel project-info">
      <div class="inspector-heading"><h2>{{current.name}}</h2><span class="project-state" :class="current.generation_status">{{projectStatus(current)}}</span></div>
      <div v-if="cinematic" class="inspector-tabs" aria-label="Панель проекта">
        <button type="button" :class="{active:inspectorTab==='edit'}" :aria-pressed="inspectorTab==='edit'" @click="inspectorTab='edit'">Редактор</button>
        <button type="button" :class="{active:inspectorTab==='info'}" :aria-pressed="inspectorTab==='info'" @click="inspectorTab='info'">О проекте</button>
      </div>
      <p v-if="current.generation_status==='failed'" class="notice error">Не удалось создать сайт.</p>
      <div v-if="!cinematic||inspectorTab==='info'" class="project-details">
        <details class="brief"><summary>Описание проекта</summary><p class="project-description">{{current.prompt}}</p></details>
        <details v-if="cinematic&&Object.keys(current.contacts||{}).length" class="brief"><summary>Контакты</summary><p v-for="field in contactFields.filter(f=>current.contacts?.[f[0]])" :key="field[0]" class="contact-summary"><strong>{{field[1]}}</strong><br>{{current.contacts[field[0]]}}</p></details>
      </div>
      <template v-if="!cinematic"><button class="primary" :disabled="busy" @click="newProject(current)">Создать полноценный сайт</button><h3>История изменений</h3><div class="revision-list"><button v-for="r in current.revisions" :key="r.id" :disabled="busy" :class="{active:r.id===selected}" @click="selected=r.id">{{r.instruction}}</button></div><form @submit.prevent="edit"><label>Изменение<textarea v-model="instruction" required maxlength="8000" rows="3" placeholder="Например: сделай тёмный дизайн"></textarea></label><button :disabled="busy||!config.configured||!revision">Создать версию</button></form></template>
      <div v-else-if="cinematic&&current.generation_status==='complete'" v-show="inspectorTab==='edit'||candidateReady||editingBlock" class="block-editor">
        <div class="section-heading"><span>Редактирование блоков</span></div>
        <p v-if="!current.source_archive_available" class="muted">Для правки нужен сохранённый исходный ZIP.</p>
        <template v-else>
          <div class="block-options"><button v-for="b in blockOptions" :key="b[0]" type="button" :class="{active:targetBlock===b[0]}" :disabled="busy||editingBlock||candidateReady" @click="targetBlock=b[0]">{{b[1]}}</button></div>
          <form v-if="!editingBlock&&!candidateReady" @submit.prevent="submitBlock">
            
            <label>Что изменить?<textarea v-model="blockInstruction" required maxlength="4000" rows="3" placeholder="Опишите, что хотите изменить…"></textarea></label>
            <details v-if="targetBlock==='home'" class="advanced editor-advanced"><summary>Настройки анимации</summary><label class="check"><input v-model="upgradeMotion" type="checkbox"> Обновить анимацию</label><button type="button" :disabled="busy||activeJob||!config.cinematic_enabled" @click="applyHeroFilm">Обновить киносцену</button></details>
            <p class="request-note">Используется один платный запрос.</p>
            <button type="submit" class="primary" :disabled="busy||activeJob||!config.cinematic_enabled||!blockInstruction.trim()">Применить изменения</button>
          </form>
          <div v-if="editingBlock" role="status" class="notice block-live-status"><div class="block-live-heading"><strong>{{blockPhaseNames[blockEdit.stage]||'Выполняется правка'}}</strong><span>{{blockProgress}}%</span></div><div class="progress-track"><span :style="{width:blockProgress+'%'}"/></div><small>Последнее подтверждение движка: {{blockEventAge}} назад. Статус обновляется автоматически.</small><p v-if="blockEventStale" class="block-stale">Движок пока не сообщил новый этап. Проверяем выполнение — не запускайте повторную правку.</p></div>
          <div v-if="blockEdit?.status==='failed'" class="notice error">Правка не завершилась. Исходный сайт сохранён.</div>
          <div v-if="candidateReady" class="notice"><strong>Новый вариант собран</strong><p class="muted">Сравните версии перед сохранением.</p><div class="decision-actions"><button :class="{active:compareVersion==='original'}" @click="compareVersion='original'">До</button><button :class="{active:compareVersion==='candidate'}" @click="compareVersion='candidate'">После</button><button class="primary" :disabled="busy" @click="decideBlock(blockEdit.id,'accept')">Принять</button><button :disabled="busy" @click="decideBlock(blockEdit.id,'discard')">Отклонить</button></div></div>
          <details v-if="current.block_edits?.length" class="block-history"><summary>История правок</summary><article v-for="e in current.block_edits" :key="e.id"><strong>{{blockOptions.find(b=>b[0]===e.block)?.[1]||e.block}}</strong><small>{{({pending:e.status==='failed'?'Ошибка':e.status==='complete'?'Готов к просмотру':'В работе',accepted:'Принято',discarded:'Отклонено',rolled_back:'Отменено'})[e.decision]}}</small><p class="brief-text">{{e.instruction}}</p><button v-if="e.decision==='accepted'&&current.preview_version===e.candidate_run" :disabled="busy||editingBlock||candidateReady" @click="decideBlock(e.id,'rollback')">Откатить версию</button></article></details>
        </template>
      </div>
      <div v-else-if="generating" class="muted small-info">Можно закрыть страницу — создание продолжится.</div>
    </aside>
    <main class="panel preview-panel">
      <div class="toolbar"><div class="devices"><button :class="{active:device==='100%'}" :aria-pressed="device==='100%'" @click="device='100%'" aria-label="Компьютер" title="Компьютер"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="13" rx="2"/><path d="M12 16v5m-4 0h8"/></svg></button><button :class="{active:device==='390px'}" :aria-pressed="device==='390px'" @click="device='390px'" aria-label="Телефон" title="Телефон"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg></button></div><div class="actions"><button v-if="cinematic" :disabled="!previewSrc" @click="openPreview">Открыть ↗</button><button v-else :disabled="busy||!revision" @click="publish">Утвердить локально</button><button :disabled="busy||(cinematic?(!previewSrc||!current.source_archive_available):!revision)" @click="download">{{candidateReady?'ZIP действующей версии':'Скачать ZIP'}}</button></div></div>
      <div v-if="cinematic&&generating" class="waiting">
        <div class="progress-head"><div><span class="eyebrow">ГЕНЕРАЦИЯ САЙТА</span><h2>{{current.generation_status==='queued'?'В очереди':phaseIndex>=0?phases[phaseIndex]?.[1]:'Создание сайта'}}</h2></div><span class="elapsed">{{elapsed}}</span></div>
        <div v-if="progressKnown" class="progress-track" role="progressbar" aria-label="Завершённые этапы" :aria-valuenow="completedSteps" aria-valuemin="0" :aria-valuemax="phases.length"><span :style="{width:(completedSteps/phases.length*100)+'%'}"/></div>
        <div v-else class="progress-track indeterminate" role="progressbar" aria-label="Выполнение без детализации"><span/></div>
        <p v-if="progressKnown" class="muted">{{completedSteps}} из {{phases.length}} этапов завершено</p>
        <ol class="phase-list"><li v-for="(phase,index) in phases" :key="phase[0]" :class="{done:phaseIndex>index,working:phaseIndex===index}"><span class="phase-dot"><template v-if="phaseIndex>index">✓</template><template v-else>{{index+1}}</template></span><div><strong>{{phase[1]}}</strong></div><span v-if="phaseIndex===index" class="phase-live">В работе</span></li></ol>
        <p v-if="pollError" role="status" class="muted">Восстанавливаем соединение…</p>
        <p v-if="oldEvent&&!pollError" class="notice">Этот этап занимает больше времени, чем обычно.</p>
      </div>
      <div v-else-if="cinematic&&previewSrc" class="preview-frame"><iframe title="Кинематографический предпросмотр сайта" :key="previewKey" sandbox="allow-scripts allow-same-origin" :src="previewSrc" :style="{width:device,maxWidth:'100%'}"/></div>
      <div v-else-if="!cinematic&&revision" class="preview-frame"><iframe title="Предпросмотр сайта" sandbox="" :srcdoc="previewHtml" :style="{width:device,maxWidth:'100%'}"/></div>
      <div v-else class="empty-preview"><h2>{{current.generation_status==='failed'?'Генерация не завершилась':'Предпросмотр недоступен'}}</h2><p class="muted">Предпросмотр появится после создания сайта.</p></div>
    </main>
  </div>
</section>
</template>

<style scoped>
.block-editor{border-top:1px solid var(--line);margin-top:16px;padding-top:16px}.block-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;margin:12px 0}.block-options button{padding:8px;font-size:12px}.block-editor form>button{width:100%}.block-editor .decision-actions{display:grid;grid-template-columns:1fr 1fr;gap:6px}.block-history{margin-top:14px;font-size:12px}.block-history summary{cursor:pointer;color:var(--muted)}.block-history article{border-top:1px solid var(--line);padding:10px 0}.block-history small{display:block;color:var(--muted);margin-top:4px}
.contact-fields{min-width:0;border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:16px 0}.contact-fields legend{font-size:14px;font-weight:650;padding:0 6px}.contact-summary{font-size:12px;line-height:1.55;color:var(--muted);overflow-wrap:anywhere}.contact-summary strong{color:inherit}
.studio{--line:#344153;--muted:#9baac0;--accent:#698dff;--panel:#111a28;padding:24px clamp(12px,2vw,28px);max-width:1720px;margin:auto;color:inherit;min-width:0}
.studio-head,.section-heading,.toolbar,.progress-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.studio-head{margin-bottom:20px}.studio h1{font-size:36px;line-height:1.15;font-weight:750;letter-spacing:-.045em;margin:5px 0}.studio h2{font-size:22px;line-height:1.3;font-weight:650;overflow-wrap:anywhere}.studio h3{font-size:14px;font-weight:650;margin-top:20px}.studio p{margin:8px 0;overflow-wrap:anywhere}.eyebrow{font-size:10px;font-weight:750;letter-spacing:.15em;color:var(--muted)}.muted{color:var(--muted);font-size:13px;line-height:1.65}.badge{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:99px;padding:8px 12px;font-size:12px}.badge i{width:7px;height:7px;background:#64748b;border-radius:50%}.badge i.online{background:#4ade80}
.project-strip{margin-bottom:18px}.section-heading{font-size:13px;font-weight:650}.section-heading small{color:var(--muted);margin-left:5px}.projects{display:flex;gap:8px;overflow-x:auto;padding:10px 1px 4px;scrollbar-width:thin}.projects button{flex:0 0 190px;display:grid;gap:5px;min-width:0}.project-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px}.project-state{font-size:11px;color:var(--muted)}.project-state.complete{color:#86d9b2}.project-state.failed{color:#fb8b9e}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;min-width:0}.create-form{max-width:920px;margin:0 auto;padding:clamp(16px,3vw,30px)}.form-heading{margin-bottom:20px}.form-heading h2{font-size:28px;margin-top:6px;letter-spacing:-.035em}
.studio button{padding:10px 13px;border:1px solid var(--line);border-radius:9px;background:#182335;color:inherit;text-align:left;font-size:13px;overflow-wrap:anywhere;transition:background .15s,border-color .15s}.studio button:hover,.studio button.active{background:#273b5f;border-color:#698dff}.studio button:disabled{opacity:.46;cursor:not-allowed}.studio button.primary{background:#315ee7;border-color:#4f75ef;color:white;font-weight:650;text-align:center}.studio button.primary:hover{background:#426df0}.studio button.compact{padding:8px 12px}.studio button.launch{width:100%;padding:14px;margin-top:16px}
.choice-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.studio label{display:block;margin:12px 0;font-size:13px;font-weight:550;min-width:0}.studio input,.studio textarea,.studio select{display:block;width:100%;padding:12px;margin-top:6px;background:#0b1320;color:inherit;border:1px solid var(--line);border-radius:9px;font:inherit}.studio textarea{resize:vertical}.studio input:focus,.studio textarea:focus,.studio select:focus,.studio button:focus-visible,.studio summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}.field-count{display:block;text-align:right;margin-top:5px;color:var(--muted)}.check{display:flex!important;align-items:flex-start;gap:10px;font-weight:400!important}.check input{width:auto;margin-top:3px}.advanced{padding:12px;border:1px solid var(--line);border-radius:10px;margin:12px 0}.advanced summary{cursor:pointer;font-size:13px}.advanced summary span{color:var(--muted);float:right}.cost-note,.notice,.status-card{padding:12px;border:1px solid var(--line);border-radius:10px;font-size:13px;line-height:1.6}.cost-note{background:#0d1624;color:var(--muted)}.notice{margin:10px 0;background:#26324a}.error{color:#ff9aaa}.status-card{margin:14px 0;background:#19273a}.status-card.complete{border-color:#396a59}.status-card.failed{border-color:#8f4356}.status-card small{display:block;color:var(--muted);margin-top:6px}
.workspace{display:grid;grid-template-columns:minmax(0,260px) minmax(0,1fr);gap:14px;align-items:start}.project-info h2{margin-top:7px}.project-info{min-width:0}.brief{border-top:1px solid var(--line);padding-top:14px;margin-top:15px}.studio button.text-button{padding:4px 8px;background:transparent;border-color:transparent;color:#a6bdff}.brief-text{font-size:13px;color:#c2cee0;line-height:1.65;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-wrap}.brief-text.expanded{display:block;max-height:240px;overflow-y:auto;scrollbar-width:thin}.diagnostic{max-height:160px;overflow:auto;font-size:12px}.small-info{border-top:1px solid var(--line);padding-top:12px;margin-top:15px}.revision-list{max-height:200px;overflow:auto}.revision-list button{display:block;width:100%;margin:5px 0;text-overflow:ellipsis;white-space:nowrap;overflow:hidden}
.preview-panel{padding:10px;background:#0b121e}.toolbar{padding:5px 3px 12px}.devices,.actions{display:flex;gap:6px;flex-wrap:wrap}.devices button{border-radius:7px}.preview-frame{background:#070b12;border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;justify-content:center}.studio iframe{height:clamp(430px,72vh,1000px);border:0;display:block;background:#fff;max-width:100%;flex-shrink:1}.waiting{max-width:780px;margin:0 auto;padding:clamp(16px,3vw,38px);min-height:440px}.elapsed{font-variant-numeric:tabular-nums;font-size:13px;color:var(--muted)}.progress-track{height:7px;border-radius:8px;background:#26354b;overflow:hidden;margin-top:20px}.progress-track span{display:block;height:100%;background:#7296ff;border-radius:8px;transition:width .3s ease}.progress-track.indeterminate span{width:30%;animation:travel 1.8s ease-in-out infinite}.phase-list{list-style:none;margin:22px 0;padding:0;display:grid;gap:0}.phase-list li{display:flex;align-items:center;gap:12px;min-height:56px;padding:9px 0;color:var(--muted);border-bottom:1px solid #243144}.phase-list li div{min-width:0;flex:1}.phase-list strong{display:block;font-size:14px;font-weight:600}.phase-list small{display:block;font-size:11px;line-height:1.45;margin-top:3px}.phase-dot{height:27px;width:27px;flex:none;border:1px solid #43536d;border-radius:50%;display:grid;place-items:center;font-size:12px}.phase-list li.done{color:#a1d9c1}.phase-list li.done .phase-dot{border-color:#3c8b70;background:#16392d}.phase-list li.working{color:#e0eaff}.phase-list li.working .phase-dot{border:2px solid #7195ff;box-shadow:0 0 0 4px #7195ff22}.phase-live{font-size:11px;color:#a5bcff;white-space:nowrap}.connection{display:grid;gap:4px;font-size:12px;color:var(--muted)}.empty-preview{padding:50px 16px;text-align:center;min-height:300px}
@keyframes travel{0%{transform:translateX(-100%)}100%{transform:translateX(340%)}}@media(prefers-reduced-motion:reduce){.progress-track span{animation:none;transition:none}.studio button{transition:none}}@media(max-width:1050px){.workspace{grid-template-columns:minmax(0,210px) minmax(0,1fr)}}@media(max-width:800px){.workspace,.choice-grid{grid-template-columns:minmax(0,1fr)}.studio{padding:12px}.studio-head{align-items:flex-start}.studio iframe{height:65vh;min-height:360px}.toolbar{justify-content:flex-start}.waiting{padding:14px}.project-info{padding:14px}.advanced summary span{float:none;display:block;margin-top:5px}}

/* Studio-only product layout. Independent inspector and preview scroll areas. */
.studio{--line:#2c394d;--panel:#111a28;--muted:#a0aec2;--workspace-height:clamp(420px,calc(100dvh - 270px),1100px);padding:18px clamp(12px,2vw,26px);max-width:1800px}
.studio-head{margin-bottom:14px}.studio h1{font-size:30px;margin:0}.project-strip{margin-bottom:14px}
.projects{padding:9px 0 3px;gap:8px}.projects button{flex-basis:174px;padding:10px 12px;border-radius:12px}.projects button.active{box-shadow:inset 0 0 0 1px #698dff66}
.workspace{grid-template-columns:minmax(0,1fr) minmax(250px,300px);grid-template-areas:"preview inspector";gap:12px;align-items:stretch}
.project-info{grid-area:inspector;max-height:var(--workspace-height);overflow:auto;overscroll-behavior:contain;scrollbar-width:thin;padding:15px;min-height:0}
.preview-panel{grid-area:preview;display:flex;flex-direction:column;min-width:0;height:var(--workspace-height);padding:10px;overflow:hidden}
.inspector-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;padding-bottom:12px}.inspector-heading h2{margin:0;font-size:17px;min-width:0}.inspector-heading .project-state{flex-shrink:0}
.inspector-tabs{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px;background:#0b1320;border-radius:10px;margin-bottom:12px}.inspector-tabs button{text-align:center;border-color:transparent;padding:9px 5px}
.block-editor{border:0;margin:0;padding:0}.block-options{gap:6px;margin:10px 0 16px}.block-options button{min-height:38px;overflow-wrap:normal;word-break:normal;text-align:center;padding:7px 4px;font-size:12px}
.studio textarea{min-height:88px;max-height:180px;resize:vertical}.request-note{font-size:11px;color:var(--muted);margin:7px 0!important}.editor-advanced{padding:9px 10px;margin:8px 0}.editor-advanced button{width:100%;margin-top:5px}
.block-live-heading{display:flex;justify-content:space-between;align-items:center;gap:8px}.block-live-heading span{font-variant-numeric:tabular-nums;color:#a5bcff;font-weight:650}.block-live-status small{display:block;color:var(--muted);margin-top:7px}.block-stale{margin:8px 0 0;color:#e8c58a;font-size:12px}.block-history,.brief{border:1px solid var(--line);border-radius:10px;padding:10px;margin:10px 0 0}.block-history summary,.brief summary{cursor:pointer;font-size:13px;font-weight:600;color:inherit}.project-description{white-space:pre-wrap;line-height:1.6;font-size:13px;overflow-wrap:anywhere}
.toolbar{flex:0 0 auto;padding:0 0 10px;gap:8px;justify-content:space-between}.devices{flex-wrap:nowrap;background:#111a28;padding:3px;border-radius:10px}.devices button{display:grid;place-items:center;width:40px;height:36px;padding:7px;border-color:transparent}.devices svg{width:20px;height:20px}.actions{gap:5px}.actions button{padding:8px 10px;font-size:12px}
.preview-frame{flex:1;min-height:0;align-items:stretch;background:#080e18}.studio iframe{height:100%;min-height:0;flex-shrink:1}.waiting,.empty-preview{overflow:auto;min-height:0;max-height:100%;width:100%}.waiting{padding:clamp(12px,2vw,26px)}.phase-list li{min-height:42px}
@media(min-width:901px) and (max-width:1250px){.workspace{grid-template-columns:minmax(0,1fr) minmax(225px,255px)}}
@media(max-width:900px){.workspace{grid-template-columns:minmax(0,1fr);grid-template-areas:"preview" "inspector"}.preview-panel{height:clamp(350px,64dvh,720px)}.project-info{max-height:none;overflow:visible}.studio{padding:12px}.block-options{grid-template-columns:repeat(auto-fit,minmax(100px,1fr))}}
@media(max-width:480px){.studio h1{font-size:25px}.studio-head{gap:8px}.projects button{flex-basis:148px}.preview-panel{padding:6px}.toolbar{gap:5px}.devices button{width:36px;height:34px}.actions button{padding:7px 6px;font-size:11px}.project-info{padding:12px}.preview-panel{height:clamp(320px,60dvh,620px)}}
</style>
