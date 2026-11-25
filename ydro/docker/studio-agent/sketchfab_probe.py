"""Local-account diagnostic. No token, signed URL or model archive is exported."""
import io
import json
import os
import re
import zipfile
from urllib.parse import urlsplit
import requests

API = "https://api.sketchfab.com/v3"
MAX_ARCHIVE = 16 * 1024 * 1024
CDN = {"sketchfab-prod-media.s3.amazonaws.com"}
UID = re.compile(r"[0-9a-f]{32}")

def request_bytes(url, *, headers=None, params=None, limit=1024*1024):
    try:
        with requests.get(url, headers=headers, params=params, stream=True,
                          timeout=(8,30), allow_redirects=False) as response:
            status = response.status_code
            if status != 200:
                raise ValueError("HTTP " + str(status))
            data = bytearray()
            for part in response.iter_content(65536):
                if len(data)+len(part)>limit:
                    raise ValueError("response exceeds configured limit")
                data.extend(part)
            return bytes(data)
    except requests.RequestException:
        raise ValueError("network request failed") from None

def api(path, token, params=None):
    try:
        return json.loads(request_bytes(API+path,
            headers={"Authorization":"Token "+token},params=params))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("invalid JSON response") from None

def license_ok(item):
    license = item.get("license")
    if not isinstance(license,dict):
        return False
    return license.get("slug") in ("cc0","by") or license.get("url") in (
        "https://creativecommons.org/publicdomain/zero/1.0/",
        "http://creativecommons.org/publicdomain/zero/1.0/",
        "https://creativecommons.org/licenses/by/4.0/",
        "http://creativecommons.org/licenses/by/4.0/")

def allowed_cdn(url):
    if not isinstance(url,str):
        return False
    try:
        p=urlsplit(url)
        return p.scheme=="https" and p.netloc.lower() in CDN and p.path.startswith("/archives/")
    except ValueError:
        return False

def validate_archive(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist()
            if len(entries)>100 or sum(x.file_size for x in entries)>48*1024*1024:
                raise ValueError("archive exceeds unpacked size limit")
            scenes=[x for x in entries if x.filename.lower().endswith(".gltf")]
            if len(scenes)!=1 or scenes[0].file_size>2*1024*1024:
                raise ValueError("expected one glTF scene")
            scene=json.loads(archive.read(scenes[0]))
            if scene.get("asset",{}).get("version")!="2.0" or not scene.get("meshes"):
                raise ValueError("not a glTF 2.0 mesh")
    except (zipfile.BadZipFile,RuntimeError,UnicodeError,json.JSONDecodeError,AttributeError,NotImplementedError):
        raise ValueError("invalid glTF archive") from None

def probe(token):
    if not token.strip() or any(c.isspace() for c in token):
        raise ValueError("Set SKETCHFAB_API_TOKEN in .env.studio.local")
    try:
        me=api("/me",token)
        if not isinstance(me,dict) or not me.get("uid"):
            raise ValueError("unexpected account response")
    except ValueError as exc:
        raise ValueError("SKETCHFAB_AUTH_FAILED: "+str(exc)) from None
    print("SKETCHFAB_AUTH_OK",flush=True)
    data=api("/search",token,{"type":"models","q":"chair","downloadable":"true","count":24})
    candidates=[]
    for item in data.get("results",[]):
        uid=item.get("uid","")
        if not isinstance(uid,str) or not UID.fullmatch(uid):
            continue
        if item.get("isDownloadable") is False:
            continue
        faces=item.get("faceCount")
        if type(faces) is int and faces>100000:
            continue
        # Search may omit license metadata, so verify on the model detail endpoint.
        candidates.append((faces if type(faces) is int else 100000,uid))
    selected=None
    for _,uid in sorted(candidates)[:8]:
        detail=api("/models/"+uid,token)
        if detail.get("isDownloadable") is True and license_ok(detail):
            selected=uid
            break
    if not selected:
        raise ValueError("SKETCHFAB_SEARCH_OK: no verified CC0/CC BY downloadable candidate; try another search later")
    print("SKETCHFAB_SEARCH_OK: model="+selected,flush=True)
    try:
        result=api("/models/"+selected+"/download",token)
    except ValueError as exc:
        raise ValueError("SKETCHFAB_DOWNLOAD_FAILED: "+str(exc)) from None
    entry=result.get("gltf",{})
    url=entry.get("url")
    if not allowed_cdn(url):
        raise ValueError("SKETCHFAB_LINK_UNSUPPORTED: absent or unapproved CDN address")
    print("SKETCHFAB_DOWNLOAD_LINK_OK",flush=True)
    size=entry.get("size")
    if type(size) is int and size>MAX_ARCHIVE:
        raise ValueError("SKETCHFAB_ARCHIVE_TOO_LARGE: link works, test limit is 16 MiB")
    raw=request_bytes(url,limit=MAX_ARCHIVE)
    validate_archive(raw)
    print("SKETCHFAB_OK: glTF archive downloaded and validated; bytes="+str(len(raw)),flush=True)

if __name__=="__main__":
    try:
        probe(os.environ.get("SKETCHFAB_API_TOKEN","").strip())
    except ValueError as exc:
        print(str(exc),flush=True)
        raise SystemExit(1) from None
