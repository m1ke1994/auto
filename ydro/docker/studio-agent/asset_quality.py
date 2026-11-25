"""Metadata-only asset ranking. Never equate a score with visual inspection."""
import math
import re

BAD = re.compile(r"\b(?:toy|toys|cartoon|cartoony|stylized|stylised|low[\s_-]*poly|low[\s_-]*polygon|voxel|chibi|miniature|lego|roblox|minecraft|blocky)\b",re.I)
GOOD = re.compile(r"\b(?:photorealistic|photo[\s_-]*realistic|realistic|realism|photogrammetry|high[\s_-]*detail(?:ed)?|high[\s_-]*quality|pbr|scan|scanned|physically[\s_-]*based)\b",re.I)
STOP = {"realistic","photorealistic","photo","real","high","detail","detailed","quality","pbr","model","3d","premium","cinematic","low","poly","free","downloadable","with","and","for","the","scan","photogrammetry","stylized","cartoon","toy"}
VEHICLE = {"car","cars","vehicle","automobile","automotive","supercar","sports car","sedan","coupe","suv","truck","roadster"}
ALIASES = {"car","cars","vehicle","vehicles","automobile","automobiles","automotive","supercar","supercars","sedan","coupe","suv","truck","roadster","sportscar"}

def text_fields(item):
    tags=item.get("tags",[])
    categories=item.get("categories",[])
    def names(values):
        if not isinstance(values,list): return ""
        return " ".join(str(v.get("name","") or v.get("slug",""))[:100] if isinstance(v,dict) else str(v)[:100] for v in values[:30])
    primary=" ".join((str(item.get("name",""))[:200],str(item.get("slug",""))[:120],names(tags),names(categories)))
    return primary.replace("_"," "),str(item.get("description",""))[:1200].replace("_"," ")

def rank_asset(item,query,faces,style="realistic"):
    primary,desc=text_fields(item)
    metadata=primary+" "+desc
    words=set(re.findall(r"[a-z0-9]+",query.lower()))-STOP
    tokens=set(re.findall(r"[a-z0-9]+",metadata.lower()))
    vehicle=bool(words & ALIASES)
    if style=="realistic":
        if BAD.search(primary) or BAD.search(desc):
            return None
        # For complex vehicles reject extremely sparse meshes; simple props
        # can legitimately have few faces. Geometry alone never proves realism.
        if vehicle and faces<3500:
            return None
    matched=words & tokens
    if vehicle and tokens & ALIASES:
        matched |= words & ALIASES
    if words and not matched:
        return None
    relevance=30*len(matched)/max(1,len(words))
    realism=min(30,8+8*len(set(m.group(0).lower() for m in GOOD.finditer(metadata))))
    if style=="stylized":
        realism=22 if BAD.search(metadata) else 12
    pbr=item.get("isPBR")
    textured=item.get("isTextured")
    materials=12 if pbr is True or str(pbr).lower() in ("metalness","specular") else 4
    if textured is True: materials+=5
    if re.search(r"\b(?:pbr|textures?|metallic|roughness|normal map)\b",metadata,re.I): materials+=3
    detail=min(10,10*math.log1p(faces)/math.log1p(30000))
    performance=10 if faces<=70000 else 7
    score=round(relevance+realism+min(materials,20)+detail+performance)
    return {"metadata_score":score,"matched_terms":sorted(matched),
            "realism_signals":bool(GOOD.search(metadata)),
            "pbr_hint":bool(pbr is True or str(pbr).lower() in ("metalness","specular")),
            "visual_verified":False}
