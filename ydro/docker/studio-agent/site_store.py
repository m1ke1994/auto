"""All tool-controlled files live in memory; no user-supplied filesystem paths."""
import json
import re
import zipfile
from pathlib import Path

ALLOWED = re.compile(r"src/(?:[A-Za-z0-9_-]+/){0,3}[A-Za-z0-9_-]+\.(?:vue|js|ts|css|svg)")
MAX_FILE = 64_000
MAX_TOTAL = 300_000
MAX_FILES = 30
REQUIRED = {"src/App.vue", "src/style.css"}
RESERVED = {"src/main.js", "src/main.ts"}

class SiteStore:
    def __init__(self):
        self.files = {}

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

    def export(self, output, model):
        self.validate()
        # Only trusted code controls the package manifest and Vite entrypoint.
        trusted = {
            "package.json": json.dumps({"name":"tracknode-agent-site","private":True,"version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"vue":"3.5.34"},"devDependencies":{"vite":"6.4.1","@vitejs/plugin-vue":"5.2.4"}},indent=2),
            "index.html": '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>TrackNode Studio</title></head><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>',
            "vite.config.js": "import {defineConfig} from 'vite';\nimport vue from '@vitejs/plugin-vue';\nexport default defineConfig({plugins:[vue()],base:'./'});\n",
            "src/main.js": "import {createApp} from 'vue';\nimport App from './App.vue';\nimport './style.css';\ncreateApp(App).mount('#app');\n",
            "README.md": "# TrackNode OpenHands source\nUntrusted AI-generated source. Inspect it and build only in an isolated, credential-free environment. No build or visual verification has been performed.\n",
            "tracknode-agent.json": json.dumps({"engine":"openhands-sdk","model":model,"build_verified":False,"files":sorted(self.files)},indent=2),
        }
        dest = Path(output)
        # Refuse to overwrite a previous artifact or a symlink.
        with dest.open("xb") as stream, zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted({**self.files, **trusted}.items()):
                archive.writestr(name, content)
