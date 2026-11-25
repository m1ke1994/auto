"""Local single-user Sketchfab importer. No shared-account SaaS access."""
import io
import json
import re
import stat
import time
import zipfile
from urllib.parse import urlsplit
from PIL import Image
from models3d import MAX_BYTES, MAX_POLYS, EXTENSIONS, safe_relative
from sketchfab_probe import api, allowed_cdn, request_bytes, NetworkFailure, UID, MAX_ARCHIVE

LICENSES = {
    "https://creativecommons.org/publicdomain/zero/1.0/":"CC0 1.0",
    "https://creativecommons.org/licenses/by/4.0/":"CC BY 4.0",
    "https://creativecommons.org/licenses/by/3.0/":"CC BY 3.0",
}

def license_info(detail):
    value=detail.get("license")
    if not isinstance(value,dict):
        return None
    url=value.get("url","")
    if not isinstance(url,str):
        return None
    url=url.replace("http://creativecommons.org/","https://creativecommons.org/",1)
    url=url.rstrip("/")+"/"
    if url not in LICENSES:
        return None
    return LICENSES[url],url

def safe_member(name):
    return (isinstance(name,str) and len(name)<=400 and
            all(re.fullmatch(r"[A-Za-z0-9_.-]{1,120}",p) and not p.startswith(".")
                for p in name.split("/")))

def unpack_model(raw, prefix, budget):
    """Read selected members into memory, never extract an untrusted ZIP."""
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=[x for x in archive.infolist() if not x.is_dir()]
            if len(entries)>100 or sum(x.file_size for x in entries)>48*1024*1024:
                raise ValueError("Sketchfab unpacked archive too large.")
            members={}
            for entry in entries:
                if not safe_member(entry.filename) or stat.S_ISLNK(entry.external_attr>>16):
                    raise ValueError("Unsafe Sketchfab archive path or symlink.")
                if entry.filename in members:
                    raise ValueError("Duplicate archive member.")
                members[entry.filename]=entry
            scenes=[p for p in members if p.lower().endswith(".gltf")]
            if len(scenes)!=1 or members[scenes[0]].file_size>min(2*1024*1024,budget):
                raise ValueError("Expected one size-limited glTF scene.")
            scene_path=scenes[0]
            parent=scene_path.rpartition("/")[0]
            scene_bytes=archive.read(members[scene_path])
            scene=json.loads(scene_bytes)
            if scene["asset"]["version"]!="2.0" or not scene.get("meshes"):
                raise ValueError("Expected glTF 2.0 geometry.")
            if set(scene.get("extensionsRequired",[]))-EXTENSIONS or set(scene.get("extensionsUsed",[]))-EXTENSIONS:
                raise ValueError("Unsupported model extension; choose an uncompressed glTF.")
            refs={}
            for kind in ("buffers","images"):
                for item in scene.get(kind,[]):
                    uri=item.get("uri")
                    if not safe_relative(uri):
                        raise ValueError("Model must use safe local buffer and image files.")
                    path=(parent+"/" if parent else "")+uri
                    if path not in members:
                        raise ValueError("Missing glTF dependency.")
                    refs[uri]=(kind,members[path])
            if len(refs)>24:
                raise ValueError("Too many model dependencies.")
            pending={prefix+"model.gltf":scene_bytes}
            for uri,(kind,entry) in sorted(refs.items()):
                if entry.file_size>budget-sum(map(len,pending.values())):
                    raise ValueError("Project 3D asset byte limit exceeded.")
                blob=archive.read(entry)
                if kind=="images":
                    with Image.open(io.BytesIO(blob)) as img:
                        if img.format not in ("JPEG","PNG","WEBP") or img.width*img.height>16_777_216:
                            raise ValueError("Unsupported or oversized model texture.")
                        img.verify()
                pending[prefix+uri]=blob
            return pending
    except (zipfile.BadZipFile,RuntimeError,UnicodeError,KeyError,TypeError,AttributeError,OSError,NotImplementedError,Image.DecompressionBombError):
        raise ValueError("Invalid Sketchfab archive or texture.") from None

class SketchfabLibrary:
    def __init__(self,token,shared):
        self._token=token.strip()
        self.shared=shared
        self.candidates={}
        self.searches=0

    @property
    def enabled(self):
        return bool(self._token)

    def search(self,query):
        if not self.enabled:
            raise ValueError("Sketchfab local account is not configured.")
        if not 2<=len(query.strip())<=100 or self.searches>=4:
            raise ValueError("Use short English keywords; max four Sketchfab searches.")
        self.searches+=1
        result=api("/search",self._token,{"type":"models","q":query.strip(),"downloadable":"true","count":24})
        candidates=[]
        for item in result.get("results",[]):
            uid=item.get("uid")
            faces=item.get("faceCount")
            if isinstance(uid,str) and UID.fullmatch(uid) and type(faces) is int and 0<faces<=MAX_POLYS:
                candidates.append((faces,uid))
        found=[]
        for _,uid in sorted(candidates)[:8]:
            detail=api("/models/"+uid,self._token)
            license=license_info(detail)
            user=detail.get("user",{})
            author=user.get("username") if isinstance(user,dict) else None
            faces=detail.get("faceCount")
            if (detail.get("isDownloadable") is not True or not license or
                not isinstance(author,str) or not author.strip() or
                type(faces) is not int or not 0<faces<=MAX_POLYS):
                continue
            item={"id":uid,"name":str(detail.get("name",uid))[:150],
                  "author":author[:150],"license":license[0],"license_url":license[1],
                  "source":"Sketchfab","url":"https://sketchfab.com/3d-models/"+uid,
                  "polycount":faces}
            self.candidates[uid]=item
            found.append(item)
            if len(found)>=4:
                break
        return found

    def save(self,uid):
        if uid not in self.candidates:
            raise ValueError("Select an ID returned by sketchfab_search.")
        key="sketchfab-"+uid
        if key in self.shared.credits:
            return self.shared.credits[key]
        if self.shared.downloads>=2:
            raise ValueError("Maximum two model download attempts across providers.")
        self.shared.downloads+=1
        detail=api("/models/"+uid,self._token)
        license=license_info(detail)
        current=self.candidates[uid]
        if detail.get("isDownloadable") is not True or not license or license[1]!=current["license_url"]:
            raise ValueError("Model license or availability changed.")
        budget=MAX_BYTES-sum(map(len,self.shared.assets.values()))
        if budget<=0:
            raise ValueError("Project 3D asset byte limit reached.")
        for attempt in range(2):
            data=api("/models/"+uid+"/download",self._token)
            entry=data.get("gltf",{})
            url=entry.get("url")
            if not allowed_cdn(url):
                raise ValueError("Sketchfab download host not approved.")
            size=entry.get("size")
            if type(size) is int and size>min(MAX_ARCHIVE,budget):
                raise ValueError("Sketchfab archive exceeds project model size limit.")
            try:
                raw=request_bytes(url,limit=min(MAX_ARCHIVE,budget),timeout=(15,90))
                break
            except NetworkFailure:
                if attempt==1:
                    raise ValueError("Sketchfab CDN download failed after two attempts.") from None
                time.sleep(2)
        path="tn-models/"+key+"/"
        pending=unpack_model(raw,"public/"+path,budget)
        credit={**current,"path":path+"model.gltf","bytes":sum(map(len,pending.values())),
                "changes":"Imported local glTF files; original geometry and textures retained."}
        self.shared.assets.update(pending)
        self.shared.credits[key]=credit
        return credit
