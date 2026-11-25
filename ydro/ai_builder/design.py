"""Bounded design schema: model output is data, never executable code."""
import json
from html import escape
from django.core.exceptions import ValidationError

STYLES = ("auto", "business", "premium", "cinema", "3d")
THEMES = {
    "editorial": ("#f3efe6", "#292621", "#8c513a", "#e7ded0", "Georgia,serif"),
    "dark": ("#11141e", "#f4f0e8", "#b99bff", "#202536", "Georgia,serif"),
    "modern": ("#f5f8fa", "#142b38", "#007c79", "#e3efed", "system-ui,sans-serif"),
    "bold": ("#f7f1dd", "#252337", "#a93c25", "#f0e3bd", "system-ui,sans-serif"),
}
def clean(value, limit, field="text"):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field}: ожидается непустая строка.")
    value = value.strip()
    if len(value) > limit:
        raise ValidationError(f"{field}: превышен лимит {limit} символов.")
    return value

def validate(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("theme"),str) or raw.get("theme") not in THEMES:
        raise ValidationError("Некорректная дизайн-тема.")
    pages = raw.get("pages")
    if not isinstance(pages, list) or not 2 <= len(pages) <= 5:
        raise ValidationError("Нужно от 2 до 5 страниц.")
    result = {"theme":raw["theme"], "brand":clean(raw.get("brand"),120,"brand"), "pages":[]}
    for i, page in enumerate(pages):
        if not isinstance(page,dict):
            raise ValidationError("Некорректная страница.")
        items=page.get("items")
        if not isinstance(items,list) or not 2 <= len(items) <= 5:
            raise ValidationError("Нужно от 2 до 5 блоков.")
        out={"label":clean(page.get("label"),40,f"pages[{i}].label"), "eyebrow":clean(page.get("eyebrow"),80,f"pages[{i}].eyebrow"),
             "heading":clean(page.get("heading"),160,f"pages[{i}].heading"),"intro":clean(page.get("intro"),500,f"pages[{i}].intro"),"items":[]}
        for j, item in enumerate(items):
            if not isinstance(item,dict):
                raise ValidationError("Некорректный блок.")
            out["items"].append({"title":clean(item.get("title"),100,f"pages[{i}].items[{j}].title"),"text":clean(item.get("text"),700,f"pages[{i}].items[{j}].text")})
        result["pages"].append(out)
    return result

def demo_spec(name, prompt, style="auto", instruction="", previous=None):
    # Offline fixture: topic-specific content, not an LLM.
    combined=(name+" "+prompt).lower()
    poet=any(x in combined for x in ("поэт","стих","песен","писател","автор"))
    if previous:
        spec=json.loads(json.dumps(previous,ensure_ascii=False))
    elif poet:
        spec={"theme":"editorial","brand":name,"pages":[
            {"label":"Главная","eyebrow":"Литературный портфель","heading":"Слова, которые остаются","intro":"Пространство для стихов, песен и историй. Здесь слово становится способом услышать себя и мир.","items":[{"title":"Поэзия","text":"Лирика, наблюдения и размышления. Место для авторских произведений."},{"title":"Музыка","text":"Тексты песен и творческие истории."}]},
            {"label":"Творчество","eyebrow":"Избранное","heading":"Между строк","intro":"Коллекция произведений. Автор может заменить эти демонстрационные описания собственными текстами.","items":[{"title":"Стихотворения","text":"Будущая подборка стихов."},{"title":"Песни","text":"Будущая подборка текстов песен."}]},
            {"label":"Об авторе","eyebrow":"Знакомство","heading":"История автора","intro":"Здесь можно рассказать о творческом пути и вдохновении.","items":[{"title":"Биография","text":"Добавьте подтверждённые сведения об авторе."},{"title":"Сотрудничество","text":"Добавьте реальные контактные данные для связи."}]}]}
    else:
        spec={"theme":"modern","brand":name,"pages":[
            {"label":"Главная","eyebrow":"Знакомство с проектом","heading":name,"intro":"Современное пространство для презентации ваших услуг, подхода и работ.","items":[{"title":"Наш подход","text":"Расскажите, что важно вашим клиентам и как вы решаете их задачи."},{"title":"Проекты","text":"Добавьте примеры выполненных работ и реальные результаты."}]},
            {"label":"Возможности","eyebrow":"Что мы предлагаем","heading":"От задачи к результату","intro":"Здесь будет информация о направлениях работы.","items":[{"title":"Услуги","text":"Добавьте список услуг и условия."},{"title":"Как мы работаем","text":"Опишите этапы сотрудничества."}]},
            {"label":"Контакты","eyebrow":"Начало диалога","heading":"Давайте познакомимся","intro":"Добавьте подтверждённые способы связи.","items":[{"title":"Связаться","text":"Укажите реальные телефон и почту."},{"title":"График","text":"Укажите актуальное время работы."}]}]}
    if not previous:
        spec["theme"]={"premium":"editorial","cinema":"dark","3d":"dark","business":"modern"}.get(style,spec["theme"])
    text=instruction.lower()
    if any(x in text for x in ("темн","тёмн","dark","черн","чёрн")):
        spec["theme"]="dark"
    elif any(x in text for x in ("светл","light")):
        spec["theme"]="editorial" if poet else "modern"
    return validate(spec)

