"""All tool-controlled files live in memory; no user-supplied filesystem paths."""
import json
import re
import zipfile
from pathlib import Path
from html import escape
from quality import quality_issues

ALLOWED = re.compile(r"src/(?:[A-Za-z0-9_-]+/){0,3}[A-Za-z0-9_-]+\.(?:vue|js|ts|css|svg)")
MAX_FILE = 64_000
MAX_TOTAL = 300_000
MAX_FILES = 30
DEPENDENCIES = {"vue":"3.5.34", "three":"0.180.0", "gsap":"3.13.0", "lenis":"1.3.20"}
REQUIRED = {"src/App.vue", "src/style.css"}
RESERVED = {"src/main.js", "src/main.ts", "src/landing-progress.js"}

class SiteStore:
    def __init__(self, media=None):
        self.files = {}
        self.media = media
        self.profile = None
        self.design_brief = ""
        self.self_review = ""

    def set_plan(self, content):
        if not 80 <= len(content.strip()) <= 8000:
            raise ValueError("Art direction plan must contain 80-8000 characters.")
        self.design_brief = content.strip()
        self.self_review = ""

    def set_review(self, content):
        self.validate()
        if self.profile:
            issues = quality_issues(self.files,self.profile)
            if issues:
                raise ValueError("Fix before review: " + " | ".join(issues))
        if not 40 <= len(content.strip()) <= 6000:
            raise ValueError("Self review must contain 40-6000 characters.")
        self.self_review = content.strip()

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

    def export(self, output, model, profile=None):
        self.validate()
        if profile is not None:
            issues = quality_issues(self.files,profile)
            if issues:
                raise ValueError("Source quality gate: " + " | ".join(issues))
            if not self.design_brief or not self.self_review:
                raise ValueError("Art direction plan and final self-review are required.")
            if not any(p.startswith("src/components/") and p.endswith(".vue") for p in self.files):
                raise ValueError("At least one Vue component is required.")
        # Only trusted code controls the package manifest and Vite entrypoint.
        trusted = {
            "package.json": json.dumps({"name":"tracknode-agent-site","private":True,"version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":DEPENDENCIES,"devDependencies":{"vite":"6.4.1","@vitejs/plugin-vue":"5.2.4"}},indent=2),
            "index.html": '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>TrackNode Studio</title></head><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>',
            "vite.config.js": "import {defineConfig} from 'vite';\nimport vue from '@vitejs/plugin-vue';\nexport default defineConfig({plugins:[vue()],base:'./'});\n",
            "src/main.js": "import {createApp} from 'vue';\nimport App from './App.vue';\nimport './style.css';\nimport {installLandingProgress} from './landing-progress.js';\ncreateApp(App).mount('#app');\ninstallLandingProgress();\n",
            "src/landing-progress.js": Path(__file__).with_name("landing-progress.js").read_text(encoding="utf-8"),
            "README.md": "# TrackNode OpenHands source\nUntrusted AI-generated source. Inspect it and build only in an isolated, credential-free environment. No build or visual verification has been performed.\n",
            "tracknode-agent.json": json.dumps({"engine":"openhands-sdk","model":model,"build_verified":False,"visual_verified":False,"profile":profile,"files":sorted(self.files)},indent=2),
        }
        if self.design_brief:
            trusted["ART_DIRECTION.md"] = "# AI art direction (unverified)\n\n" + self.design_brief
        if self.self_review:
            trusted["SELF_REVIEW.md"] = "# AI source review (not build or browser testing)\n\n" + self.self_review
        assets = self.media.assets if self.media else {}
        credits = list(self.media.credits.values()) if self.media else []
        if credits:
            trusted["MEDIA_CREDITS.json"] = json.dumps(credits,ensure_ascii=False,indent=2)
            links = " · ".join(
                '<a href="' + escape(c["url"],quote=True) + '" rel="noopener noreferrer">'
                + escape(c["photographer"] or "Pexels photographer") + '</a>' for c in credits
            )
            footer = ('<aside aria-label="Photo credits" style="padding:12px;text-align:center;background:var(--tn-footer-bg,#171717);color:var(--tn-footer-fg,#e5e5e5);font:12px/1.6 system-ui">'
                      '<a href="https://www.pexels.com/" style="color:inherit">Photos provided by Pexels</a> · '
                      + links + '</aside>')
            trusted["index.html"] = trusted["index.html"].replace("</body>",footer+"</body>")
        dest = Path(output)
        # Refuse to overwrite a previous artifact or a symlink.
        with dest.open("xb") as stream, zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted({**self.files, **assets, **trusted}.items()):
                archive.writestr(name, content)
