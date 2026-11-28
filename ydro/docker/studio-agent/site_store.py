"""All tool-controlled files live in memory; no user-supplied filesystem paths."""
import json
import os
import re
import zipfile
from pathlib import Path
from html import escape, unescape
from urllib.parse import urlsplit
from quality import quality_issues
from storyboard import validate_storyboard

ALLOWED = re.compile(r"src/(?:[A-Za-z0-9_-]+/){0,3}[A-Za-z0-9_-]+\.(?:vue|js|ts|css|svg)")
MAX_FILE = 64_000
MAX_TOTAL = 300_000
MAX_FILES = 30
DEPENDENCIES = {"vue":"3.5.34", "three":"0.180.0", "gsap":"3.13.0", "lenis":"1.3.20"}
REQUIRED = {"src/App.vue", "src/style.css"}
RESERVED = {"src/tn-contacts.js", "src/main.js", "src/main.ts", "src/landing-progress.js", "src/components/CinemaModel.vue", "src/cinematic-motion.js", "src/components/SceneCarousel.vue", "src/components/SceneStory.vue", "src/components/HeroObjectStage.vue", "src/components/AboutMetrics.vue"}

class SiteStore:
    def __init__(self, media=None, models=None):
        self.files = {}
        self.media = media
        self.models = models
        self.profile = None
        self.design_brief = ""
        self.self_review = ""
        self.review_origin = None
        self.scene_required = False
        self.storyboard = None
        self.hero_preset = None
        self.contacts = {}

    def set_contacts(self, raw):
        limits={"phone":32,"email":180,"address":250,"telegram":250,"vk":250,"whatsapp":250,"website":250}
        if not isinstance(raw,dict) or set(raw)-set(limits):
            raise ValueError("Invalid contact data")
        out={}
        for key,value in raw.items():
            if not isinstance(value,str) or len(value)>limits[key] or any(ord(c)<32 or ord(c)==127 for c in value):
                raise ValueError("Invalid contact value")
            value=value.strip()
            if not value:
                continue
            if key=="phone" and (not re.fullmatch(r"\+?[0-9 ()-]{5,32}",value) or not 5<=sum(c.isdigit() for c in value)<=15):
                raise ValueError("Invalid contact phone")
            if key=="email" and not re.fullmatch(r"[^\s@<>\x22\x27:;,?&#%]+@[^\s@<>\x22\x27:;,?&#%]+\.[^\s@<>\x22\x27:;,?&#%]+",value):
                raise ValueError("Invalid contact email")
            if key in ("telegram","vk","whatsapp","website"):
                u=urlsplit(value)
                if u.scheme not in ("http","https") or not u.hostname or u.username or u.password or "\\" in value or any(c.isspace() for c in value):
                    raise ValueError("Invalid public contact URL")
            out[key]=value
        self.contacts=out

    def set_plan(self, content):
        if not 80 <= len(content.strip()) <= 8000:
            raise ValueError("Art direction plan must contain 80-8000 characters.")
        self.design_brief = content.strip()
        self.self_review = ""

    def set_storyboard(self, content):
        self.storyboard=validate_storyboard(content)
        self.self_review=""

    def scene_issues(self):
        issues=[]
        if self.hero_preset:
            app=self.files.get("src/App.vue","")
            home=re.search(r'<section\b[^>]*\bid\s*=\s*["\']home["\'][^>]*>(.*?)</section>',app,re.S)
            tag=re.search(r'<HeroObjectStage\b[^>]*>',home.group(1)) if home else None
            imported=re.search(r'import\s+HeroObjectStage\s+from\s*["\']\./components/HeroObjectStage\.vue["\']',app)
            if not imported or not tag or not re.search(r'\bpreset\s*=\s*["\']'+re.escape(self.hero_preset)+r'["\']',tag.group(0)) or len(re.findall(r'<HeroObjectStage\b',app))!=1:
                issues.append("Render one trusted HeroObjectStage with literal preset="+self.hero_preset+" inside home in App.vue.")
        if not self.scene_required:
            return issues
        if not self.storyboard:
            issues.append("Save a valid storyboard before source generation.")
        source="\n".join(v for p,v in self.files.items() if p.endswith(".vue"))
        for name in ("SceneCarousel","SceneStory"):
            if not re.search(r"<"+name+r"\b",source) or not re.search(r"import\s+"+name+r"\s+from\s+['\"][^'\"]*/"+name+r"\.vue['\"]",source):
                issues.append("Import and render trusted "+name+" in a middle chapter.")
        return issues

    def model_issues(self):
        if not self.models:
            return []
        source="\n".join(self.files.values())
        refs=set(re.findall(r"tn-models/[A-Za-z0-9_-]+/model\.gltf",source))
        paths={c["path"] for c in self.models.credits.values()}
        issues=[]
        if refs-paths:
            issues.append("Remove stale model references: "+", ".join(sorted(refs-paths)))
        if paths-refs:
            issues.append("Unused imported models: "+", ".join(sorted(paths-refs)))
        if paths and not re.search(r"<CinemaModel\b",source):
            issues.append("Use the trusted CinemaModel component.")
        if len(paths)>2:
            issues.append("At most two imported models per project.")
        return issues

    def remove_model(self,key):
        if not self.models or key not in self.models.credits:
            raise ValueError("Choose an exact key from model_inventory.")
        if len(self.models.rejected)>=12:
            raise ValueError("Rejected model history limit.")
        prefix="public/tn-models/"+key+"/"
        self.models.assets={p:b for p,b in self.models.assets.items() if not p.startswith(prefix)}
        del self.models.credits[key]
        self.models.rejected.add(key)
        self.self_review=""

    def set_review(self, content, *, origin="agent"):
        if origin not in ("agent","automated_structural"):
            raise ValueError("Invalid source review origin.")
        self.validate()
        if self.profile:
            issues = quality_issues(self.files,self.profile)+self.model_issues()+self.scene_issues()
            if issues:
                raise ValueError("Fix before review: " + " | ".join(issues))
        if not 40 <= len(content.strip()) <= 6000:
            raise ValueError("Self review must contain 40-6000 characters.")
        self.self_review = content.strip()
        self.review_origin = origin

    def write(self, path, content):
        if not ALLOWED.fullmatch(path) or path in RESERVED:
            raise ValueError("Path not allowed. Use src/App.vue, src/style.css or src/components/Name.vue.")
        if not content.strip() or len(content.encode("utf-8")) > MAX_FILE:
            raise ValueError("File must be nonempty and at most 64 KB.")
        candidate = dict(self.files)
        candidate[path] = content
        if len(candidate) > MAX_FILES or sum(len(s.encode("utf-8")) for s in candidate.values()) > MAX_TOTAL:
            raise ValueError("Project exceeds file count or size limit.")
        self.files = candidate
        self.self_review = ""

    def read(self, path):
        if path not in self.files:
            raise ValueError("No such project file.")
        return self.files[path]

    def validate(self):
        missing = REQUIRED - self.files.keys()
        if missing:
            raise ValueError("Missing required files: " + ", ".join(sorted(missing)))
        if "<template" not in self.files["src/App.vue"]:
            raise ValueError("App.vue needs a Vue template.")

    def checkpoint(self, output, model, profile):
        """Atomically replace a separate, explicitly unapproved recovery archive."""
        if not self.design_brief or not self.files:
            return False
        dest=Path(output)
        temp=dest.with_name(dest.name+".tmp")
        # Fixed paths in a disposable output directory, never tool-controlled.
        if temp.exists():
            temp.unlink()
        try:
            self.export(temp,model,profile,checkpoint=True)
            os.replace(temp,dest)
        finally:
            if temp.exists():
                temp.unlink()
        return True

    def export(self, output, model, profile=None, *, checkpoint=False):
        if not checkpoint:
            self.validate()
        if profile is not None and not checkpoint:
            issues = quality_issues(self.files,profile)+self.model_issues()+self.scene_issues()
            if issues:
                raise ValueError("Source quality gate: " + " | ".join(issues))
            if self.models and self.models.credits:
                source = "\n".join(self.files.values())
                if not re.search(r"<CinemaModel\b", source):
                    raise ValueError("Imported models must use the trusted CinemaModel component.")
                for credit in self.models.credits.values():
                    if credit["path"] not in source:
                        raise ValueError("Imported model is not referenced by generated source.")
            if not self.design_brief or not self.self_review:
                raise ValueError("Art direction plan and final self-review are required.")
            if not any(p.startswith("src/components/") and p.endswith(".vue") for p in self.files):
                raise ValueError("At least one Vue component is required.")
        # Derive the document title and description from visible page copy.
        # The H1 remains the source of truth; never ship a generic studio tab title.
        app_source = self.files.get("src/App.vue", "")
        h1_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", app_source, re.IGNORECASE | re.DOTALL)
        def visible_text(value):
            value = re.sub(r"<[^>]+>", " ", value)
            value = re.sub(r"\{\{.*?\}\}", " ", value)
            return " ".join(unescape(value).split())
        page_title = visible_text(h1_match.group(1))[:90] if h1_match else "Сайт"
        hero_match = re.search(r'<p\b[^>]*class="[^"]*hero-lede[^"]*"[^>]*>(.*?)</p>', app_source, re.IGNORECASE | re.DOTALL)
        page_description = visible_text(hero_match.group(1))[:200] if hero_match else ""
        description_tag = '<meta name="description" content="' + escape(page_description, quote=True) + '">' if page_description else ""
        # Only trusted code controls the package manifest and Vite entrypoint.
        trusted = {
            "package.json": json.dumps({"name":"tracknode-agent-site","private":True,"version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":DEPENDENCIES,"devDependencies":{"vite":"6.4.1","@vitejs/plugin-vue":"5.2.4"}},indent=2),
            "index.html": '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + escape(page_title) + '</title>' + description_tag + '</head><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>',
            "vite.config.js": "import {defineConfig} from 'vite';\nimport vue from '@vitejs/plugin-vue';\nexport default defineConfig({plugins:[vue()],base:'./'});\n",
            "src/main.js": "import {createApp} from 'vue';\nimport App from './App.vue';\nimport './style.css';\nimport {installLandingProgress} from './landing-progress.js';\ncreateApp(App).mount('#app');\ninstallLandingProgress();\n",
            "src/landing-progress.js": Path(__file__).with_name("landing-progress.js").read_text(encoding="utf-8"),
            "src/components/CinemaModel.vue": Path(__file__).with_name("CinemaModel.vue").read_text(encoding="utf-8"),
            "src/cinematic-motion.js": Path(__file__).with_name("cinematic-motion.js").read_text(encoding="utf-8"),
            "src/components/SceneCarousel.vue": Path(__file__).with_name("SceneCarousel.vue").read_text(encoding="utf-8"),
            "src/components/SceneStory.vue": Path(__file__).with_name("SceneStory.vue").read_text(encoding="utf-8"),
            "src/components/HeroObjectStage.vue": Path(__file__).with_name("HeroObjectStage.vue").read_text(encoding="utf-8"),
            "src/components/AboutMetrics.vue": Path(__file__).with_name("AboutMetrics.vue").read_text(encoding="utf-8"),
            "README.md": "# TrackNode OpenHands source\nUntrusted AI-generated source. Inspect it and build only in an isolated, credential-free environment. No build or visual verification has been performed.\n",
            "tracknode-agent.json": json.dumps({"engine":"openhands-sdk","model":model,"build_verified":False,"visual_verified":False,"checkpoint":checkpoint,"scene_engine":1 if self.scene_required else 0,"hero_preset":self.hero_preset,"review_origin":self.review_origin if self.self_review else None,"profile":profile,"files":sorted(self.files),"rejected_models":sorted(self.models.rejected) if self.models else []},indent=2),
        }
        if self.contacts:
            entries=[]
            labels={"phone":"Телефон","email":"Email","address":"Адрес","telegram":"Telegram","vk":"ВКонтакте","whatsapp":"WhatsApp","website":"Сайт"}
            for key,label in labels.items():
                if key not in self.contacts:
                    continue
                value=self.contacts[key]
                href=("tel:"+re.sub(r"[^0-9+]","",value) if key=="phone" else "mailto:"+value if key=="email" else "" if key=="address" else value)
                entries.append({"key":key,"label":label,"value":value,"href":href})
            trusted["CONTACTS.json"]=json.dumps(self.contacts,ensure_ascii=False)
            trusted["public/tn-contact-contract.json"]=json.dumps(entries,ensure_ascii=False)
            trusted["src/tn-contacts.js"]="const entries="+json.dumps(entries,ensure_ascii=True)+";\n"+r"""
export function installContacts(){
  for(const target of document.querySelectorAll('#contacts, footer[data-tn-footer]')){
    const group=document.createElement('div')
    group.dataset.tnContactGroup=''
    group.setAttribute('aria-label','Контактные данные')
    group.style.cssText='display:flex;flex-wrap:wrap;gap:.65rem 1.3rem;align-items:flex-start;margin-block:1.2rem;max-width:100%;min-width:0;overflow-wrap:anywhere;font-size:clamp(.875rem,1.2vw,1rem);line-height:1.5'
    for(const entry of entries){
      const node=document.createElement(entry.href?'a':'span')
      node.dataset.tnContact=entry.key
      node.textContent=entry.label+': '+entry.value
      node.style.cssText='min-width:0;max-width:100%;overflow-wrap:anywhere;color:inherit'
      if(entry.href){
        node.setAttribute('href',entry.href)
        if(/^https?:/.test(entry.href)){node.target='_blank';node.rel='noopener noreferrer'}
      }
      group.append(node)
    }
    target.append(group)
  }
}
"""
            trusted["src/main.js"] += "import {installContacts} from './tn-contacts.js';\ninstallContacts();\n"
        if self.storyboard:
            trusted["STORYBOARD.json"]=json.dumps(self.storyboard,ensure_ascii=False,indent=2)
        # New exports declare the shared carousel behavior independently of profile.
        trusted["public/tn-carousel-contract.json"]=json.dumps({"version":2,"hiddenScrollbar":True,"wheel":True})
        if self.scene_required:
            trusted["public/tn-scene-contract.json"]=json.dumps({"version":1,"carousel":True,"story":True,"heroPreset":self.hero_preset})
        if self.design_brief:
            trusted["ART_DIRECTION.md"] = "# AI art direction (unverified)\n\n" + self.design_brief
        if self.self_review:
            heading = "# Automated structural source check (not AI, build or browser review)" if self.review_origin == "automated_structural" else "# AI source review (not build or browser testing)"
            trusted["SELF_REVIEW.md"] = heading + "\n\n" + self.self_review
        assets = self.media.assets if self.media else {}
        credits = list(self.media.credits.values()) if self.media else []
        if credits:
            trusted["MEDIA_CREDITS.json"] = json.dumps(credits,ensure_ascii=False,indent=2)
            links = " · ".join(
                '<a href="' + escape(c["url"],quote=True) + '" rel="noopener noreferrer">'
                + escape(c["photographer"] or "Pexels photographer") + '</a>' for c in credits
            )
            footer = ('<details class="tn-photo-credits" style="padding:12px clamp(20px,4vw,64px);border-top:1px solid color-mix(in srgb,var(--tn-footer-fg,#e5e5e5) 16%,transparent);background:var(--tn-footer-bg,#171717);color:var(--tn-footer-fg,#e5e5e5);font:11px/1.6 system-ui">'
                      '<summary style="width:max-content;margin:0 auto;cursor:pointer;letter-spacing:.12em;text-transform:uppercase;opacity:.72">Photography credits</summary>'
                      '<aside aria-label="Photo credits" style="padding-top:10px;display:flex;flex-wrap:wrap;justify-content:center;gap:4px 8px;text-align:center;opacity:.72">'
                      '<a href="https://www.pexels.com/" style="color:inherit">Photos provided by Pexels</a> · '
                      + links + '</aside></details>')
            trusted["index.html"] = trusted["index.html"].replace("</body>",footer+"</body>")
        if self.models and self.models.credits:
            assets = {**assets, **self.models.assets}
            model_credits = list(self.models.credits.values())
            trusted["MODEL_CREDITS.json"] = json.dumps(model_credits,ensure_ascii=False,indent=2)
            links = []
            for c in model_credits:
                provider = c.get("source","Poly Haven")
                name = escape(c["name"])
                author = escape(c.get("author",""))
                license = escape(c.get("license","CC0"))
                model_link = '<a href="' + escape(c["url"],quote=True) + '" style="color:inherit">' + name + '</a>'
                license_url = c.get("license_url","https://creativecommons.org/publicdomain/zero/1.0/")
                license_link = '<a href="' + escape(license_url,quote=True) + '" style="color:inherit">' + license + '</a>'
                provider_url = "https://sketchfab.com/" if provider=="Sketchfab" else "https://polyhaven.com/"
                links.append(model_link + (" — " + author if author else "") + " — " + license_link +
                             ' · <a href="' + provider_url + '" style="color:inherit">' + escape(provider) + '</a>' +
                             (" · " + escape(c["changes"]) if c.get("changes") else ""))
            strip = '<aside class="tn-model-credits" aria-label="3D model credits" style="padding:10px 20px;display:flex;flex-wrap:wrap;justify-content:center;gap:4px 8px;text-align:center;opacity:.72;background:var(--tn-footer-bg,#171717);color:var(--tn-footer-fg,#e5e5e5);font:10px/1.5 system-ui">3D: ' + " | ".join(links) + '</aside>'
            trusted["index.html"] = trusted["index.html"].replace("</body>",strip+"</body>")
        bundle={**self.files, **assets, **trusted}
        if profile=="cinema" and not checkpoint and self.models and self.models.credits:
            from block_edit import apply_hero_film, primary_hero_film
            if primary_hero_film(self.files):
                # Never silently publish a split-column primary hero.
                bundle=apply_hero_film({k:v.encode("utf-8") if isinstance(v,str) else v for k,v in bundle.items()})
        dest = Path(output)
        # Refuse to overwrite a previous artifact or a symlink.
        with dest.open("xb") as stream, zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(bundle.items()):
                archive.writestr(name, content)