def css(spec):
    bg,fg,accent,panel,font=THEMES[spec["theme"]]
    return f"""*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:{bg};color:{fg};font:17px/1.65 system-ui,sans-serif}}a{{color:inherit}}header,main,footer{{max-width:1280px;margin:auto;padding:clamp(20px,5vw,64px)}}header{{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;border-bottom:1px solid {accent}44}}nav{{display:flex;gap:18px;flex-wrap:wrap}}nav a{{text-decoration:none}}nav a:hover{{text-decoration:underline}}.brand{{font-weight:800;letter-spacing:.04em}}.hero{{min-height:65vh;display:grid;grid-template-columns:1.3fr .7fr;align-items:center;gap:30px}}.eyebrow{{text-transform:uppercase;font-size:12px;letter-spacing:.18em;color:{accent};font-weight:800}}h1,h2{{font-family:{font};line-height:1.08;letter-spacing:-.04em;margin:.35em 0}}h1{{font-size:clamp(48px,8vw,112px)}}h2{{font-size:clamp(34px,5vw,64px)}}h3{{font-size:24px}}p{{max-width:68ch;overflow-wrap:anywhere}}.art{{min-height:300px;aspect-ratio:3/4;position:relative;overflow:hidden;background:{panel};border-radius:48% 48% 4px 4px;display:grid;place-items:center}}.art:before{{content:'';width:72%;aspect-ratio:1;border:1px solid {accent};border-radius:50%;box-shadow:0 0 0 24px {accent}22,0 0 0 48px {accent}11;transform:rotate(-18deg)}}.art:after{{content:'';position:absolute;width:36%;height:82%;border:1px solid {accent};transform:rotate(24deg)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(240px,100%),1fr));gap:16px}}article{{padding:clamp(20px,4vw,48px);background:{panel};border-top:2px solid {accent}}}.num{{font-size:12px;color:{accent};font-weight:bold}}.section{{padding:54px 0;border-top:1px solid {accent}44}}.cta{{display:inline-block;margin-top:12px;background:{fg};color:{bg};padding:12px 24px;text-decoration:none;border-radius:3px}}footer{{border-top:1px solid {accent}44}}@media(max-width:700px){{.hero{{grid-template-columns:1fr;min-height:0}}.art{{min-height:180px;aspect-ratio:16/9}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}"""

def header(spec):
    links="".join(f'<a href="#page-{i}">{escape(p["label"])}</a>' for i,p in enumerate(spec["pages"]))
    return f'<header><span class="brand">{escape(spec["brand"])}</span><nav aria-label="Навигация">{links}</nav></header>'

def page_markup(page, i, count):
    items="".join(f'<article><span class="num">{j+1:02d}</span><h3>{escape(x["title"])}</h3><p>{escape(x["text"])}</p></article>' for j,x in enumerate(page["items"]))
    heading="h1" if i==0 else "h2"
    next_link=f'<a class="cta" href="#page-{(i+1)%count}">{("Подробнее" if i==0 else "Далее")}</a>'
    return f'<section class="section" id="page-{i}"><div class="hero"><div><p class="eyebrow">{escape(page["eyebrow"])}</p><{heading}>{escape(page["heading"])}</{heading}><p>{escape(page["intro"])}</p>{next_link}</div><div class="art" aria-hidden="true"></div></div><div class="grid">{items}</div></section>'

def markup(spec):
    return header(spec)+"<main>"+"".join(page_markup(p,i,len(spec["pages"])) for i,p in enumerate(spec["pages"]))+"</main><footer>"+escape(spec["brand"])+"</footer>"

def preview(spec):
    return ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<meta name="robots" content="noindex,nofollow"><title>'+escape(spec["brand"])+'</title><style>'+css(spec)+'</style></head><body>'+markup(spec)+'</body></html>')

def source_files(spec):
    spec=validate(spec)
    return {
        "package.json":json.dumps({"name":"tracknode-generated-site","private":True,"version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"vue":"3.5.34"},"devDependencies":{"vite":"6.4.1","@vitejs/plugin-vue":"5.2.4"}},indent=2),
        "index.html":'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(spec["brand"])+'</title></head><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>',
        "vite.config.js":"import { defineConfig } from 'vite'\nimport vue from '@vitejs/plugin-vue'\nexport default defineConfig({plugins:[vue()],base:'./'})\n",
        "src/main.js":"import {createApp} from 'vue'\nimport App from './App.vue'\nimport './style.css'\ncreateApp(App).mount('#app')\n",
        "src/App.vue":'<script setup>\nimport spec from "./design.json"\nimport SitePage from "./SitePage.vue"\n</script>\n<template><header><span class="brand" v-text="spec.brand"/><nav aria-label="Навигация"><a v-for="(page,i) in spec.pages" :key="i" :href="\'#page-\'+i" v-text="page.label"/></nav></header><main><SitePage v-for="(page,i) in spec.pages" :key="i" :page="page" :index="i" :count="spec.pages.length"/></main><footer v-text="spec.brand"/></template>\n',
        "src/SitePage.vue":'<script setup>\ndefineProps({page:Object,index:Number,count:Number})\n</script>\n<template><section class="section" :id="\'page-\'+index"><div class="hero"><div><p class="eyebrow" v-text="page.eyebrow"/><component :is="index===0?\'h1\':\'h2\'" v-text="page.heading"/><p v-text="page.intro"/><a class="cta" :href="\'#page-\'+((index+1)%count)">{{index===0?\'Подробнее\':\'Далее\'}}</a></div><div class="art" aria-hidden="true"/></div><div class="grid"><article v-for="(item,j) in page.items" :key="j"><span class="num">{{String(j+1).padStart(2,\'0\')}}</span><h3 v-text="item.title"/><p v-text="item.text"/></article></div></section></template>\n',
        "src/design.json":json.dumps(spec,ensure_ascii=False,indent=2),
        "src/style.css":css(spec),
        "preview.html":preview(spec),
        "README.md":"# TrackNode Studio\nStatic Vue/Vite project with section navigation. Run npm install, npm run dev, npm run build. No backend or real 3D runtime. Model text is rendered as data.\n",
    }
