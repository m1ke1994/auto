"""Restore only bounded, previously exported source and local credited assets."""
import json
import re
import stat
import zipfile
from pathlib import Path
from site_store import ALLOWED, RESERVED
from models3d import MAX_BYTES, MAX_POLYS, safe_relative, EXTENSIONS
from media import MAX_PHOTOS, MAX_OUTPUT, allowed_url
from sketchfab_models import LICENSES

MODEL_KEY=re.compile(r"[A-Za-z0-9_-]{1,100}")
PHOTO=re.compile(r"src/media/pexels-([0-9]{1,15})\.webp")
MODEL_PATH=re.compile(r"tn-models/([A-Za-z0-9_-]{1,100})/model\.gltf")

def require(ok,message):
    if not ok:
        raise ValueError(message)

def restore(store,path):
    require(Path(path).stat().st_size<=40*1024*1024,"Source archive exceeds limit.")
    with zipfile.ZipFile(path) as z:
        members={}
        seen=set()
        entries=z.infolist()
        require(len(entries)<=180 and sum(x.file_size for x in entries)<=40*1024*1024,"Archive bounds exceeded.")
        for e in entries:
            name=e.filename
            require(len(name)<=450 and all(re.fullmatch(r"[A-Za-z0-9_.-]+",p) and not p.startswith(".") for p in name.split("/")) and not stat.S_ISLNK(e.external_attr>>16),"Unsafe archive member.")
            require(name.lower() not in seen,"Duplicate archive path.")
            seen.add(name.lower())
            members[name]=e
        def read(name,limit):
            require(name in members and 0<members[name].file_size<=limit,"Missing or oversized archive member.")
            return z.read(members[name])
        def metadata(name,default):
            return json.loads(read(name,128*1024)) if name in members else default
        info=metadata("tracknode-agent.json",{})
        require(isinstance(info,dict) and info.get("engine")=="openhands-sdk","Expected a TrackNode export.")
        for name in sorted(members):
            if ALLOWED.fullmatch(name) and name not in RESERVED:
                store.write(name,read(name,64000).decode("utf-8"))
        store.validate()
        plan=read("ART_DIRECTION.md",16000).decode("utf-8")
        plan=plan.partition("\n\n")[2] or plan
        store.set_plan(plan[:8000])
        history=info.get("rejected_models",[])
        require(isinstance(history,list) and len(history)<=12 and all(isinstance(x,str) and MODEL_KEY.fullmatch(x) for x in history),"Invalid rejected model history.")
        store.models.rejected.update(history)
        media=metadata("MEDIA_CREDITS.json",[])
        require(isinstance(media,list) and len(media)<=MAX_PHOTOS,"Invalid photo credits.")
        for c in media:
            require(isinstance(c,dict),"Invalid photo credit.")
            p=c.get("path","")
            m=PHOTO.fullmatch(p) if isinstance(p,str) else None
            require(m and type(c.get("id")) is int and int(m.group(1))==c["id"] and allowed_url(c.get("url"),{"www.pexels.com","pexels.com"}) and isinstance(c.get("photographer"),str) and p not in store.media.credits,"Invalid photo metadata.")
            store.media.assets[p]=read(p,MAX_OUTPUT)
            store.media.credits[p]={k:c[k] for k in ("path","id","photographer","url","alt","width","height") if k in c}
        store.media.downloads=len(media)
        models=metadata("MODEL_CREDITS.json",[])
        require(isinstance(models,list) and len(models)<=2,"Invalid model credits.")
        for c in models:
            require(isinstance(c,dict),"Invalid model credit.")
            p=c.get("path","")
            m=MODEL_PATH.fullmatch(p) if isinstance(p,str) else None
            require(m and isinstance(c.get("name"),str) and isinstance(c.get("author",""),str),"Invalid model metadata.")
            key=m.group(1)
            require(key not in store.models.credits and key not in store.models.rejected,"Duplicate or rejected model.")
            if c.get("source")=="Sketchfab":
                require(key=="sketchfab-"+str(c.get("id","")) and re.fullmatch(r"sketchfab-[a-f0-9]{32}",key) and LICENSES.get(c.get("license_url"))==c.get("license") and c.get("license_url") in LICENSES and allowed_url(c.get("url"),{"sketchfab.com"}),"Invalid Sketchfab credit.")
            else:
                require(key==c.get("id") and c.get("license")=="CC0" and allowed_url(c.get("url"),{"polyhaven.com"}),"Invalid Poly Haven credit.")
            prefix="public/tn-models/"+key+"/"
            raw=read(prefix+"model.gltf",2*1024*1024)
            scene=json.loads(raw)
            require(scene.get("asset",{}).get("version")=="2.0" and bool(scene.get("meshes")) and not set(scene.get("extensionsRequired",[]))-EXTENSIONS,"Invalid model scene.")
            pending={prefix+"model.gltf":raw}
            for kind in ("buffers","images"):
                for item in scene.get(kind,[]):
                    uri=item.get("uri")
                    if uri is None:
                        continue
                    require(safe_relative(uri),"Unsafe model dependency.")
                    pending[prefix+uri]=read(prefix+uri,MAX_BYTES)
            require(len(pending)<=25 and sum(map(len,pending.values()))+sum(map(len,store.models.assets.values()))<=MAX_BYTES,"Model budget exceeded.")
            store.models.assets.update(pending)
            credit={k:c[k] for k in ("id","name","author","path","source","url","license","license_url","changes","polycount","metadata_score","visual_verified","visual_score","visual_quality_tier") if k in c}
            if credit.get("source")!="Sketchfab":
                credit["license_url"]="https://creativecommons.org/publicdomain/zero/1.0/"
            credit["bytes"]=sum(map(len,pending.values()))
            store.models.credits[key]=credit
        store.self_review=""
    return info

def critic_notes(path):
    p=Path(path)
    require(0<p.stat().st_size<=512*1024,"Invalid visual report size.")
    report=json.loads(p.read_text(encoding="utf-8"))
    require(report.get("model")=="deepseek-flash" and report.get("status")=="needs_revision" and report.get("passed") is False,"Only a completed rejected visual review can trigger repair.")
    notes={}
    for device in ("desktop","mobile"):
        d=report["devices"][device]
        issues=[]
        for item in d["issues"][:20]:
            require(item["severity"] in ("critical","major","minor"),"Invalid issue severity.")
            issues.append({k:str(item[k])[:1000] for k in ("severity","image","problem","fix")})
        notes[device]={"score":d["score"],"summary":str(d["summary"])[:1500],"issues":issues}
    return json.dumps(notes,ensure_ascii=False)[:18000]
