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
const blockOptions=[['home','Hero / Главная'],['header','Header'],['about','О компании'],['services','Услуги'],['benefits','Преимущества'],['contacts','Контакты'],['footer','Footer']]
const targetBlock=ref('home'), blockInstruction=ref(''), upgradeMotion=ref(true), compareVersion=ref('candidate')
const blockEdit=computed(()=>current.value?.block_edit)
const editingBlock=computed(()=>['queued','running'].includes(blockEdit.value?.status))
const candidateReady=computed(()=>blockEdit.value?.status==='complete'&&blockEdit.value?.decision==='pending')
const blockPhaseNames={queued:'В очереди',preparing:'Подготовка',generating:'ИИ редактирует выбранный блок',building:'Сборка новой версии',auditing:'Проверка в Chromium',finalizing:'Сохранение результата'}
const blockStep=computed(()=>({queued:0,preparing:0,generating:1,building:2,auditing:3,finalizing:4})[blockEdit.value?.stage]??0)
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
function projectStatus(p){return p.engine!=='cinematic'?'Quick / макет':({complete:'Готов',failed:'Ошибка',queued:'В очереди',running:'В работе'})[p.generation_status]||'—'}
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

function open(id){showPrompt.value=false;targetBlock.value='home';blockInstruction.value='';upgradeMotion.value=true;compareVersion.value='candidate';run(async()=>apply((await http.get(base+id+'/')).data))}
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
  <header class="studio-head"><div><small class="eyebrow">TRACKNODE / AI WORKSPACE</small><h1>Studio</h1><p>От идеи до готового сайта.</p></div><span class="badge"><i :class="{online:config.cinematic_enabled}"/>{{config.cinematic_enabled?'Cinematic настроен':'Проверка движка'}}</span></header>
  <div v-if="error" role="alert" class="notice error">{{error}}</div>
  <div class="project-strip">
    <div class="section-heading"><span>Мои проекты <small>{{projects.length}}</small></span><button class="primary compact" :disabled="busy" @click="newProject()">+ Новый проект</button></div>
    <div v-if="projects.length" class="projects">
      <button v-for="p in projects" :key="p.id" :disabled="busy" :class="{active:current?.id===p.id}" @click="open(p.id)"><span class="project-name">{{p.name}}</span><small :class="['project-state',p.generation_status]">{{p.engine==='cinematic'?'Cinema · ':''}}{{projectStatus(p)}}</small></button>
    </div>
    <p v-else class="muted">Здесь появятся созданные сайты.</p>
  </div>

  <form v-if="!current" class="panel create-form" @submit.prevent="create">
    <div class="form-heading"><span class="eyebrow">НОВЫЙ ПРОЕКТ</span><h2>Расскажите о своей идее</h2><p class="muted">Движок сам разработает композицию, подберёт материалы и создаст сайт.</p></div>
    <div class="choice-grid"><label>Движок<select v-model="engine"><option value="cinematic">Cinematic — полный сайт</option><option value="quick">Quick — старый макет без фото и 3D</option></select></label><label>Стиль<select v-model="style"><option v-for="s in styles" :key="s[0]" :value="s[0]">{{s[1]}}</option></select></label></div>
    <label>Название<input v-model="name" required maxlength="120" placeholder="Например, NOIR CHRONOS"></label>
    <label>Описание<textarea v-model="prompt" required maxlength="8000" rows="6" placeholder="Опишите бизнес, аудиторию, настроение и нужные разделы."></textarea><small class="field-count">{{prompt.length}} / 8000</small></label>
    <template v-if="engine==='cinematic'">
      <fieldset class="contact-fields"><legend>Контактная группа</legend><p class="muted">Укажите публичные контакты бизнеса. Они будут добавлены в раздел «Контакты» и футер готового сайта. Не вводите личные или закрытые данные.</p>
        <label class="check"><input v-model="noContacts" type="checkbox" data-testid="no-contacts"> Без контактов (демонстрационный сайт)</label>
        <div v-if="!noContacts" class="choice-grid"><label v-for="field in contactFields" :key="field[0]">{{field[1]}}<input v-model="contacts[field[0]]" :type="field[2]" :placeholder="field[3]" :maxlength="field[0]==='phone'?32:field[0]==='email'?180:250" :data-testid="'contact-'+field[0]"></label></div>
        <p v-if="!noContacts&&!hasContacts" class="muted">Заполните хотя бы одно поле.</p>
      </fieldset>
      <details class="advanced"><summary>Дополнительные настройки <span>Hero и 3D</span></summary>
        <div class="choice-grid"><label>Hero<select v-model="heroMode"><option v-for="h in heroModes" :key="h[0]" :value="h[0]">{{h[1]}}</option></select></label><label>Стиль ассета<select v-model="assetStyle"><option value="realistic">Реалистичный</option><option value="stylized">Стилизованный</option></select></label></div>
        <label class="check"><input v-model="requireModel" type="checkbox"> Остановить генерацию, если подходящая модель Sketchfab не найдена.</label>
      </details>
      <p class="muted">Sketchfab проверяется автоматически. Если подходящей модели нет, по умолчанию используются фотографии.</p>
      <div class="cost-note">Оценочный бюджет OpenHands — <strong>&#36;{{Number(config.cinematic_max_cost_usd).toFixed(2)}}</strong> за запуск. Preflight и Visual Critic оплачиваются отдельно. Автоматических платных повторов нет.</div>
      <p v-if="activeJob" class="notice">У вас уже выполняется генерация. Откройте её в списке проектов.</p>
    </template>
    <p v-if="engine==='quick'" class="cost-note">Quick — текстовый макет с геометрическими заглушками, без Sketchfab и Three.js.</p>
    <p v-if="engine==='cinematic'&&!config.cinematic_enabled" class="notice error">Cinematic недоступен. Подмена макетом не выполняется.</p>
    <button class="primary launch" :disabled="busy||(engine==='cinematic'?(!config.cinematic_enabled||activeJob):!config.configured)">{{busy?'Отправляем запрос…':engine==='cinematic'?'Запустить Cinematic Engine':'Создать быструю концепцию'}}</button>
  </form>

  <div v-else class="workspace">
    <aside class="panel project-info">
      <span class="eyebrow">{{cinematic?'CINEMATIC PROJECT':'LEGACY PROJECT'}}</span><h2>{{current.name}}</h2>
      <div class="status-card" :class="current.generation_status"><strong>{{cinematic?(current.generation_status==='complete'?visualLabel:current.generation_status==='failed'?'Генерация остановлена':current.generation_status==='running'?'Создаём ваш сайт':'Задание в очереди'):'Quick — старый макет'}}</strong>
        <small v-if="cinematic&&current.generation_status==='complete'&&visualReview.score!==null">Visual Critic: {{visualReview.score}} / 100 · цель {{visualReview.threshold}}</small>
      </div>
      <p v-if="current.generation_error" class="error diagnostic">{{current.generation_error}}</p>
      <p v-if="cinematic&&current.generation_status==='complete'&&visualReview.status!=='passed'" class="muted">Сайт доступен для просмотра; премиальная оценка не подтверждена.</p>
      <div class="brief"><div class="section-heading"><span>Описание проекта</span><button class="text-button" :aria-expanded="showPrompt" @click="showPrompt=!showPrompt">{{showPrompt?'Свернуть':'Читать'}}</button></div><p :class="['brief-text',{expanded:showPrompt}]">{{current.prompt}}</p><small class="muted">{{current.prompt.length}} символов</small></div>
      <div v-if="cinematic&&Object.keys(current.contacts||{}).length" class="brief"><span class="eyebrow">КОНТАКТЫ ПРОЕКТА</span><p v-for="field in contactFields.filter(f=>current.contacts?.[f[0]])" :key="field[0]" class="contact-summary"><strong>{{field[1]}}</strong><br>{{current.contacts[field[0]]}}</p></div>
      <template v-if="!cinematic"><button class="primary" :disabled="busy" @click="newProject(current)">Создать Cinema-сайт</button><h3>История изменений</h3><div class="revision-list"><button v-for="r in current.revisions" :key="r.id" :disabled="busy" :class="{active:r.id===selected}" @click="selected=r.id">{{r.instruction}}</button></div><form @submit.prevent="edit"><label>Изменение<textarea v-model="instruction" required maxlength="8000" rows="3" placeholder="Например: сделай тёмный дизайн"></textarea></label><button :disabled="busy||!config.configured||!revision">Создать версию</button></form></template>
      <div v-else-if="cinematic&&current.generation_status==='complete'" class="block-editor">
        <div class="section-heading"><span>Редактирование блоков</span><small>AI</small></div>
        <p v-if="!current.source_archive_available" class="muted">Для правки нужен сохранённый исходный ZIP.</p>
        <template v-else>
          <div class="block-options"><button v-for="b in blockOptions" :key="b[0]" type="button" :class="{active:targetBlock===b[0]}" :disabled="busy||editingBlock||candidateReady" @click="targetBlock=b[0]">{{b[1]}}</button></div>
          <form v-if="!editingBlock&&!candidateReady" @submit.prevent="submitBlock">
            <label>Что изменить?<textarea v-model="blockInstruction" required maxlength="4000" rows="5" placeholder="Например: сделай заголовок читаемым, увеличь поворот модели. Остальное сохрани."></textarea></label>
            <label v-if="targetBlock==='home'" class="check"><input v-model="upgradeMotion" type="checkbox"> Обновить движок поворота Hero</label>
            <p class="muted">Один платный запрос к DeepSeek, без нового поиска ассетов и автоматических повторов.</p>
            <button type="submit" class="primary" :disabled="busy||activeJob||!config.cinematic_enabled||!blockInstruction.trim()">Перегенерировать блок</button>
          </form>
          <div v-if="editingBlock" role="status" class="notice"><strong>{{blockPhaseNames[blockEdit.stage]||'Выполняется правка'}}</strong><div class="progress-track"><span :style="{width:blockStep/5*100+'%'}"/></div><small>{{blockStep}} из 5 этапов · исходный сайт доступен</small><p class="muted">{{pollingLabel}}<br>Последнее событие: {{blockEdit.updated_at?formatDuration(now-Date.parse(blockEdit.updated_at))+' назад':'—'}}</p></div>
          <div v-if="blockEdit?.status==='failed'" class="notice error">Правка не завершилась. Исходный сайт сохранён.<p class="diagnostic">{{blockEdit.error}}</p></div>
          <div v-if="candidateReady" class="notice"><strong>Новый вариант собран</strong><p class="muted">Сравните с исходником. Визуальный критик не запускался.</p><div class="decision-actions"><button :class="{active:compareVersion==='original'}" @click="compareVersion='original'">До</button><button :class="{active:compareVersion==='candidate'}" @click="compareVersion='candidate'">После</button><button class="primary" :disabled="busy" @click="decideBlock(blockEdit.id,'accept')">Принять</button><button :disabled="busy" @click="decideBlock(blockEdit.id,'discard')">Отклонить</button></div></div>
          <details v-if="current.block_edits?.length" class="block-history"><summary>История правок</summary><article v-for="e in current.block_edits" :key="e.id"><strong>{{blockOptions.find(b=>b[0]===e.block)?.[1]||e.block}}</strong><small>{{({pending:e.status==='failed'?'Ошибка':e.status==='complete'?'Готов к просмотру':'В работе',accepted:'Принято',discarded:'Отклонено',rolled_back:'Отменено'})[e.decision]}}</small><p class="brief-text">{{e.instruction}}</p><button v-if="e.decision==='accepted'&&current.preview_version===e.candidate_run" :disabled="busy||editingBlock||candidateReady" @click="decideBlock(e.id,'rollback')">Откатить версию</button></article></details>
        </template>
      </div>
      <div v-else-if="generating" class="muted small-info">Можно закрыть страницу: задача выполняется локально независимо от браузера. Повторно запускать её не нужно.</div>
    </aside>
    <main class="panel preview-panel">
      <div class="toolbar"><div class="devices"><button :class="{active:device==='100%'}" :aria-pressed="device==='100%'" @click="device='100%'">Компьютер</button><button :class="{active:device==='390px'}" :aria-pressed="device==='390px'" @click="device='390px'">Телефон</button></div><div class="actions"><button v-if="cinematic" :disabled="!previewSrc" @click="openPreview">Открыть отдельно ↗</button><button v-else :disabled="busy||!revision" @click="publish">Утвердить локально</button><button :disabled="busy||(cinematic?(!previewSrc||!current.source_archive_available):!revision)" @click="download">{{candidateReady?'ZIP действующей версии':'Скачать ZIP'}}</button></div></div>
      <div v-if="cinematic&&generating" class="waiting">
        <div class="progress-head"><div><span class="eyebrow">ГЕНЕРАЦИЯ САЙТА</span><h2>{{current.generation_status==='queued'?'В очереди':phaseIndex>=0?phases[phaseIndex]?.[1]:'Создание сайта'}}</h2></div><span class="elapsed">{{elapsed}}</span></div>
        <div v-if="progressKnown" class="progress-track" role="progressbar" aria-label="Завершённые этапы" :aria-valuenow="completedSteps" aria-valuemin="0" :aria-valuemax="phases.length"><span :style="{width:(completedSteps/phases.length*100)+'%'}"/></div>
        <div v-else class="progress-track indeterminate" role="progressbar" aria-label="Выполнение без детализации"><span/></div>
        <p class="muted">{{progressKnown?completedSteps+' из '+phases.length+' этапов завершено':'Старый worker не передаёт подробные этапы.'}} · не оценка оставшегося времени</p>
        <ol class="phase-list"><li v-for="(phase,index) in phases" :key="phase[0]" :class="{done:phaseIndex>index,working:phaseIndex===index}"><span class="phase-dot"><template v-if="phaseIndex>index">✓</template><template v-else>{{index+1}}</template></span><div><strong>{{phase[1]}}</strong><small>{{phase[2]}}</small></div><span v-if="phaseIndex===index" class="phase-live">В работе</span></li></ol>
        <div class="connection" role="status"><span :class="{error:pollError}">{{pollingLabel}}</span><span v-if="current.generation_event_at">Последняя смена этапа: {{eventAge}} назад</span><span v-else>Время последнего события пока недоступно.</span></div>
        <p v-if="oldEvent&&!pollError" class="notice">Этап давно не менялся. Возможен длительный запрос к AI или обработка модели; связь с API не подтверждает активность агента.</p>
      </div>
      <div v-else-if="cinematic&&previewSrc" class="preview-frame"><iframe title="Кинематографический предпросмотр сайта" :key="previewKey" sandbox="allow-scripts allow-same-origin" :src="previewSrc" :style="{width:device,maxWidth:'100%'}"/></div>
      <div v-else-if="!cinematic&&revision" class="preview-frame"><iframe title="Предпросмотр сайта" sandbox="" :srcdoc="previewHtml" :style="{width:device,maxWidth:'100%'}"/></div>
      <div v-else class="empty-preview"><h2>{{current.generation_status==='failed'?'Генерация не завершилась':'Предпросмотр недоступен'}}</h2><p class="muted">Проверьте статус проекта. Диагностические данные сохраняются локально.</p></div>
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
</style>
