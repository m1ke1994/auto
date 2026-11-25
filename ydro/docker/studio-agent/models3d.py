"""Bounded, local glTF assets from the official Poly Haven API."""
import hashlib
import json
import re
from urllib.parse import quote
import requests
from media import allowed_url
from asset_quality import rank_asset

API="https://api.polyhaven.com"
HEADERS={"User-Agent":"TrackNode-Studio/2.0 (3D asset importer)"}
SLUG=re.compile(r"[A-Za-z0-9_-]{1,100}")
PART=re.compile(r"[A-Za-z0-9_.-]{1,120}")
MAX_BYTES=16*1024*1024
MAX_POLYS=100000
CDN={"dl.polyhaven.org","dl.polyhaven.com"}
EXTENSIONS={"KHR_materials_specular","KHR_materials_ior","KHR_materials_clearcoat","KHR_materials_emissive_strength","KHR_materials_unlit","KHR_texture_transform","KHR_materials_transmission","KHR_materials_sheen","KHR_materials_volume","KHR_mesh_quantization"}

def safe_relative(path):
    return (isinstance(path,str) and len(path)<=400 and
            all(PART.fullmatch(p) and p not in (".","..") and not p.startswith(".") for p in path.split("/")) and
            path.lower().endswith((".bin",".jpg",".jpeg",".png",".webp")))

def fetch(url,hosts,limit):
    if not allowed_url(url,hosts):
        raise ValueError("Unapproved model download host.")
    try:
        with requests.get(url,headers=HEADERS,timeout=(8,25),allow_redirects=False,stream=True) as response:
            if response.status_code!=200:
                raise ValueError("Poly Haven HTTP "+str(response.status_code))
            data=bytearray()
            for chunk in response.iter_content(65536):
                if len(data)+len(chunk)>limit:
                    raise ValueError("Poly Haven download exceeds size limit.")
                data.extend(chunk)
            return bytes(data)
    except requests.RequestException:
        raise ValueError("Poly Haven connectivity error.") from None

def api(path):
    try:
        return json.loads(fetch(API+path,{"api.polyhaven.com"},8*1024*1024))
    except (UnicodeError,ValueError) as exc:
        raise ValueError("Poly Haven API: "+str(exc)[:180]) from None

def file_bytes(record,limit):
    if not isinstance(record,dict):
        raise ValueError("Invalid model file metadata.")
    size=record.get("size")
    checksum=record.get("md5")
    if type(size) is not int or not 0<size<=limit or not isinstance(checksum,str) or not re.fullmatch(r"[a-fA-F0-9]{32}",checksum):
        raise ValueError("Model file size or checksum unavailable/out of bounds.")
    data=fetch(record.get("url"),CDN,size)
    if len(data)!=size or hashlib.md5(data).hexdigest()!=checksum.lower():
        raise ValueError("Model file integrity mismatch.")
    return data

class ModelLibrary:
    def __init__(self):
        self.catalog=None
        self.candidates={}
        self.assets={}
        self.credits={}
        self.searches=0
        self.downloads=0
        self.style='realistic'
        self.rejected=set()

    def search(self,query):
        if not 2<=len(query.strip())<=100 or self.searches>=5:
            raise ValueError("Use a short English model query; max five searches.")
        self.searches+=1
        if self.catalog is None:
            self.catalog=api("/assets?type=models")
            if not isinstance(self.catalog,dict):
                raise ValueError("Unexpected Poly Haven catalog.")
        tokens=re.findall(r"[a-z0-9]+",query.lower())
        if not tokens:
            raise ValueError("Use English search keywords.")
        matches=[]
        for slug,item in self.catalog.items():
            if slug in self.rejected or not SLUG.fullmatch(slug) or not isinstance(item,dict) or item.get("type")!=2:
                continue
            count=item.get("polycount")
            if type(count) is not int or not 0<count<=MAX_POLYS:
                continue
            title=str(item.get("name",slug))[:150]
            haystack=(" ".join([slug,title,str(item.get("tags",[])),str(item.get("categories",[]))])).lower()
            rank=rank_asset({**item,"slug":slug},query,count,self.style)
            if rank is not None:
                authors=item.get("authors",{})
                record={"id":slug,"name":title,"polycount":count,"license":"CC0",
                        "author":", ".join(authors)[:300] if isinstance(authors,dict) else "",
                        "url":"https://polyhaven.com/a/"+slug,**rank}
                matches.append((rank["metadata_score"],slug,record))
        result=[x[2] for x in sorted(matches,key=lambda x:(-x[0],x[1]))[:6]]
        self.candidates.update({x["id"]:x for x in result})
        return result

    def save(self,slug):
        if slug in self.rejected:
            raise ValueError("Previously rejected model cannot be reused.")
        if slug not in self.candidates:
            raise ValueError("Select a model ID returned by model_search.")
        if slug in self.credits:
            return self.credits[slug]
        if self.downloads>=2:
            raise ValueError("Maximum two model download attempts per project.")
        self.downloads+=1
        data=api("/files/"+quote(slug,safe=""))
        try:
            entry=data["gltf"]["1k"]["gltf"]
        except (KeyError,TypeError):
            raise ValueError("This model has no 1K glTF variant.")
        budget=MAX_BYTES-sum(map(len,self.assets.values()))
        raw=file_bytes(entry,min(budget,1024*1024))
        try:
            model=json.loads(raw)
            if model["asset"]["version"]!="2.0" or not model.get("meshes"):
                raise ValueError("Expected a glTF 2.0 model with geometry.")
            if set(model.get("extensionsRequired",[]))-EXTENSIONS:
                raise ValueError("Model requires unsupported decoder/extensions.")
            refs=set()
            for block in ("buffers","images"):
                for item in model.get(block,[]):
                    uri=item.get("uri")
                    if uri is not None:
                        if not safe_relative(uri):
                            raise ValueError("Unsafe or nonlocal glTF dependency.")
                        refs.add(uri)
            includes=entry.get("include",{})
            if not isinstance(includes,dict) or len(refs)>20:
                raise ValueError("Invalid glTF dependency list.")
            prefix="public/tn-models/"+slug+"/"
            pending={prefix+"model.gltf":raw}
            for uri in sorted(refs):
                if uri not in includes:
                    raise ValueError("Model dependency missing from official manifest.")
                blob=file_bytes(includes[uri],budget-sum(map(len,pending.values())))
                pending[prefix+uri]=blob
        except (KeyError,TypeError,AttributeError,UnicodeError):
            raise ValueError("Invalid glTF data or dependency metadata.") from None
        self.assets.update(pending)
        credit={**self.candidates[slug],"path":"tn-models/"+slug+"/model.gltf",
                "bytes":sum(map(len,pending.values()))}
        self.credits[slug]=credit
        return credit
